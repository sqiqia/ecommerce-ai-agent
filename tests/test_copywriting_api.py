from fastapi.testclient import TestClient

from app.api.routes.copywriting import get_ai_client
from app.main import app
from app.schemas.copywriting import GeneratedCopywriting
from app.services.ai_client import AIConfigurationError


client = TestClient(app)


def test_preview_copywriting_prompt() -> None:
    response = client.post(
        "/copywriting/prompt-preview",
        json={
            "product_name": "  无线鼠标  ",
            "selling_points": [" 静音按键 ", "蓝牙双模", "轻巧便携"],
            "target_audience": "经常出差的职场人士",
            "platform": "小红书",
            "tone": "亲切",
            "keywords": ["办公好物", "便携"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["prompt_version"] == "1.2"
    assert "专业的电商文案策划师" in body["system_prompt"]
    assert "商品名称：无线鼠标" in body["user_prompt"]
    assert "1. 静音按键" in body["user_prompt"]
    assert "目标平台：小红书" in body["user_prompt"]
    assert "指定关键词：办公好物、便携" in body["user_prompt"]
    assert '"selling_copy"' in body["user_prompt"]
    assert "事实白名单" in body["user_prompt"]
    assert "卖点只能原样引用" in body["system_prompt"]
    assert "蓝牙双模”不等于“支持多设备切换" in body["system_prompt"]


def test_preview_prompt_rejects_blank_selling_point() -> None:
    response = client.post(
        "/copywriting/prompt-preview",
        json={
            "product_name": "无线鼠标",
            "selling_points": ["静音按键", "   "],
        },
    )

    assert response.status_code == 422

def test_preview_prompt_rejects_more_than_five_selling_points() -> None:
    response = client.post(
        "/copywriting/prompt-preview",
        json={
            "product_name": "无线鼠标",
            "selling_points": ["卖点1", "卖点2", "卖点3", "卖点4", "卖点5", "卖点6"],
        },
    )

    assert response.status_code == 422


def test_generate_copywriting_api() -> None:
    class FakeAIClient:
        model = "fake-model"

        def generate(self, _):
            return GeneratedCopywriting(
                title="静音双模无线鼠标",
                selling_copy="轻巧便携，静音按键搭配蓝牙双模，办公出差都方便。",
                call_to_action="立即体验高效办公。",
            )

    app.dependency_overrides[get_ai_client] = FakeAIClient
    try:
        response = client.post(
            "/copywriting/generate",
            json={
                "product_name": "无线鼠标",
                "selling_points": ["静音按键", "蓝牙双模", "轻巧便携"],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "title": "静音双模无线鼠标",
        "selling_copy": "轻巧便携，静音按键搭配蓝牙双模，办公出差都方便。",
        "call_to_action": "立即体验高效办公。",
        "model": "fake-model",
        "prompt_version": "1.2",
        "token_usage": None,
    }


def test_generate_copywriting_reports_missing_configuration() -> None:
    class UnconfiguredAIClient:
        model = ""

        def generate(self, _):
            raise AIConfigurationError("缺少大模型配置：AI_API_KEY")

    app.dependency_overrides[get_ai_client] = UnconfiguredAIClient
    try:
        response = client.post(
            "/copywriting/generate",
            json={
                "product_name": "无线鼠标",
                "selling_points": ["静音按键"],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"] == "缺少大模型配置：AI_API_KEY"
