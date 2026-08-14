import json

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
        prompt_version="1.0",
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
            json={"choices": [{"message": {"content": generated_content}}]},
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = AIChatClient(
            api_key="test-key",
            base_url="https://ai.example.com/v1/",
            model="test-model",
            http_client=http_client,
        )
        result = client.generate(make_prompt())

    assert result.title == "静音双模无线鼠标"
    assert "蓝牙双模" in result.selling_copy
    assert result.call_to_action == "立即体验高效办公。"


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
