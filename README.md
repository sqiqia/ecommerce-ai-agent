# 电商运营自动化 Agent

[![Python tests](https://github.com/sqiqia/ecommerce-ai-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/sqiqia/ecommerce-ai-agent/actions/workflows/tests.yml)

这是一个基于 FastAPI、千问大模型和 SQLite 的中文电商运营 AI 应用。项目重点不是证明 AI 文案一定能提高销量，而是展示如何把大模型接入一条有业务规则、结构化输出、数据持久化和自动化测试的应用链路。

> 项目定位：初级 AI 应用开发求职作品集，不是生产级电商 SaaS，也不把固定步骤工作流包装成通用自主智能体。

## 招聘方速览

| 项目维度 | 已完成内容 |
|---|---|
| 核心闭环 | 业务输入 → 利润工具 → 千问 → JSON 校验 → 风险检查 → 历史与反馈 |
| 后端能力 | FastAPI、Pydantic、SQLAlchemy、异常映射和 OpenAPI |
| 数据处理 | 单品利润分析、Excel 逐行校验、批量处理和结果导出 |
| 可验证性 | 47 项 pytest；20 条离线案例；Fake AI Client；GitHub Actions 自动回归 |
| 真实边界 | 本地单用户应用；没有真实转化率数据、登录权限和公网部署 |

简历写法、能力证据和不能夸大的内容见 [项目复盘与简历材料](docs/PROJECT_REVIEW.md)。

## 项目解决什么问题

电商运营人员经常需要重复处理商品利润、营销文案和运营策略。本项目把这些步骤集中到一个中文工作台中：

- 输入售价、成本和佣金后，由确定性工具计算利润，避免让大模型猜数字；
- 将商品资料和利润结果交给千问，生成结构化运营方案；
- 使用 Pydantic 校验模型输出，防止缺少定价、营销、风险或行动计划字段；
- 标记“保证、销量第一、全网最低”等不应直接发布的高风险表述；
- 保存分析记录、执行轨迹和真实用户反馈，支持后续复盘；
- 批量处理 Excel 商品数据，并保存任务或导出结果。

## 系统架构

```mermaid
flowchart LR
    A["中文网页表单"] --> B["FastAPI 接口"]
    B --> C["Pydantic 参数校验"]
    C --> D["利润计算工具"]
    D --> E["Prompt 构建"]
    E --> F["千问大模型"]
    F --> G["结构化结果校验"]
    G --> H["内容风险检查"]
    H --> I["SQLite 历史记录"]
    I --> J["结果回放与用户反馈"]
```

一次 Agent 请求的核心流程：

```text
接收业务目标 → 调用利润工具 → 构建带真实数据的 Prompt → 调用千问
→ 校验 JSON 结构 → 检查风险表述 → 保存执行记录 → 网页展示与反馈
```

## 技术栈

| 分类 | 技术 | 在项目中的用途 |
|---|---|---|
| 后端 | Python、FastAPI | 接口、依赖注入、异常处理、OpenAPI 文档 |
| 数据校验 | Pydantic | 请求参数约束和大模型结构化输出校验 |
| 大模型 | 阿里云百炼千问 | 商品文案和运营策略生成 |
| 数据库 | SQLite、SQLAlchemy | Agent 历史、Excel 任务和用户反馈持久化 |
| 数据处理 | openpyxl | Excel 导入、逐行分析和结果导出 |
| 前端 | HTML、CSS、JavaScript | 无额外前端框架的中文操作界面 |
| 测试 | pytest、FastAPI TestClient | 接口、服务、数据库和启动器自动化测试 |
| 工程化 | Git、GitHub Actions、`.env` | 版本管理、自动测试和密钥隔离 |
| 可选容器配置 | Docker、Compose | 非 root 镜像、健康检查和 SQLite 数据卷；当前未做实机验证 |

## 值得在面试中讲的设计

1. **工具结果优先**：利润由 Python 工具计算，再提供给模型，降低数值幻觉。
2. **结构化输出**：模型必须返回固定 JSON 字段，异常响应会被识别而不是直接展示。
3. **可观察工作流**：网页展示每一步执行者、运行耗时和模型调用次数。
4. **安全边界**：API Key 只保存在被 Git 忽略的 `.env`，接口不会返回密钥。
5. **真实反馈代替虚假评分**：项目删除了缺乏业务依据的自动分数，改为风险提示和用户反馈。
6. **可测试性**：测试使用模拟 AI 客户端和临时 SQLite，不花费模型额度、不污染正式数据。
7. **本地可用性**：一键启动器会实际检测端口，自动避开 Windows 残留端口占用。
8. **持续集成**：GitHub Actions 会在推送和合并请求时自动运行完整测试。

更完整的面试讲解、简历写法和常见追问见 [项目面试指南](docs/INTERVIEW_GUIDE.md)。

## 已实现功能

- FastAPI 应用骨架
- PyCharm 一键启动器：自动避开被占用的本地端口
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
- Agent 内容风险检查：标记绝对化或无法直接核验的表述，提醒人工复核，不增加模型调用
- Agent 运行信息：记录成功工作流的耗时与模型调用次数
- Agent 真实反馈：`POST /agent/runs/{run_id}/feedback`，保存“有帮助/需要改进”和文字意见
- 离线评测：20 条模拟案例、批量模型调用、自动约定检查、报告和人工评分模板

网页端的“Agent 分析历史”会自动列出最近 20 次成功运行；点击“查看详情”可回放完整报告并恢复当时的表单输入。失败的模型调用不会写入历史记录。

查看本地 SQLite 数据库概要：

```powershell
python scripts/inspect_database.py
```
- 自动接口文档：`GET /docs`
- 基础自动化测试

## 本地运行

推荐直接运行启动器，它会从 8000 开始自动寻找空闲端口：

```powershell
python -m pip install -r requirements.txt
python run_server.py
```

终端会打印实际访问地址。例如 8000、8001 被占用时，会自动切换到 8002：

```text
端口 8000 已被占用，已自动切换到 8002。
中文工作台：http://127.0.0.1:8002
健康检查：http://127.0.0.1:8002/health
接口文档：http://127.0.0.1:8002/docs
```

需要指定起始端口时使用：

```powershell
python run_server.py --port 8010
```

## 可选：Docker 配置

仓库保留了 Dockerfile 和 Compose 配置，但作者当前环境没有完成真实镜像构建验证，因此 Docker 不作为简历成果。安装 Docker Desktop 的使用者可以自行验证：

本机安装 Docker Desktop 后，在项目根目录执行：

```powershell
# 首次克隆项目时创建本机配置；已有 .env 不要重复执行这一行
Copy-Item .env.example .env
docker compose up --build
```

默认访问地址：

```text
中文工作台：http://127.0.0.1:8080
健康检查：http://127.0.0.1:8080/health
接口文档：http://127.0.0.1:8080/docs
```

选择 8080 是为了避开本机开发中常见的 8000、8001 端口占用。需要修改宿主机端口时，在 `.env` 中添加：

```text
APP_HOST_PORT=8090
```

Compose 使用具名卷 `ecommerce_data` 保存 SQLite 数据，因此正常重建容器不会删除历史记录。真实 `.env` 只在运行时注入，`.dockerignore` 会阻止它进入镜像。镜像使用 `requirements-prod.txt`，不会安装 pytest 等开发测试工具。

中文工作台包含五个可操作板块：

1. 电商运营 Agent：自动调用利润工具，再由大模型生成运营策略、风险提醒和行动计划。
2. AI 商品文案：填写商品卖点、目标用户和平台，调用大模型生成结构化文案。
3. 单品利润测算：计算佣金、总成本、利润和利润率。
4. Excel 批量分析：上传 `.xlsx` 表格，保存任务或下载分析结果。
5. 任务记录管理：查看保存在 SQLite 中的历史分析任务。

AI 文案模块支持兼容 Chat Completions 格式的大模型服务。真实调用前，需要在本机
`.env` 中填写 `AI_API_KEY`、`AI_BASE_URL` 和 `AI_MODEL`。不要把真实 Key 写入
代码、`.env.example` 或提交到 GitHub。

## 离线评测

不需要真实店铺或上架商品。项目提供 20 条明确标注为模拟数据的商品案例，覆盖四个平台和四种利润状态。默认命令只验证案例，不调用模型：

```powershell
python -m evaluation.run_evaluation
```

真实执行需要同时添加 `--execute --confirm-paid-calls`，避免误触付费调用。详细步骤、输出文件和人工评分方法见 [离线评测使用说明](evaluation/README.md)。

## 测试

```powershell
python -m pytest -q
```

当前完整测试数量：`47`。测试中的模型响应均为本地模拟数据，不会消耗千问额度。

GitHub Actions 会在推送到 `main` 或创建合并请求时执行同一条测试命令。只有工作流实际显示通过，才能把“持续集成”作为已验证能力。

## 当前边界

为了保证项目适合初学者理解和本机演示，当前版本有意保留以下边界：

- Agent 是可解释的固定步骤编排，不是能够无限自主执行的通用智能体；
- 风险检查基于明确词表，只负责提醒人工复核，不等同于完整内容安全系统；
- SQLite 适合单机练习和演示，不适合多实例高并发生产环境；
- 当前没有登录、权限控制、支付和公网部署；
- 失败的模型调用会向用户显示错误，但不会写入成功历史记录。

这些限制是当前阶段的主动取舍，不应在面试中包装成已经完成的生产级能力。
