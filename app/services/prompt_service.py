from app.schemas.copywriting import (
    CopywritingPromptRequest,
    CopywritingPromptResponse,
)


SYSTEM_PROMPT = """你是一名专业的电商文案策划师。
你的任务是根据真实商品信息生成清晰、有吸引力且不过度夸大的中文销售文案。
你必须执行严格的“事实白名单”：只有用户明确提供的字段可以当作事实，其他信息必须省略或标为“需验证”。
商品卖点只能原样引用，不得解释、扩展或推导隐藏能力。例如“蓝牙双模”不等于“支持多设备切换”。
目标用户与平台只用于调整表达方式，不能据此推断用户经历、产品使用效果或适用环境。
不得虚构商品参数、性能、功效、场景、销量、认证、库存、优惠、用户评价或体验，也不得用常识补全缺失信息。
除输入中已有数字外，不得添加数量、金额、比例、周期或效果数字。
如果输入中含有夸大或绝对化卖点，不要照抄该承诺，只说明相关信息需要核验。
输出前逐句删除所有无法直接指向事实白名单的产品能力、数字和结论。
输出必须严格符合用户指定的 JSON 格式。"""


def build_copywriting_prompt(
    request: CopywritingPromptRequest,
) -> CopywritingPromptResponse:
    """把结构化商品信息转换成可直接发送给大模型的 Prompt。"""

    selling_points = "\n".join(
        f"{index}. {point}"
        for index, point in enumerate(request.selling_points, start=1)
    )
    keywords = "、".join(request.keywords) if request.keywords else "无指定关键词"

    user_prompt = f"""请为下面的商品生成销售文案：

商品名称：{request.product_name}
商品卖点：
{selling_points}
目标用户：{request.target_audience}
目标平台：{request.platform}
文案语气：{request.tone}
指定关键词：{keywords}

事实白名单：商品名称、卖点原文、目标用户原文、目标平台、文案语气和指定关键词。除此之外均为未知。

写作要求：
1. 标题不超过 20 个汉字。
2. 正文控制在 80 到 150 个汉字。
3. 自然体现商品卖点和目标用户需求。
4. 卖点只能使用输入原文，不得把它解释成新的功能、效果或具体使用体验。
5. 不得编造输入中不存在的数据、使用场景、优惠、承诺、销量、评价、认证、折扣、赠品或试用信息。
6. 除输入已有数字外不得添加任何数字；对缺失信息只能省略或写“需验证”，不得凭常识推测。
7. 目标用户和平台不能作为产品效果或适用场景已经成立的证据。
8. 若输入含夸大承诺，不要复述风险原句。
9. 只返回下面格式的 JSON，不要添加 Markdown 标记或解释：
{{
  "title": "商品标题",
  "selling_copy": "销售正文",
  "call_to_action": "行动引导语"
}}"""

    return CopywritingPromptResponse(
        prompt_version="1.2",
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )
