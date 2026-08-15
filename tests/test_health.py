from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


client = TestClient(app)


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "电商智营 AI 工作台" in response.text
    assert "电商运营策略 Agent" in response.text
    assert "AI 商品文案生成" in response.text
    assert "单品利润测算" in response.text
    assert "Excel 批量分析" in response.text


def test_api_info_does_not_expose_api_key() -> None:
    response = client.get("/api-info")

    assert response.status_code == 200
    body = response.json()
    assert body["app"] == "电商运营自动化 Agent"
    assert body["version"] == settings.app_version
    assert body["docs"] == "/docs"
    assert "ai_model" in body
    assert "ai_configured" in body
    assert "api_key" not in str(body).lower()


def test_frontend_static_files() -> None:
    css_response = client.get("/static/styles.css")
    js_response = client.get("/static/app.js")

    assert css_response.status_code == 200
    assert "--green" in css_response.text
    assert js_response.status_code == 200
    assert "/copywriting/generate" in js_response.text
    assert "/agent/analyze" in js_response.text


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["message"] == "电商运营自动化 Agent 正常运行"
    assert "time" in body


def test_openapi_and_docs() -> None:
    openapi_response = client.get("/openapi.json")
    docs_response = client.get("/docs")

    assert openapi_response.status_code == 200
    assert openapi_response.json()["info"]["title"] == "电商运营自动化 Agent"
    assert docs_response.status_code == 200
    assert "swagger-ui" in docs_response.text.lower()
