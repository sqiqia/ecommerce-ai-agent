import json
from pathlib import Path

from pydantic import ValidationError

from app.schemas.agent import AgentAnalyzeResponse
from app.schemas.product import ProductAnalyzeRequest
from app.services.agent_guardrail_service import ensure_agent_guardrail
from app.services.product_service import analyze_product
from evaluation.models import (
    AutomaticChecks,
    EvaluationCase,
    ProfitBand,
)


FINANCIAL_RISK_TERMS = ("亏损", "利润", "成本", "价格", "售价", "佣金", "调价")


def classify_profit_band(profit: float, profit_rate_percent: float) -> ProfitBand:
    if profit <= 0:
        return "loss"
    if profit_rate_percent < 15:
        return "low"
    if profit_rate_percent < 30:
        return "medium"
    return "healthy"


def analyze_case_finances(case: EvaluationCase):
    request = case.request
    return analyze_product(
        ProductAnalyzeRequest(
            product_name=request.product_name,
            sale_price=request.sale_price,
            cost_price=request.cost_price,
            shipping_fee=request.shipping_fee,
            commission_rate=request.commission_rate,
        )
    )


def load_cases(path: Path) -> list[EvaluationCase]:
    """读取案例并同时验证编号唯一性和利润分档。"""

    try:
        raw_cases = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法读取评测案例：{path}") from exc

    if not isinstance(raw_cases, list):
        raise ValueError("评测案例文件的最外层必须是 JSON 数组")

    try:
        cases = [EvaluationCase.model_validate(item) for item in raw_cases]
    except ValidationError as exc:
        raise ValueError(f"评测案例格式错误：{exc}") from exc

    case_ids = [case.case_id for case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("评测案例编号不能重复")

    for case in cases:
        analysis = analyze_case_finances(case)
        actual_band = classify_profit_band(
            analysis.profit,
            analysis.profit_rate_percent,
        )
        if actual_band != case.expected_profit_band:
            raise ValueError(
                f"{case.case_id} 的预期利润档位是 {case.expected_profit_band}，"
                f"实际计算为 {actual_band}"
            )
    return cases


def combine_strategy_text(response: AgentAnalyzeResponse) -> str:
    strategy = response.strategy
    return " ".join(
        [
            strategy.overall_assessment,
            strategy.pricing_suggestion,
            strategy.marketing_strategy,
            strategy.risk_warning,
            *strategy.action_plan,
        ]
    )


def evaluate_response(
    case: EvaluationCase,
    response: AgentAnalyzeResponse,
) -> AutomaticChecks:
    """检查模型结果是否遵守工作流约定，不冒充业务效果评分。"""

    full_text = combine_strategy_text(response)
    action_plan_count_valid = 2 <= len(response.strategy.action_plan) <= 5
    platform_mentioned = (
        case.request.platform == "通用" or case.request.platform in full_text
    )

    keywords = case.request.keywords
    matched_keyword_count = sum(keyword in full_text for keyword in keywords)
    keyword_coverage_rate = (
        matched_keyword_count / len(keywords) if keywords else 1.0
    )

    financial_risk_acknowledged = True
    if case.expected_profit_band in {"loss", "low"}:
        financial_risk_acknowledged = any(
            term in full_text for term in FINANCIAL_RISK_TERMS
        )

    guardrail = ensure_agent_guardrail(response)
    contract_passed = all(
        [
            action_plan_count_valid,
            platform_mentioned,
            keyword_coverage_rate == 1.0,
            financial_risk_acknowledged,
        ]
    )
    return AutomaticChecks(
        action_plan_count_valid=action_plan_count_valid,
        platform_mentioned=platform_mentioned,
        keyword_coverage_rate=round(keyword_coverage_rate, 4),
        financial_risk_acknowledged=financial_risk_acknowledged,
        guardrail_status=guardrail.status,
        matched_risky_phrases=guardrail.matched_phrases,
        contract_passed=contract_passed,
    )
