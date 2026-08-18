from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.ai import ModelTokenUsage


class CopywritingPromptRequest(BaseModel):
    """生成商品文案 Prompt 时接收的数据。"""

    model_config = ConfigDict(str_strip_whitespace=True)

    product_name: str = Field(
        min_length=1,
        max_length=100,
        description="商品名称",
        examples=["无线鼠标"],
    )
    selling_points: list[str] = Field(
        min_length=1,
        max_length=5,
        description="1 到 5 个商品卖点",
        examples=[["静音按键", "蓝牙双模", "轻巧便携"]],
    )
    target_audience: str = Field(
        default="普通消费者",
        min_length=1,
        max_length=100,
        description="目标用户群体",
        examples=["经常出差的职场人士"],
    )
    platform: Literal["通用", "淘宝", "抖音", "小红书"] = Field(
        default="通用",
        description="文案投放平台",
    )
    tone: Literal["专业", "亲切", "活泼", "简洁"] = Field(
        default="亲切",
        description="文案语气",
    )
    keywords: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="希望文案包含的关键词，最多 5 个",
        examples=[["办公好物", "便携"]],
    )

    @field_validator("selling_points", "keywords")
    @classmethod
    def list_items_must_not_be_blank(cls, value: list[str]) -> list[str]:
        cleaned_items = [item.strip() for item in value]
        if any(not item for item in cleaned_items):
            raise ValueError("列表中的内容不能为空")
        return cleaned_items


class CopywritingPromptResponse(BaseModel):
    """返回给前端或大模型调用层的标准 Prompt。"""

    prompt_version: str
    system_prompt: str
    user_prompt: str


class GeneratedCopywriting(BaseModel):
    """大模型生成并经过校验的文案内容。"""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=40)
    selling_copy: str = Field(min_length=1, max_length=500)
    call_to_action: str = Field(min_length=1, max_length=100)


class CopywritingGenerateResponse(GeneratedCopywriting):
    """文案生成接口最终返回的数据。"""

    model: str
    prompt_version: str
    token_usage: ModelTokenUsage | None = None
