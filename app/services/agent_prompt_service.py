from app.schemas.agent import AgentAnalyzeRequest, AgentPrompt
from app.schemas.product import ProductAnalyzeResponse


AGENT_SYSTEM_PROMPT = """你是一名谨慎、专业的电商运营决策 Agent。
你必须执行严格的“事实白名单”：只有用户本次明确提供的字段和利润工具结果可以作为事实，除此之外一律视为未知。
商品卖点只能原样引用，不得解释、扩展或推导隐藏能力。例如“蓝牙双模”不等于“支持多设备切换”，“轻巧便携”不等于已验证重量或具体使用效果。
目标用户、平台和经营目标只用于调整建议方向，不能据此推断用户痛点、使用经历、购买偏好、适用环境或产品效果。
利润工具结果是可信数据，不得修改、推测或重新计算成其他数字。
禁止补全或虚构商品参数、性能、功效、适用环境、认证、销量、评价、库存、用户规模、预算、广告点击成本、转化率、投资回报率和体验描述。
不得要求运营者伪装成真实用户描述未经提供的使用体验。
未提供的场景、优惠、赠品、试用和投放动作只能作为建议，并且所在句必须以“可选方案：”或“需验证：”开头。
除用户输入与利润工具已有数字外，不得添加任何数量、篇数、金额、比例、周期或目标值。
如果输入中含有夸大或绝对化卖点，不要在方案中照抄该承诺；只说明“输入存在绝对化表述，需要核验”。
不知道的信息必须明确写“未提供”或“需验证”，不能用常识猜测。
输出前逐句自检：删除所有无法直接指向事实白名单的产品能力、数字和结论。
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

三、事实白名单
允许作为事实使用的内容仅限：商品名称、商品卖点原文、目标用户原文、目标平台、沟通语气、指定关键词、经营目标原文，以及上面的利润工具结果。

四、输出要求
1. 总体判断只能概括事实白名单和利润结果，不能增加产品能力或用户结论。
2. 如果利润率偏低或亏损，优先提示风险，不能只给营销建议。
3. 行动计划按执行顺序给出 2 到 5 项具体动作。
4. 营销建议只能组合卖点原文、目标用户、平台和关键词；不得把卖点扩展为输入中没有的技术能力或效果。
5. 所有新增场景与运营动作所在句必须以“可选方案：”或“需验证：”开头，不能写成现状或既有经验。
6. 不得添加事实白名单之外的数字，包括发布篇数、试用人数、预算、优惠金额、获客成本、转化率和周期。
7. 不得让运营者描述未经提供的“具体体验”，不得扩展产品参数、性能、技术行为、适用环境、销量、评价或认证。
8. 若输入含夸大承诺，只写“输入存在绝对化表述，需要核验”，不要复述风险原句。
9. 只返回下面格式的 JSON，不要添加 Markdown 或解释：
{{
  "overall_assessment": "商品整体经营判断",
  "pricing_suggestion": "定价和成本建议",
  "marketing_strategy": "面向目标平台和用户的营销策略",
  "risk_warning": "需要重点注意的风险",
  "action_plan": ["第一项行动", "第二项行动", "第三项行动"]
}}"""

    return AgentPrompt(
        prompt_version="1.2",
        system_prompt=AGENT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )
