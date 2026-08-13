from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["app"] == "电商运营自动化 Agent"
    assert body["version"] == "0.1.0"
    assert body["docs"] == "/docs"


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
