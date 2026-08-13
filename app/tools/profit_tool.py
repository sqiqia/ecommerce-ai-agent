from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


MONEY_PRECISION = Decimal("0.01")
RATE_PRECISION = Decimal("0.0001")


@dataclass(frozen=True)
class ProfitCalculation:
    commission: Decimal
    total_cost: Decimal
    profit: Decimal
    profit_rate: Decimal
    profitable: bool
    advice: str


def round_money(value: Decimal) -> Decimal:
    """金额统一使用四舍五入并保留两位小数。"""

    return value.quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


def calculate_profit(
    *,
    sale_price: Decimal,
    cost_price: Decimal,
    shipping_fee: Decimal,
    commission_rate: Decimal,
) -> ProfitCalculation:
    """计算一个商品的佣金、总成本、利润、利润率和经营建议。"""

    commission = round_money(sale_price * commission_rate)
    total_cost = round_money(cost_price + shipping_fee + commission)
    profit = round_money(sale_price - total_cost)
    profit_rate = (profit / sale_price).quantize(
        RATE_PRECISION,
        rounding=ROUND_HALF_UP,
    )

    if profit <= 0:
        advice = "该商品会亏损，不建议销售"
    elif profit_rate < Decimal("0.15"):
        advice = "利润率较低，建议降低成本或提高售价"
    elif profit_rate < Decimal("0.30"):
        advice = "利润一般，可以继续优化"
    else:
        advice = "利润正常，可以销售"

    return ProfitCalculation(
        commission=commission,
        total_cost=total_cost,
        profit=profit,
        profit_rate=profit_rate,
        profitable=profit > 0,
        advice=advice,
    )
