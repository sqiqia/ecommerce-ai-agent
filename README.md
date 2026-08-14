# 电商运营自动化 Agent

这是一个用于学习 Python 后端、商品数据处理、AI 工具调用和自动化工作流的练手项目。

## 当前阶段

- FastAPI 应用骨架
- 首页接口：`GET /`
- 健康检查：`GET /health`
- 商品利润分析：`POST /products/analyze`
- Excel 批量分析：`POST /products/analyze-excel`
- Excel 结果导出：`POST /products/analyze-excel/export`
- 保存 Excel 分析任务：`POST /tasks/analyze-excel`
- 历史任务列表：`GET /tasks`
- 任务详情：`GET /tasks/{task_id}`
- AI 文案 Prompt 预览：`POST /copywriting/prompt-preview`

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

打开：<http://127.0.0.1:8000/docs>

当前 AI 文案模块已经完成 Prompt 构建和预览。真实大模型 API 调用将在下一阶段接入，
因此本阶段无需填写 `AI_API_KEY`。

## 测试

```powershell
python -m pytest -q
```
