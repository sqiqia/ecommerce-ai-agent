from app.schemas.agent import AgentAnalyzeResponse, AgentGuardrailResult


RISKY_CLAIMS = ("保证", "绝对", "全网最低", "销量第一", "100%有效")


def inspect_agent_result(result: AgentAnalyzeResponse) -> AgentGuardrailResult:
    """检查不应直接用于对外发布的绝对化承诺，不调用大模型。"""

    full_text = " ".join(
        [
            result.strategy.overall_assessment,
            result.strategy.pricing_suggestion,
            result.strategy.marketing_strategy,
            result.strategy.risk_warning,
            *result.strategy.action_plan,
        ]
    )
    matched_phrases = [phrase for phrase in RISKY_CLAIMS if phrase in full_text]
    if matched_phrases:
        return AgentGuardrailResult(
            status="needs_review",
            matched_phrases=matched_phrases,
            message="检测到绝对化或无法直接核验的表述，请人工修改后再发布。",
        )
    return AgentGuardrailResult(
        status="passed",
        matched_phrases=[],
        message="未发现预设的高风险绝对化表述，发布前仍建议人工复核商品事实。",
    )


def ensure_agent_guardrail(result: AgentAnalyzeResponse) -> AgentGuardrailResult:
    """兼容旧历史记录：没有检查结果时按当前规则即时检查。"""

    if result.guardrail is None:
        result.guardrail = inspect_agent_result(result)
    return result.guardrail
