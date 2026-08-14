import json

import httpx
from pydantic import ValidationError

from app.schemas.copywriting import GeneratedCopywriting, CopywritingPromptResponse


class AIClientError(Exception):
    """大模型客户端错误的基类。"""


class AIConfigurationError(AIClientError):
    """大模型配置不完整。"""


class AIProviderError(AIClientError):
    """无法连接大模型服务，或服务返回错误状态。"""


class AIResponseError(AIClientError):
    """大模型返回的数据无法解析或不符合约定格式。"""


class AIChatClient:
    """调用兼容 Chat Completions 格式的大模型服务。"""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float = 30,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.strip().rstrip("/")
        self.model = model.strip()
        self.timeout_seconds = timeout_seconds
        self._http_client = http_client

    def generate(self, prompt: CopywritingPromptResponse) -> GeneratedCopywriting:
        """发送 Prompt，并把大模型响应转换成结构化文案。"""

        self._validate_configuration()
        request_body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
            "temperature": 0.7,
            "response_format": {"type": "json_object"},
        }
        response = self._post(request_body)

        if response.is_error:
            raise AIProviderError(
                f"大模型服务返回错误状态码 {response.status_code}"
            )

        try:
            content = response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AIResponseError("大模型响应中缺少文案内容") from exc

        if not isinstance(content, str) or not content.strip():
            raise AIResponseError("大模型返回的文案内容为空")

        return self._parse_copywriting(content)

    def _validate_configuration(self) -> None:
        missing_fields = [
            name
            for name, value in (
                ("AI_API_KEY", self.api_key),
                ("AI_BASE_URL", self.base_url),
                ("AI_MODEL", self.model),
            )
            if not value
        ]
        if missing_fields:
            raise AIConfigurationError(
                f"缺少大模型配置：{'、'.join(missing_fields)}"
            )

    def _post(self, request_body: dict[str, object]) -> httpx.Response:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            if self._http_client is not None:
                return self._http_client.post(url, headers=headers, json=request_body)

            with httpx.Client(timeout=self.timeout_seconds) as client:
                return client.post(url, headers=headers, json=request_body)
        except httpx.RequestError as exc:
            raise AIProviderError("无法连接大模型服务") from exc

    @staticmethod
    def _parse_copywriting(content: str) -> GeneratedCopywriting:
        cleaned_content = content.strip()
        if cleaned_content.startswith("```"):
            lines = cleaned_content.splitlines()
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned_content = "\n".join(lines).strip()

        try:
            data = json.loads(cleaned_content)
            return GeneratedCopywriting.model_validate(data)
        except (json.JSONDecodeError, ValidationError, TypeError) as exc:
            raise AIResponseError("大模型返回的文案不是约定的 JSON 格式") from exc
