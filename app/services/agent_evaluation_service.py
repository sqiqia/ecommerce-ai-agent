from app.schemas.agent import (
    AgentAnalyzeRequest,
    AgentAnalyzeResponse,
    AgentQualityCriterion,
    AgentQualityEvaluation,
)


RISKY_CLAIMS = ("保证", "绝对", "全网最低", "销量第一", "100%有效")


def _input_quality(request: AgentAnalyzeRequest) -> AgentQualityCriterion:
    selling_point_score = min(len(request.selling_points), 5) * 2
    keyword_score = min(len(request.keywords), 2) * 2.5
    audience_score = 5 if len(request.target_audience) >= 8 else 3
    goal_score = 5 if len(request.business_goal) >= 10 else 3
    score = round(selling_point_score + keyword_score + audience_score + goal_score)
    return AgentQualityCriterion(
        name="输入信息完整度",
        score=score,
        max_score=25,
        explanation=(
            f"已提供 {len(request.selling_points)} 个卖点、{len(request.keywords)} 个关键词，"
            "并检查了目标用户与经营目标的描述长度。"
        ),
    )


def _business_grounding(result: AgentAnalyzeResponse) -> AgentQualityCriterion:
    strategy_text = " ".join(
        [
            result.strategy.overall_assessment,
            result.strategy.pricing_suggestion,
            result.strategy.marketing_strategy,
        ]
    )
    score = 10
    if any(word in strategy_text for word in ("价格", "利润", "成本", "优惠", "定价")):
        score += 8
    if result.product_analysis.profit <= 0:
        if any(word in result.strategy.risk_warning for word in ("亏", "成本", "利润", "风险")):
            score += 7
    elif result.strategy.pricing_suggestion.strip():
        score += 7
    return AgentQualityCriterion(
        name="业务数据依据",
        score=score,
        max_score=25,
        explanation=(
            f"策略已关联单件利润 {result.product_analysis.profit:.2f} 元和"
            f"利润率 {result.product_analysis.profit_rate_percent:.2f}%。"
        ),
    )


def _actionability(result: AgentAnalyzeResponse) -> AgentQualityCriterion:
    actions = [action.strip() for action in result.strategy.action_plan if action.strip()]
    count_score = 10 if len(actions) >= 3 else 6
    length_score = 8 if actions and sum(map(len, actions)) / len(actions) >= 6 else 4
    unique_score = 7 if len(set(actions)) == len(actions) else 3
    return AgentQualityCriterion(
        name="行动计划可执行性",
        score=count_score + length_score + unique_score,
        max_score=25,
        explanation=f"共生成 {len(actions)} 项行动计划，并检查了内容长度和重复项。",
    )


def _risk_and_format(result: AgentAnalyzeResponse) -> AgentQualityCriterion:
    full_text = " ".join(
        [
            result.strategy.overall_assessment,
            result.strategy.pricing_suggestion,
            result.strategy.marketing_strategy,
            result.strategy.risk_warning,
            *result.strategy.action_plan,
        ]
    )
    risky_hits = [claim for claim in RISKY_CLAIMS if claim in full_text]
    warning_score = 10 if len(result.strategy.risk_warning.strip()) >= 10 else 5
    claim_score = 10 if not risky_hits else 2
    return AgentQualityCriterion(
        name="风险与格式检查",
        score=warning_score + claim_score + 5,
        max_score=25,
        explanation=(
            "风险提醒与结构化字段完整，未发现高风险绝对化承诺。"
            if not risky_hits
            else f"发现可能需要人工核对的表述：{'、'.join(risky_hits)}。"
        ),
    )


def evaluate_agent_result(
    request: AgentAnalyzeRequest,
    result: AgentAnalyzeResponse,
) -> AgentQualityEvaluation:
    """使用确定性规则执行质量门禁，不产生额外大模型调用。"""

    criteria = [
        _input_quality(request),
        _business_grounding(result),
        _actionability(result),
        _risk_and_format(result),
    ]
    overall_score = sum(criterion.score for criterion in criteria)
    if overall_score >= 90:
        grade = "优秀"
    elif overall_score >= 80:
        grade = "良好"
    elif overall_score >= 70:
        grade = "合格"
    else:
        grade = "需要优化"

    suggestions = []
    if criteria[0].score < 22:
        suggestions.append("补充更具体的商品卖点、关键词和目标用户使用场景。")
    if criteria[1].score < 22:
        suggestions.append("让策略更明确地引用价格、成本、利润或优惠方案。")
    if criteria[2].score < 22:
        suggestions.append("把行动计划写成至少三条具体、互不重复的操作。")
    if criteria[3].score < 22:
        suggestions.append("删除绝对化承诺，并补充可核验的风险提醒。")
    if not suggestions:
        suggestions.append("当前结果已通过基础质量门禁，落地前仍建议由运营人员复核。")

    return AgentQualityEvaluation(
        overall_score=overall_score,
        grade=grade,
        passed=overall_score >= 70,
        criteria=criteria,
        suggestions=suggestions,
        evaluator="rule_based_v1",
    )


def ensure_agent_evaluation(
    request: AgentAnalyzeRequest,
    result: AgentAnalyzeResponse,
) -> AgentQualityEvaluation:
    """兼容旧历史记录：缺少评分时按当前规则即时补算。"""

    if result.quality_evaluation is None:
        result.quality_evaluation = evaluate_agent_result(request, result)
    return result.quality_evaluation
