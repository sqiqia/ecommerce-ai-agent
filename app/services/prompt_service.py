from app.schemas.copywriting import (
    CopywritingPromptRequest,
    CopywritingPromptResponse,
)


SYSTEM_PROMPT = """你是一名专业的电商文案策划师。
你的任务是根据真实商品信息生成清晰、有吸引力且不过度夸大的中文销售文案。
不得虚构功效、销量、认证或用户评价，输出必须严格符合用户指定的 JSON 格式。"""


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

写作要求：
1. 标题不超过 20 个汉字。
2. 正文控制在 80 到 150 个汉字。
3. 自然体现商品卖点和目标用户需求。
4. 不得编造输入信息中不存在的数据或承诺。
5. 只返回下面格式的 JSON，不要添加 Markdown 标记或解释：
{{
  "title": "商品标题",
  "selling_copy": "销售正文",
  "call_to_action": "行动引导语"
}}"""

    return CopywritingPromptResponse(
        prompt_version="1.0",
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )
