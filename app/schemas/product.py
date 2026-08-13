from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductAnalyzeRequest(BaseModel):
    """商品利润分析接口接收的数据。"""

    model_config = ConfigDict(str_strip_whitespace=True)

    product_name: str = Field(
        min_length=1,
        max_length=100,
        description="商品名称，去除前后空格后不能为空",
        examples=["无线鼠标"],
    )
    sale_price: float = Field(
        gt=0,
        allow_inf_nan=False,
        description="商品售价，必须大于 0",
        examples=[79],
    )
    cost_price: float = Field(
        ge=0,
        allow_inf_nan=False,
        description="商品采购成本，不能为负数",
        examples=[35],
    )
    shipping_fee: float = Field(
        default=0,
        ge=0,
        allow_inf_nan=False,
        description="单件商品运费，不能为负数",
        examples=[8],
    )
    commission_rate: float = Field(
        default=0.05,
        ge=0,
        le=1,
        allow_inf_nan=False,
        description="平台佣金率，5% 应输入 0.05",
        examples=[0.05],
    )

    @field_validator("product_name")
    @classmethod
    def product_name_must_not_be_blank(cls, value: str) -> str:
        if not value:
            raise ValueError("商品名称不能为空")
        return value


class ProductAnalyzeResponse(BaseModel):
    """商品利润分析接口返回的数据。"""

    product_name: str
    sale_price: float
    commission: float
    total_cost: float
    profit: float
    profit_rate: float
    profit_rate_percent: float
    profitable: bool
    advice: str


class ExcelRowResult(BaseModel):
    """Excel 中一行商品数据的处理结果。"""

    source_row: int
    status: Literal["success", "error"]
    product_name: str | None = None
    sale_price: float | str | None = None
    cost_price: float | str | None = None
    shipping_fee: float | str | None = None
    commission_rate: float | str | None = None
    analysis: ProductAnalyzeResponse | None = None
    error_reason: str | None = None


class ExcelAnalyzeResponse(BaseModel):
    """整张商品 Excel 表的批量分析结果。"""

    filename: str
    total_rows: int
    success_count: int
    error_count: int
    results: list[ExcelRowResult]
