# 电商运营自动化 Agent

这是一个用于学习 Python 后端、商品数据处理、AI 工具调用和自动化工作流的练手项目。

## 当前阶段

- FastAPI 应用骨架
- 中文可视化工作台：`GET /`
- 健康检查：`GET /health`
- 商品利润分析：`POST /products/analyze`
- Excel 批量分析：`POST /products/analyze-excel`
- Excel 结果导出：`POST /products/analyze-excel/export`
- 保存 Excel 分析任务：`POST /tasks/analyze-excel`
- 历史任务列表：`GET /tasks`
- 任务详情：`GET /tasks/{task_id}`
- AI 文案 Prompt 预览：`POST /copywriting/prompt-preview`
- AI 商品文案生成：`POST /copywriting/generate`
- 电商运营 Agent：`POST /agent/analyze`，自动调用利润工具并生成运营策略与执行轨迹
- Agent 历史记录：`GET /agent/runs`、`GET /agent/runs/{run_id}`

网页端的“Agent 分析历史”会自动列出最近 20 次成功运行；点击“查看详情”可回放完整报告并恢复当时的表单输入。失败的模型调用不会写入历史记录。

查看本地 SQLite 数据库概要：

```powershell
python scripts/inspect_database.py
```
- 自动接口文档：`GET /docs`
- 基础自动化测试

## 本地运行

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

业务操作界面：<http://127.0.0.1:8000/>

开发接口文档：<http://127.0.0.1:8000/docs>

中文工作台包含五个可操作板块：

1. 电商运营 Agent：自动调用利润工具，再由大模型生成运营策略、风险提醒和行动计划。
2. AI 商品文案：填写商品卖点、目标用户和平台，调用大模型生成结构化文案。
3. 单品利润测算：计算佣金、总成本、利润和利润率。
4. Excel 批量分析：上传 `.xlsx` 表格，保存任务或下载分析结果。
5. 任务记录管理：查看保存在 SQLite 中的历史分析任务。

AI 文案模块支持兼容 Chat Completions 格式的大模型服务。真实调用前，需要在本机
`.env` 中填写 `AI_API_KEY`、`AI_BASE_URL` 和 `AI_MODEL`。不要把真实 Key 写入
代码、`.env.example` 或提交到 GitHub。

## 测试

```powershell
python -m pytest -q
```
