import re

from app.schemas.agent import AgentAnalyzeResponse, AgentGuardrailResult


RISKY_CLAIMS = ("保证", "绝对", "全网最低", "销量第一", "100%有效")
CAUTION_PREFIXES = (
    "不要",
    "不得",
    "不能",
    "禁止",
    "避免",
    "拒绝",
    "删除",
    "去除",
    "慎用",
    "不应",
    "不可",
    "停止",
    "请勿",
)
CAUTION_SUFFIXES = (
    "属于风险",
    "存在风险",
    "需要复核",
    "需复核",
    "人工复核",
    "风险表述",
    "风险用语",
    "不可使用",
    "不应使用",
)


def _is_cautionary_context(text: str, start: int, end: int, phrase: str) -> bool:
    """识别“禁止使用某词”等提醒语境，避免把风险提示本身判成违规。"""

    prefix = text[max(0, start - 40):start]
    sentence_prefix = re.split(r"[，。；！？]", prefix)[-1]
    suffix = text[end:end + 24].strip(" ，。；：、‘’\"（）()")
    if any(marker in sentence_prefix for marker in CAUTION_PREFIXES):
        return True
    if any(suffix.startswith(marker) for marker in CAUTION_SUFFIXES):
        return True
    if re.match(r"^(属于|是|为)?(需要|需|应)?(人工)?(复核|核验)", suffix):
        return True
    if phrase == "绝对" and suffix.startswith(("化表述", "化用语", "化承诺")):
        return True
    return False


def find_actionable_risky_claims(text: str) -> list[str]:
    """只返回作为营销承诺出现的风险词，忽略否定、禁止和复核语境。"""

    matched: list[str] = []
    for phrase in RISKY_CLAIMS:
        occurrences = re.finditer(re.escape(phrase), text)
        if any(
            not _is_cautionary_context(text, match.start(), match.end(), phrase)
            for match in occurrences
        ):
            matched.append(phrase)
    return matched


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
    matched_phrases = find_actionable_risky_claims(full_text)
    if matched_phrases:
        return AgentGuardrailResult(
            status="needs_review",
            matched_phrases=matched_phrases,
            message="检测到非提醒语境中的绝对化或无法直接核验表述，请人工修改后再发布。",
        )
    return AgentGuardrailResult(
        status="passed",
        matched_phrases=[],
        message="未发现预设的高风险绝对化表述，发布前仍建议人工复核商品事实。",
    )


def ensure_agent_guardrail(result: AgentAnalyzeResponse) -> AgentGuardrailResult:
    """历史回放使用当前规则重算，修复旧版本已保存的误报。"""

    result.guardrail = inspect_agent_result(result)
    return result.guardrail
