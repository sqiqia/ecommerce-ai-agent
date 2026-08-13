from decimal import Decimal

from app.schemas.product import ProductAnalyzeRequest, ProductAnalyzeResponse
from app.tools.profit_tool import calculate_profit


def to_decimal(value: float) -> Decimal:
    """先转成字符串再创建 Decimal，避免直接使用二进制浮点误差。"""

    return Decimal(str(value))


def analyze_product(
    product: ProductAnalyzeRequest,
) -> ProductAnalyzeResponse:
    calculation = calculate_profit(
        sale_price=to_decimal(product.sale_price),
        cost_price=to_decimal(product.cost_price),
        shipping_fee=to_decimal(product.shipping_fee),
        commission_rate=to_decimal(product.commission_rate),
    )

    return ProductAnalyzeResponse(
        product_name=product.product_name,
        sale_price=product.sale_price,
        commission=float(calculation.commission),
        total_cost=float(calculation.total_cost),
        profit=float(calculation.profit),
        profit_rate=float(calculation.profit_rate),
        profit_rate_percent=float(calculation.profit_rate * 100),
        profitable=calculation.profitable,
        advice=calculation.advice,
    )
