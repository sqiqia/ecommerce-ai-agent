from fastapi.testclient import TestClient

from app.api.routes.copywriting import get_ai_client
from app.main import app
from app.schemas.agent import GeneratedOperationStrategy
from app.services.ai_client import AIConfigurationError


client = TestClient(app)


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


def test_agent_calls_profit_tool_and_ai_model() -> None:
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

    app.dependency_overrides[get_ai_client] = FakeAIClient
    try:
        response = client.post("/agent/analyze", json=make_request_body())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
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


def test_agent_rejects_invalid_financial_data() -> None:
    body = make_request_body()
    body["sale_price"] = 0

    response = client.post("/agent/analyze", json=body)

    assert response.status_code == 422


def test_agent_reports_missing_ai_configuration() -> None:
    class UnconfiguredAIClient:
        model = ""

        def generate_structured(self, *_):
            raise AIConfigurationError("缺少大模型配置：AI_API_KEY")

    app.dependency_overrides[get_ai_client] = UnconfiguredAIClient
    try:
        response = client.post("/agent/analyze", json=make_request_body())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"] == "缺少大模型配置：AI_API_KEY"
