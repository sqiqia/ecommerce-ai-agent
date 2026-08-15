from collections.abc import Generator
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.api.routes.copywriting import get_ai_client
from app.database.connection import Base, create_database_engine, get_db
from app.main import app
from app.schemas.agent import GeneratedOperationStrategy
from app.services.ai_client import AIConfigurationError


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    temp_directory = Path("tests/.tmp")
    temp_directory.mkdir(parents=True, exist_ok=True)
    database_path = temp_directory / f"test_agent_{uuid4().hex}.db"
    test_engine = create_database_engine(f"sqlite:///{database_path}")
    testing_session = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )
    Base.metadata.create_all(bind=test_engine)

    def override_get_db() -> Generator[Session, None, None]:
        database = testing_session()
        try:
            yield database
        finally:
            database.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()
        database_path.unlink(missing_ok=True)


def make_request_body() -> dict[str, object]:
    return {
        "product_name": "无线鼠标",
        "selling_points": ["静音按键", "蓝牙双模", "轻巧便携"],
        "target_audience": "经常出差的职场人士",
        "platform": "小红书",
        "tone": "亲切",
        "keywords": ["办公好物", "便携"],
        "sale_price": 79,
        "cost_price": 35,
        "shipping_fee": 8,
        "commission_rate": 0.05,
        "business_goal": "提高商品转化率并保持利润",
    }


class FakeAIClient:
    model = "fake-agent-model"

    def generate_structured(self, prompt, response_model):
        assert response_model is GeneratedOperationStrategy
        assert "单件利润：32.05 元" in prompt.user_prompt
        assert "利润率：40.57%" in prompt.user_prompt
        assert "小红书" in prompt.user_prompt
        return GeneratedOperationStrategy(
            overall_assessment="商品利润健康，适合面向差旅办公人群推广。",
            pricing_suggestion="保持当前价格，优先测试小幅优惠券。",
            marketing_strategy="突出静音、双模和便携三个真实卖点。",
            risk_warning="不要编造续航时间和销量数据。",
            action_plan=["制作场景内容", "测试两版标题", "复盘转化数据"],
        )


def test_agent_calls_tools_and_persists_replayable_history(client: TestClient) -> None:
    app.dependency_overrides[get_ai_client] = FakeAIClient
    try:
        response = client.post("/agent/analyze", json=make_request_body())
    finally:
        app.dependency_overrides.pop(get_ai_client, None)

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == 1
    assert body["agent_version"] == "1.0"
    assert body["model"] == "fake-agent-model"
    assert body["product_analysis"]["profit"] == 32.05
    assert body["product_analysis"]["profit_rate_percent"] == 40.57
    assert body["strategy"]["action_plan"] == [
        "制作场景内容",
        "测试两版标题",
        "复盘转化数据",
    ]
    assert [step["executor"] for step in body["execution_trace"]] == [
        "agent_planner",
        "profit_calculator",
        "fake-agent-model",
        "pydantic_validator",
    ]
    assert all(step["status"] == "completed" for step in body["execution_trace"])

    listing = client.get("/agent/runs")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["product_name"] == "无线鼠标"

    detail = client.get("/agent/runs/1")
    assert detail.status_code == 200
    assert detail.json()["request"] == make_request_body()
    assert detail.json()["result"] == body
    assert "api_key" not in str(detail.json()).lower()


def test_agent_history_returns_latest_run_first(client: TestClient) -> None:
    app.dependency_overrides[get_ai_client] = FakeAIClient
    try:
        first_body = make_request_body()
        second_body = make_request_body()
        second_body["product_name"] = "便携键盘"
        assert client.post("/agent/analyze", json=first_body).status_code == 200
        assert client.post("/agent/analyze", json=second_body).status_code == 200
    finally:
        app.dependency_overrides.pop(get_ai_client, None)

    response = client.get("/agent/runs?offset=0&limit=1")
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["items"][0]["id"] == 2
    assert response.json()["items"][0]["product_name"] == "便携键盘"


def test_agent_history_reports_unknown_run(client: TestClient) -> None:
    response = client.get("/agent/runs/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Agent 运行记录不存在"


def test_agent_rejects_invalid_financial_data(client: TestClient) -> None:
    body = make_request_body()
    body["sale_price"] = 0

    response = client.post("/agent/analyze", json=body)

    assert response.status_code == 422
    assert client.get("/agent/runs").json()["total"] == 0


def test_agent_failure_is_not_saved(client: TestClient) -> None:
    class UnconfiguredAIClient:
        model = ""

        def generate_structured(self, *_):
            raise AIConfigurationError("缺少大模型配置：AI_API_KEY")

    app.dependency_overrides[get_ai_client] = UnconfiguredAIClient
    try:
        response = client.post("/agent/analyze", json=make_request_body())
    finally:
        app.dependency_overrides.pop(get_ai_client, None)

    assert response.status_code == 503
    assert response.json()["detail"] == "缺少大模型配置：AI_API_KEY"
    assert client.get("/agent/runs").json()["total"] == 0
