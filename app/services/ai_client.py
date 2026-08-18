import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.schemas.ai import ModelTokenUsage
from app.schemas.copywriting import GeneratedCopywriting, CopywritingPromptResponse


class ChatPrompt(Protocol):
    """大模型提示词对象需要提供的最小字段集合。"""

    system_prompt: str
    user_prompt: str


StructuredResponse = TypeVar("StructuredResponse", bound=BaseModel)
MILLION_TOKENS = Decimal("1000000")
COST_PRECISION = Decimal("0.00000001")


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
        timeout_seconds: float = 60,
        http_client: httpx.Client | None = None,
        pricing_model: str = "",
        input_price_per_million_tokens: Decimal = Decimal("0"),
        output_price_per_million_tokens: Decimal = Decimal("0"),
    ) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.strip().rstrip("/")
        self.model = model.strip()
        self.timeout_seconds = timeout_seconds
        self._http_client = http_client
        self.pricing_model = pricing_model.strip()
        self.input_price_per_million_tokens = input_price_per_million_tokens
        self.output_price_per_million_tokens = output_price_per_million_tokens
        self.last_usage: ModelTokenUsage | None = None

    def generate(self, prompt: CopywritingPromptResponse) -> GeneratedCopywriting:
        """发送 Prompt，并把大模型响应转换成结构化文案。"""

        return self.generate_structured(prompt, GeneratedCopywriting)

    def generate_structured(
        self,
        prompt: ChatPrompt,
        response_model: type[StructuredResponse],
    ) -> StructuredResponse:
        """发送 Prompt，并把 JSON 响应校验成指定的 Pydantic 模型。"""

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
        self.last_usage = None
        response = self._post(request_body)

        if response.is_error:
            raise AIProviderError(
                f"大模型服务返回错误状态码 {response.status_code}"
            )

        try:
            response_body = response.json()
        except ValueError as exc:
            raise AIResponseError("大模型返回的响应不是 JSON") from exc

        self.last_usage = self._parse_usage(response_body)
        try:
            content = response_body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIResponseError("大模型响应中缺少文案内容") from exc

        if not isinstance(content, str) or not content.strip():
            raise AIResponseError("大模型返回的文案内容为空")

        return self._parse_structured(content, response_model)

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
        except httpx.TimeoutException as exc:
            raise AIProviderError(
                f"大模型请求超过 {self.timeout_seconds:g} 秒，已停止等待"
            ) from exc
        except httpx.RequestError as exc:
            raise AIProviderError("无法连接大模型服务") from exc

    def _parse_usage(self, response_body: object) -> ModelTokenUsage | None:
        if not isinstance(response_body, dict):
            return None
        usage = response_body.get("usage")
        if not isinstance(usage, dict):
            return None

        input_tokens = self._non_negative_int(
            usage.get("prompt_tokens", usage.get("input_tokens", 0))
        )
        output_tokens = self._non_negative_int(
            usage.get("completion_tokens", usage.get("output_tokens", 0))
        )
        total_tokens = self._non_negative_int(usage.get("total_tokens", 0))
        if total_tokens == 0:
            total_tokens = input_tokens + output_tokens

        details = usage.get("prompt_tokens_details")
        cached_input_tokens = 0
        if isinstance(details, dict):
            cached_input_tokens = self._non_negative_int(
                details.get("cached_tokens", 0)
            )

        pricing_matches = bool(self.pricing_model) and self.pricing_model == self.model
        if pricing_matches:
            input_cost = self._estimate_cost(
                input_tokens,
                self.input_price_per_million_tokens,
            )
            output_cost = self._estimate_cost(
                output_tokens,
                self.output_price_per_million_tokens,
            )
            total_cost = (input_cost + output_cost).quantize(
                COST_PRECISION,
                rounding=ROUND_HALF_UP,
            )
            pricing_note = (
                "按本地配置的人民币/百万Token单价估算；未扣除免费额度、"
                "缓存折扣和活动优惠，实际费用以模型供应商账单为准。"
            )
            pricing_model: str | None = self.pricing_model
            input_price: float | None = float(self.input_price_per_million_tokens)
            output_price: float | None = float(self.output_price_per_million_tokens)
            estimated_input_cost: float | None = float(input_cost)
            estimated_output_cost: float | None = float(output_cost)
            estimated_total_cost: float | None = float(total_cost)
        else:
            pricing_note = (
                "已记录Token用量，但当前模型与价格配置不匹配，未估算费用。"
            )
            pricing_model = None
            input_price = None
            output_price = None
            estimated_input_cost = None
            estimated_output_cost = None
            estimated_total_cost = None

        return ModelTokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cached_input_tokens=cached_input_tokens,
            pricing_model=pricing_model,
            input_price_per_million_yuan=input_price,
            output_price_per_million_yuan=output_price,
            estimated_input_cost_yuan=estimated_input_cost,
            estimated_output_cost_yuan=estimated_output_cost,
            estimated_total_cost_yuan=estimated_total_cost,
            pricing_note=pricing_note,
        )

    @staticmethod
    def _non_negative_int(value: object) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return 0
        return max(parsed, 0)

    @staticmethod
    def _estimate_cost(tokens: int, price_per_million: Decimal) -> Decimal:
        return (
            Decimal(tokens) * price_per_million / MILLION_TOKENS
        ).quantize(COST_PRECISION, rounding=ROUND_HALF_UP)

    @staticmethod
    def _parse_structured(
        content: str,
        response_model: type[StructuredResponse],
    ) -> StructuredResponse:
        cleaned_content = content.strip()
        if cleaned_content.startswith("```"):
            lines = cleaned_content.splitlines()
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned_content = "\n".join(lines).strip()

        try:
            data = json.loads(cleaned_content)
            return response_model.model_validate(data)
        except (json.JSONDecodeError, ValidationError, TypeError) as exc:
            raise AIResponseError("大模型返回的内容不是约定的 JSON 格式") from exc
