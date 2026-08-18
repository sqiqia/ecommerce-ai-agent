from app.schemas.agent import AgentAnalyzeRequest, AgentPrompt
from app.schemas.product import ProductAnalyzeResponse


AGENT_SYSTEM_PROMPT = """你是一名谨慎、专业的电商运营决策 Agent。
事实边界：只有用户本次明确提供的商品资料，以及利润计算工具的结果可以当作已知事实。
利润工具结果是可信数据，不得修改、推测或重新计算成其他数字。
禁止补全或虚构任何未提供的信息，包括但不限于：商品参数与性能、适用环境、认证、销量、评价、库存、用户规模、预算、广告点击成本、转化率和投资回报率。
优惠、赠品、试用、投放等未提供的运营动作只能写成“可选方案”或“需验证”，不得描述成已经存在的事实，也不得随意添加数量或金额。
如果输入中含有夸大或绝对化卖点，不要在方案中照抄该承诺；只说明“输入存在绝对化表述，需要核验”。
不知道的信息必须明确写“未提供”或“需验证”，不能用常识猜测。
输出必须严格符合用户指定的 JSON 格式。"""


def build_agent_prompt(
    request: AgentAnalyzeRequest,
    analysis: ProductAnalyzeResponse,
) -> AgentPrompt:
    """把商品资料和工具执行结果组合成运营策略 Prompt。"""

    selling_points = "、".join(request.selling_points)
    keywords = "、".join(request.keywords) if request.keywords else "无指定关键词"

    user_prompt = f"""请根据以下资料制定商品运营方案。

一、商品资料
商品名称：{request.product_name}
商品卖点：{selling_points}
目标用户：{request.target_audience}
目标平台：{request.platform}
沟通语气：{request.tone}
指定关键词：{keywords}
经营目标：{request.business_goal}

二、利润计算工具结果
销售价格：{analysis.sale_price:.2f} 元
平台佣金：{analysis.commission:.2f} 元
总成本：{analysis.total_cost:.2f} 元
单件利润：{analysis.profit:.2f} 元
利润率：{analysis.profit_rate_percent:.2f}%
工具判断：{analysis.advice}

三、输出要求
1. 所有建议必须结合上面的商品和利润数据。
2. 如果利润率偏低或亏损，优先提示风险，不能只给营销建议。
3. 行动计划按执行顺序给出 2 到 5 项具体动作。
4. 所有推测和新增运营建议必须标记为“可选方案”或“需验证”，不能写成现状。
5. 不得擅自添加预算、赠品、试用人数、优惠金额、获客成本、转化率或其他数字。
6. 不得扩展输入中没有的产品参数、性能、技术行为、适用场景、销量、评价或认证。
7. 若输入含夸大承诺，只写“输入存在绝对化表述，需要核验”，不要复述风险原句。
8. 只返回下面格式的 JSON，不要添加 Markdown 或解释：
{{
  "overall_assessment": "商品整体经营判断",
  "pricing_suggestion": "定价和成本建议",
  "marketing_strategy": "面向目标平台和用户的营销策略",
  "risk_warning": "需要重点注意的风险",
  "action_plan": ["第一项行动", "第二项行动", "第三项行动"]
}}"""

    return AgentPrompt(
        prompt_version="1.1",
        system_prompt=AGENT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )
