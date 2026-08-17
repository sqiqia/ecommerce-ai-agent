from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.agent import AgentAnalyzeRequest, AgentAnalyzeResponse


ProfitBand = Literal["loss", "low", "medium", "healthy"]


class EvaluationCase(BaseModel):
    """一条不依赖真实店铺的模拟业务案例。"""

    case_id: str = Field(pattern=r"^CASE-\d{3}$")
    category: str = Field(min_length=1, max_length=30)
    scenario: str = Field(min_length=1, max_length=200)
    expected_profit_band: ProfitBand
    review_focus: list[str] = Field(min_length=1, max_length=5)
    request: AgentAnalyzeRequest


class AutomaticChecks(BaseModel):
    """无需人工判断、可以重复运行的基础检查。"""

    action_plan_count_valid: bool
    platform_mentioned: bool
    keyword_coverage_rate: float = Field(ge=0, le=1)
    financial_risk_acknowledged: bool
    guardrail_status: Literal["passed", "needs_review"]
    matched_risky_phrases: list[str]
    contract_passed: bool


class HumanReview(BaseModel):
    """人工评价模板；空值表示尚未评价。"""

    relevance: int | None = Field(default=None, ge=1, le=5)
    factual_grounding: int | None = Field(default=None, ge=1, le=5)
    actionability: int | None = Field(default=None, ge=1, le=5)
    platform_fit: int | None = Field(default=None, ge=1, le=5)
    risk_control: int | None = Field(default=None, ge=1, le=5)
    comment: str = Field(default="", max_length=500)


class EvaluationResult(BaseModel):
    """一条成功模型调用对应的完整评测记录。"""

    case: EvaluationCase
    response: AgentAnalyzeResponse
    duration_ms: int = Field(ge=0)
    automatic_checks: AutomaticChecks
    human_review: HumanReview = Field(default_factory=HumanReview)


class FailedEvaluationResult(BaseModel):
    """模型连接或响应解析失败时保留的错误记录。"""

    case: EvaluationCase
    duration_ms: int = Field(ge=0)
    error_type: str
    error_message: str
