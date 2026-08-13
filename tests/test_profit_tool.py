from decimal import Decimal

from app.tools.profit_tool import calculate_profit


def test_calculate_profit_with_normal_product() -> None:
    result = calculate_profit(
        sale_price=Decimal("79"),
        cost_price=Decimal("35"),
        shipping_fee=Decimal("8"),
        commission_rate=Decimal("0.05"),
    )

    assert result.commission == Decimal("3.95")
    assert result.total_cost == Decimal("46.95")
    assert result.profit == Decimal("32.05")
    assert result.profit_rate == Decimal("0.4057")
    assert result.profitable is True
    assert result.advice == "利润正常，可以销售"


def test_calculate_profit_with_loss_product() -> None:
    result = calculate_profit(
        sale_price=Decimal("19"),
        cost_price=Decimal("15"),
        shipping_fee=Decimal("5"),
        commission_rate=Decimal("0.05"),
    )

    assert result.profit == Decimal("-1.95")
    assert result.profitable is False
    assert result.advice == "该商品会亏损，不建议销售"
