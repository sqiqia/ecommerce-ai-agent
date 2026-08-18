from pydantic import BaseModel, Field


class ModelTokenUsage(BaseModel):
    """供应商返回的 Token 用量与本地单价计算出的预估费用。"""

    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    cached_input_tokens: int = Field(default=0, ge=0)
    pricing_model: str | None = None
    input_price_per_million_yuan: float | None = Field(default=None, ge=0)
    output_price_per_million_yuan: float | None = Field(default=None, ge=0)
    estimated_input_cost_yuan: float | None = Field(default=None, ge=0)
    estimated_output_cost_yuan: float | None = Field(default=None, ge=0)
    estimated_total_cost_yuan: float | None = Field(default=None, ge=0)
    pricing_note: str
