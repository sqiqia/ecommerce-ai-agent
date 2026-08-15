const byId = (id) => document.getElementById(id);

const state = {
    selectedFile: null,
    toastTimer: null,
};

function showToast(message, type = "success") {
    const toast = byId("toast");
    toast.textContent = message;
    toast.className = `toast show${type === "error" ? " error" : ""}`;
    clearTimeout(state.toastTimer);
    state.toastTimer = setTimeout(() => {
        toast.className = "toast";
    }, 3600);
}

function setButtonLoading(button, loading, loadingText) {
    if (!button.dataset.defaultText) {
        button.dataset.defaultText = button.textContent.trim();
    }
    button.disabled = loading;
    button.textContent = loading ? loadingText : button.dataset.defaultText;
}

function parseList(value, maxItems = 5) {
    return value
        .split(/[\n,，、]+/)
        .map((item) => item.trim())
        .filter(Boolean)
        .slice(0, maxItems);
}

function normalizeErrorDetail(detail) {
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
        return detail.map((item) => item.msg || "输入内容不符合要求").join("；");
    }
    return "请求没有成功，请检查输入内容后重试。";
}

async function requestJson(url, options = {}) {
    let response;
    try {
        response = await fetch(url, options);
    } catch (error) {
        throw new Error("无法连接后端服务，请确认 PyCharm 中的程序仍在运行。");
    }

    let data = null;
    try {
        data = await response.json();
    } catch (error) {
        if (!response.ok) throw new Error(`请求失败（状态码 ${response.status}）`);
    }

    if (!response.ok) {
        throw new Error(normalizeErrorDetail(data?.detail));
    }
    return data;
}

function formatMoney(value) {
    return `¥ ${Number(value).toFixed(2)}`;
}

function formatDate(value) {
    if (!value) return "—";
    return new Intl.DateTimeFormat("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    }).format(new Date(value));
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

async function loadSystemInfo() {
    const statusDots = document.querySelectorAll(".status-dot");
    try {
        const [health, info] = await Promise.all([
            requestJson("/health"),
            requestJson("/api-info"),
        ]);
        byId("hero-status").textContent = health.status === "ok" ? "服务运行正常" : "服务状态异常";
        byId("footer-status").textContent = health.status === "ok" ? "运行正常" : "状态异常";
        byId("hero-model").textContent = info.ai_model;
        byId("footer-model").textContent = info.ai_configured ? info.ai_model : "尚未配置";
        byId("hero-version").textContent = info.version;
        statusDots.forEach((dot) => dot.classList.remove("offline"));
    } catch (error) {
        byId("hero-status").textContent = "服务连接失败";
        byId("footer-status").textContent = "连接失败";
        byId("hero-model").textContent = "无法读取";
        byId("footer-model").textContent = "无法读取";
        statusDots.forEach((dot) => dot.classList.add("offline"));
    }
}

function renderAgentResult(result) {
    const analysis = result.product_analysis;
    const strategy = result.strategy;
    byId("agent-profit").textContent = formatMoney(analysis.profit);
    byId("agent-profit-rate").textContent = `${Number(analysis.profit_rate_percent).toFixed(2)}%`;
    byId("agent-tool-advice").textContent = analysis.advice;
    byId("agent-assessment").textContent = strategy.overall_assessment;
    byId("agent-pricing").textContent = strategy.pricing_suggestion;
    byId("agent-marketing").textContent = strategy.marketing_strategy;
    byId("agent-risk").textContent = strategy.risk_warning;
    const runLabel = result.run_id ? ` · 记录 #${result.run_id}` : "";
    byId("agent-meta").textContent = `Agent ${result.agent_version} · ${result.model}${runLabel}`;

    const actionList = byId("agent-action-list");
    actionList.replaceChildren(...strategy.action_plan.map((action) => {
        const item = document.createElement("li");
        item.textContent = action;
        return item;
    }));

    byId("agent-trace-list").innerHTML = result.execution_trace.map((step) => `
        <div class="agent-trace-step">
            <span class="agent-trace-number">${escapeHtml(step.sequence)}</span>
            <div class="agent-trace-detail">
                <b>${escapeHtml(step.name)}</b>
                <small>执行者：${escapeHtml(step.executor)} · 已完成</small>
                <p>${escapeHtml(step.summary)}</p>
            </div>
        </div>
    `).join("");

    byId("agent-empty").classList.add("hidden");
    byId("agent-content").classList.remove("hidden");
}

byId("agent-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = byId("agent-submit");
    const sellingPoints = parseList(byId("agent-selling-points").value);
    if (!sellingPoints.length) {
        showToast("请至少填写一个商品卖点。", "error");
        return;
    }

    const payload = {
        product_name: byId("agent-product-name").value.trim(),
        selling_points: sellingPoints,
        target_audience: byId("agent-audience").value.trim(),
        platform: byId("agent-platform").value,
        tone: byId("agent-tone").value,
        keywords: parseList(byId("agent-keywords").value),
        sale_price: Number(byId("agent-sale-price").value),
        cost_price: Number(byId("agent-cost-price").value),
        shipping_fee: Number(byId("agent-shipping-fee").value || 0),
        commission_rate: Number(byId("agent-commission-rate").value || 0) / 100,
        business_goal: byId("agent-business-goal").value.trim(),
    };

    setButtonLoading(button, true, "Agent 正在调用工具和千问…");
    byId("agent-state").textContent = "正在执行";
    try {
        const result = await requestJson("/agent/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        renderAgentResult(result);
        byId("agent-state").textContent = "执行完成";
        await loadAgentHistory();
        showToast("运营 Agent 已完成分析。", "success");
    } catch (error) {
        byId("agent-state").textContent = "执行失败";
        showToast(error.message, "error");
    } finally {
        setButtonLoading(button, false, "");
    }
});

function renderAgentHistory(items) {
    const historyList = byId("agent-history-list");
    if (!items.length) {
        historyList.innerHTML = `
            <div class="agent-history-empty">
                还没有成功记录。完成一次 Agent 分析后，结果会自动出现在这里。
            </div>
        `;
        return;
    }

    historyList.innerHTML = items.map((item) => `
        <article class="agent-history-card">
            <div class="agent-history-number">#${escapeHtml(item.id)}</div>
            <div class="agent-history-main">
                <span>${escapeHtml(formatDate(item.created_at))} · ${escapeHtml(item.model)}</span>
                <h4>${escapeHtml(item.product_name)}</h4>
                <p>${escapeHtml(item.business_goal)}</p>
            </div>
            <div class="agent-history-metric">
                <span>单件利润</span>
                <b>${escapeHtml(formatMoney(item.profit))}</b>
            </div>
            <div class="agent-history-metric">
                <span>利润率</span>
                <b>${escapeHtml(Number(item.profit_rate_percent).toFixed(2))}%</b>
            </div>
            <button class="agent-history-view" type="button" data-agent-run-id="${escapeHtml(item.id)}">
                查看详情
            </button>
        </article>
    `).join("");

    historyList.querySelectorAll("[data-agent-run-id]").forEach((button) => {
        button.addEventListener("click", () => loadAgentRunDetail(button.dataset.agentRunId));
    });
}

async function loadAgentHistory() {
    const refreshButton = byId("refresh-agent-history");
    setButtonLoading(refreshButton, true, "正在刷新…");
    try {
        const result = await requestJson("/agent/runs?offset=0&limit=20");
        byId("agent-history-total").textContent = result.total;
        renderAgentHistory(result.items);
    } catch (error) {
        byId("agent-history-list").innerHTML = `
            <div class="agent-history-empty">${escapeHtml(error.message)}</div>
        `;
    } finally {
        setButtonLoading(refreshButton, false, "");
    }
}

function restoreAgentForm(request) {
    byId("agent-product-name").value = request.product_name;
    byId("agent-selling-points").value = request.selling_points.join("\n");
    byId("agent-audience").value = request.target_audience;
    byId("agent-sale-price").value = request.sale_price;
    byId("agent-cost-price").value = request.cost_price;
    byId("agent-shipping-fee").value = request.shipping_fee;
    byId("agent-commission-rate").value = Number(request.commission_rate) * 100;
    byId("agent-platform").value = request.platform;
    byId("agent-tone").value = request.tone;
    byId("agent-keywords").value = request.keywords.join("，");
    byId("agent-business-goal").value = request.business_goal;
}

async function loadAgentRunDetail(runId) {
    try {
        const detail = await requestJson(`/agent/runs/${runId}`);
        restoreAgentForm(detail.request);
        renderAgentResult(detail.result);
        byId("agent-state").textContent = `正在回放记录 #${runId}`;
        byId("agent").scrollIntoView({ behavior: "smooth", block: "start" });
        showToast(`已加载 Agent 记录 #${runId}。`, "success");
    } catch (error) {
        showToast(error.message, "error");
    }
}

byId("refresh-agent-history").addEventListener("click", loadAgentHistory);

byId("copywriting-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = byId("copy-submit");
    const sellingPoints = parseList(byId("copy-selling-points").value);
    if (!sellingPoints.length) {
        showToast("请至少填写一个商品卖点。", "error");
        return;
    }

    const payload = {
        product_name: byId("copy-product-name").value.trim(),
        selling_points: sellingPoints,
        target_audience: byId("copy-audience").value.trim(),
        platform: byId("copy-platform").value,
        tone: byId("copy-tone").value,
        keywords: parseList(byId("copy-keywords").value),
    };

    setButtonLoading(button, true, "千问正在生成，请稍候…");
    byId("copy-state").textContent = "正在生成";
    try {
        const result = await requestJson("/copywriting/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        byId("copy-title").textContent = result.title;
        byId("copy-body").textContent = result.selling_copy;
        byId("copy-cta").textContent = result.call_to_action;
        byId("copy-model").textContent = result.model;
        byId("copy-version").textContent = result.prompt_version;
        byId("copy-empty").classList.add("hidden");
        byId("copy-result").classList.remove("hidden");
        byId("copy-state").textContent = "生成成功";
        showToast("AI 文案已经生成。", "success");
    } catch (error) {
        byId("copy-state").textContent = "生成失败";
        showToast(error.message, "error");
    } finally {
        setButtonLoading(button, false, "");
    }
});

byId("copy-content-button").addEventListener("click", async () => {
    const content = `${byId("copy-title").textContent}\n\n${byId("copy-body").textContent}\n\n${byId("copy-cta").textContent}`;
    try {
        await navigator.clipboard.writeText(content);
        showToast("文案已复制到剪贴板。", "success");
    } catch (error) {
        showToast("浏览器未允许复制，请手动选择文案。", "error");
    }
});

byId("profit-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = byId("profit-submit");
    const payload = {
        product_name: byId("profit-product-name").value.trim(),
        sale_price: Number(byId("sale-price").value),
        cost_price: Number(byId("cost-price").value),
        shipping_fee: Number(byId("shipping-fee").value || 0),
        commission_rate: Number(byId("commission-rate").value || 0) / 100,
    };

    setButtonLoading(button, true, "正在计算…");
    try {
        const result = await requestJson("/products/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        byId("profit-result-name").textContent = result.product_name;
        byId("metric-commission").textContent = formatMoney(result.commission);
        byId("metric-total-cost").textContent = formatMoney(result.total_cost);
        byId("metric-profit").textContent = formatMoney(result.profit);
        byId("metric-profit-rate").textContent = `${Number(result.profit_rate_percent).toFixed(2)}%`;
        byId("profit-advice").textContent = result.advice;
        const flag = byId("profit-flag");
        flag.textContent = result.profitable ? "可以盈利" : "当前亏损";
        flag.classList.toggle("loss", !result.profitable);
        byId("profit-placeholder").classList.add("hidden");
        byId("profit-content").classList.remove("hidden");
        showToast("利润测算完成。", "success");
    } catch (error) {
        showToast(error.message, "error");
    } finally {
        setButtonLoading(button, false, "");
    }
});

byId("excel-file").addEventListener("change", (event) => {
    const file = event.target.files?.[0] || null;
    state.selectedFile = file;
    if (!file) {
        byId("file-name").textContent = "点击选择 Excel 文件";
        byId("file-description").textContent = "仅支持 .xlsx 格式，文件不能超过 5MB";
        return;
    }
    byId("file-name").textContent = file.name;
    byId("file-description").textContent = `文件大小：${(file.size / 1024).toFixed(1)} KB，点击可重新选择`;
});

function requireExcelFile() {
    if (!state.selectedFile) {
        showToast("请先选择一个 .xlsx 文件。", "error");
        return false;
    }
    if (!state.selectedFile.name.toLowerCase().endsWith(".xlsx")) {
        showToast("文件格式不正确，只支持 .xlsx。", "error");
        return false;
    }
    return true;
}

function renderBatchResult(task) {
    byId("batch-filename").textContent = task.filename;
    byId("batch-task-id").textContent = task.id ? `任务 #${task.id}` : "即时分析";
    byId("batch-total").textContent = task.total_rows;
    byId("batch-success").textContent = task.success_count;
    byId("batch-error").textContent = task.error_count;

    const rows = task.results || [];
    byId("batch-table-body").innerHTML = rows.slice(0, 8).map((row) => {
        const success = row.status === "success";
        const profit = row.profit ?? row.analysis?.profit;
        const advice = row.advice ?? row.analysis?.advice ?? row.error_reason ?? "—";
        return `<tr>
            <td>${escapeHtml(row.source_row)}</td>
            <td>${escapeHtml(row.product_name || "—")}</td>
            <td><span class="table-status${success ? "" : " error"}">${success ? "成功" : "失败"}</span></td>
            <td>${profit === null || profit === undefined ? "—" : escapeHtml(formatMoney(profit))}</td>
            <td title="${escapeHtml(advice)}">${escapeHtml(advice)}</td>
        </tr>`;
    }).join("");

    byId("batch-empty").classList.add("hidden");
    byId("batch-content").classList.remove("hidden");
}

byId("save-task-button").addEventListener("click", async () => {
    if (!requireExcelFile()) return;
    const button = byId("save-task-button");
    const formData = new FormData();
    formData.append("file", state.selectedFile);
    setButtonLoading(button, true, "正在分析并保存…");
    try {
        const result = await requestJson("/tasks/analyze-excel", {
            method: "POST",
            body: formData,
        });
        renderBatchResult(result);
        await loadTasks();
        showToast(`任务 #${result.id} 已保存。`, "success");
    } catch (error) {
        showToast(error.message, "error");
    } finally {
        setButtonLoading(button, false, "");
    }
});

byId("export-button").addEventListener("click", async () => {
    if (!requireExcelFile()) return;
    const button = byId("export-button");
    const formData = new FormData();
    formData.append("file", state.selectedFile);
    setButtonLoading(button, true, "正在生成文件…");
    try {
        const response = await fetch("/products/analyze-excel/export", {
            method: "POST",
            body: formData,
        });
        if (!response.ok) {
            let detail = "导出失败，请检查表格格式。";
            try {
                const data = await response.json();
                detail = normalizeErrorDetail(data.detail);
            } catch (error) {
                // 保留通用中文错误说明。
            }
            throw new Error(detail);
        }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = "商品利润分析结果.xlsx";
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(url);
        showToast("分析结果已开始下载。", "success");
    } catch (error) {
        showToast(error.message, "error");
    } finally {
        setButtonLoading(button, false, "");
    }
});

function renderTaskList(tasks) {
    const list = byId("task-list");
    if (!tasks.length) {
        list.innerHTML = '<div class="task-empty">目前还没有任务。前往“Excel 批量分析”上传一份表格即可创建。</div>';
        return;
    }
    list.innerHTML = tasks.map((task) => `<article class="task-card">
        <div class="task-number">#${escapeHtml(task.id)}</div>
        <div><span>文件名称</span><b title="${escapeHtml(task.filename)}">${escapeHtml(task.filename)}</b></div>
        <div><span>总行数</span><b>${escapeHtml(task.total_rows)}</b></div>
        <div class="task-success"><span>成功</span><b>${escapeHtml(task.success_count)}</b></div>
        <div class="task-errors"><span>失败</span><b>${escapeHtml(task.error_count)}</b></div>
        <div class="task-time"><span>创建时间</span><b>${escapeHtml(formatDate(task.created_at))}</b></div>
        <button class="task-view-button" type="button" data-task-id="${escapeHtml(task.id)}">查看详情</button>
    </article>`).join("");

    list.querySelectorAll("[data-task-id]").forEach((button) => {
        button.addEventListener("click", () => loadTaskDetail(button.dataset.taskId));
    });
}

async function loadTasks() {
    const refreshButton = byId("refresh-tasks");
    setButtonLoading(refreshButton, true, "正在刷新…");
    try {
        const result = await requestJson("/tasks?offset=0&limit=20");
        byId("task-total").textContent = result.total;
        renderTaskList(result.items);
    } catch (error) {
        byId("task-list").innerHTML = `<div class="task-empty">${escapeHtml(error.message)}</div>`;
    } finally {
        setButtonLoading(refreshButton, false, "");
    }
}

async function loadTaskDetail(taskId) {
    try {
        const result = await requestJson(`/tasks/${taskId}`);
        renderBatchResult(result);
        byId("batch").scrollIntoView({ behavior: "smooth", block: "start" });
        showToast(`已加载任务 #${taskId} 的详细结果。`, "success");
    } catch (error) {
        showToast(error.message, "error");
    }
}

byId("refresh-tasks").addEventListener("click", loadTasks);

loadSystemInfo();
loadAgentHistory();
loadTasks();
