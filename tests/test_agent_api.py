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
from app.schemas.ai import ModelTokenUsage
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
    last_usage = ModelTokenUsage(
        input_tokens=800,
        output_tokens=200,
        total_tokens=1000,
        pricing_model="fake-agent-model",
        input_price_per_million_yuan=0.2,
        output_price_per_million_yuan=0.8,
        estimated_input_cost_yuan=0.00016,
        estimated_output_cost_yuan=0.00016,
        estimated_total_cost_yuan=0.00032,
        pricing_note="测试预估费用",
    )

    def generate_structured(self, prompt, response_model):
        assert response_model is GeneratedOperationStrategy
        assert "单件利润：32.05 元" in prompt.user_prompt
        assert "利润率：40.57%" in prompt.user_prompt
        assert "小红书" in prompt.user_prompt
        assert prompt.prompt_version == "1.1"
        assert "不得擅自添加预算、赠品、试用人数" in prompt.user_prompt
        assert "只有用户本次明确提供" in prompt.system_prompt
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
    assert body["guardrail"]["status"] == "passed"
    assert body["guardrail"]["matched_phrases"] == []
    assert body["runtime_metrics"]["duration_ms"] >= 0
    assert body["runtime_metrics"]["model_call_count"] == 1
    assert body["token_usage"]["total_tokens"] == 1000
    assert body["token_usage"]["estimated_total_cost_yuan"] == 0.00032

    listing = client.get("/agent/runs")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["product_name"] == "无线鼠标"
    assert listing.json()["items"][0]["guardrail_status"] == "passed"
    assert listing.json()["items"][0]["model_call_count"] == 1
    assert listing.json()["items"][0]["token_usage"]["input_tokens"] == 800
    assert listing.json()["items"][0]["feedback"] is None

    detail = client.get("/agent/runs/1")
    assert detail.status_code == 200
    assert detail.json()["request"] == make_request_body()
    assert detail.json()["result"] == body
    assert "api_key" not in str(detail.json()).lower()

    feedback = client.post(
        "/agent/runs/1/feedback",
        json={"rating": "useful", "comment": "利润和行动建议都很清楚"},
    )
    assert feedback.status_code == 200
    assert feedback.json()["rating"] == "useful"
    assert feedback.json()["comment"] == "利润和行动建议都很清楚"
    assert client.get("/agent/runs").json()["items"][0]["feedback"]["rating"] == "useful"
    assert client.get("/agent/runs/1").json()["feedback"]["comment"] == "利润和行动建议都很清楚"


def test_agent_guardrail_flags_risky_claims(client: TestClient) -> None:
    class RiskyAIClient:
        model = "fake-agent-model"

        def generate_structured(self, *_):
            return GeneratedOperationStrategy(
                overall_assessment="商品保证成为销量第一。",
                pricing_suggestion="保持当前价格并测试优惠券。",
                marketing_strategy="突出静音、双模和便携卖点。",
                risk_warning="发布前仍然需要核对全部商品参数。",
                action_plan=["制作场景内容", "测试两版标题", "复盘转化数据"],
            )

    app.dependency_overrides[get_ai_client] = RiskyAIClient
    try:
        response = client.post("/agent/analyze", json=make_request_body())
    finally:
        app.dependency_overrides.pop(get_ai_client, None)

    assert response.status_code == 200
    guardrail = response.json()["guardrail"]
    assert guardrail["status"] == "needs_review"
    assert guardrail["matched_phrases"] == ["保证", "销量第一"]
    assert "人工修改" in guardrail["message"]


def test_agent_guardrail_ignores_warning_language(client: TestClient) -> None:
    class WarningOnlyAIClient:
        model = "fake-agent-model"

        def generate_structured(self, *_):
            return GeneratedOperationStrategy(
                overall_assessment="输入存在绝对化表述，需要核验。",
                pricing_suggestion="当前价格可作为测试基准。",
                marketing_strategy="禁止使用全网最低等无法核验的宣传。",
                risk_warning="不要宣称销量第一，也不得保证效果。",
                action_plan=["核对商品资料", "删除风险用语"],
            )

    app.dependency_overrides[get_ai_client] = WarningOnlyAIClient
    try:
        response = client.post("/agent/analyze", json=make_request_body())
    finally:
        app.dependency_overrides.pop(get_ai_client, None)

    assert response.status_code == 200
    guardrail = response.json()["guardrail"]
    assert guardrail["status"] == "passed"
    assert guardrail["matched_phrases"] == []


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
    feedback_response = client.post(
        "/agent/runs/999/feedback",
        json={"rating": "useful", "comment": ""},
    )
    assert feedback_response.status_code == 404


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
