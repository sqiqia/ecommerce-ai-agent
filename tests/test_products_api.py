from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_analyze_product_api() -> None:
    response = client.post(
        "/products/analyze",
        json={
            "product_name": "  无线鼠标  ",
            "sale_price": 79,
            "cost_price": 35,
            "shipping_fee": 8,
            "commission_rate": 0.05,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "product_name": "无线鼠标",
        "sale_price": 79.0,
        "commission": 3.95,
        "total_cost": 46.95,
        "profit": 32.05,
        "profit_rate": 0.4057,
        "profit_rate_percent": 40.57,
        "profitable": True,
        "advice": "利润正常，可以销售",
    }


def test_analyze_product_rejects_zero_sale_price() -> None:
    response = client.post(
        "/products/analyze",
        json={
            "product_name": "测试商品",
            "sale_price": 0,
            "cost_price": 10,
        },
    )

    assert response.status_code == 422


def test_analyze_product_rejects_blank_name() -> None:
    response = client.post(
        "/products/analyze",
        json={
            "product_name": "   ",
            "sale_price": 20,
            "cost_price": 10,
        },
    )

    assert response.status_code == 422


def test_analyze_product_rejects_invalid_commission_rate() -> None:
    response = client.post(
        "/products/analyze",
        json={
            "product_name": "测试商品",
            "sale_price": 20,
            "cost_price": 10,
            "commission_rate": 5,
        },
    )

    assert response.status_code == 422
