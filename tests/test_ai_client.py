import json
from decimal import Decimal

import httpx
import pytest

from app.schemas.copywriting import CopywritingPromptResponse
from app.services.ai_client import (
    AIChatClient,
    AIConfigurationError,
    AIProviderError,
    AIResponseError,
)


def make_prompt() -> CopywritingPromptResponse:
    return CopywritingPromptResponse(
        prompt_version="1.1",
        system_prompt="你是一名电商文案策划师。",
        user_prompt="请为无线鼠标生成文案。",
    )


def test_ai_client_generates_structured_copywriting() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        assert request.url == "https://ai.example.com/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert body["model"] == "test-model"
        assert body["messages"][0]["role"] == "system"
        assert body["messages"][1]["role"] == "user"
        assert body["response_format"] == {"type": "json_object"}

        generated_content = json.dumps(
            {
                "title": "静音双模无线鼠标",
                "selling_copy": "轻巧便携，静音按键搭配蓝牙双模，办公出差都方便。",
                "call_to_action": "立即体验高效办公。",
            },
            ensure_ascii=False,
        )
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": generated_content}}],
                "usage": {
                    "prompt_tokens": 500,
                    "completion_tokens": 125,
                    "total_tokens": 625,
                    "prompt_tokens_details": {"cached_tokens": 100},
                },
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = AIChatClient(
            api_key="test-key",
            base_url="https://ai.example.com/v1/",
            model="test-model",
            http_client=http_client,
            pricing_model="test-model",
            input_price_per_million_tokens=Decimal("0.2"),
            output_price_per_million_tokens=Decimal("0.8"),
        )
        result = client.generate(make_prompt())

    assert result.title == "静音双模无线鼠标"
    assert "蓝牙双模" in result.selling_copy
    assert result.call_to_action == "立即体验高效办公。"
    assert client.last_usage is not None
    assert client.last_usage.input_tokens == 500
    assert client.last_usage.output_tokens == 125
    assert client.last_usage.total_tokens == 625
    assert client.last_usage.cached_input_tokens == 100
    assert client.last_usage.estimated_input_cost_yuan == 0.0001
    assert client.last_usage.estimated_output_cost_yuan == 0.0001
    assert client.last_usage.estimated_total_cost_yuan == 0.0002


def test_ai_client_does_not_apply_price_to_a_different_model() -> None:
    content = json.dumps(
        {"title": "标题", "selling_copy": "正文", "call_to_action": "行动"},
        ensure_ascii=False,
    )
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": content}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            },
        )
    )
    with httpx.Client(transport=transport) as http_client:
        client = AIChatClient(
            api_key="test-key",
            base_url="https://ai.example.com/v1",
            model="actual-model",
            http_client=http_client,
            pricing_model="another-model",
            input_price_per_million_tokens=Decimal("9"),
            output_price_per_million_tokens=Decimal("9"),
        )
        client.generate(make_prompt())

    assert client.last_usage is not None
    assert client.last_usage.total_tokens == 15
    assert client.last_usage.estimated_total_cost_yuan is None
    assert "不匹配" in client.last_usage.pricing_note


def test_ai_client_rejects_missing_configuration() -> None:
    client = AIChatClient(api_key="", base_url="", model="")

    with pytest.raises(AIConfigurationError) as error:
        client.generate(make_prompt())

    message = str(error.value)
    assert "AI_API_KEY" in message
    assert "AI_BASE_URL" in message
    assert "AI_MODEL" in message


def test_ai_client_handles_provider_error() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(429, json={"error": "rate limit"})
    )
    with httpx.Client(transport=transport) as http_client:
        client = AIChatClient(
            api_key="test-key",
            base_url="https://ai.example.com/v1",
            model="test-model",
            http_client=http_client,
        )
        with pytest.raises(AIProviderError, match="429"):
            client.generate(make_prompt())


def test_ai_client_reports_timeout_separately() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = AIChatClient(
            api_key="test-key",
            base_url="https://ai.example.com/v1",
            model="test-model",
            timeout_seconds=60,
            http_client=http_client,
        )
        with pytest.raises(AIProviderError, match="超过 60 秒"):
            client.generate(make_prompt())


def test_ai_client_rejects_invalid_json_content() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            json={"choices": [{"message": {"content": "这不是 JSON"}}]},
        )
    )
    with httpx.Client(transport=transport) as http_client:
        client = AIChatClient(
            api_key="test-key",
            base_url="https://ai.example.com/v1",
            model="test-model",
            http_client=http_client,
        )
        with pytest.raises(AIResponseError, match="JSON"):
            client.generate(make_prompt())
