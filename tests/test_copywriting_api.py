from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_preview_copywriting_prompt() -> None:
    response = client.post(
        "/copywriting/prompt-preview",
        json={
            "product_name": "  无线鼠标  ",
            "selling_points": [" 静音按键 ", "蓝牙双模", "轻巧便携"],
            "target_audience": "经常出差的职场人士",
            "platform": "小红书",
            "tone": "亲切",
            "keywords": ["办公好物", "便携"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["prompt_version"] == "1.0"
    assert "专业的电商文案策划师" in body["system_prompt"]
    assert "商品名称：无线鼠标" in body["user_prompt"]
    assert "1. 静音按键" in body["user_prompt"]
    assert "目标平台：小红书" in body["user_prompt"]
    assert "指定关键词：办公好物、便携" in body["user_prompt"]
    assert '"selling_copy"' in body["user_prompt"]


def test_preview_prompt_rejects_blank_selling_point() -> None:
    response = client.post(
        "/copywriting/prompt-preview",
        json={
            "product_name": "无线鼠标",
            "selling_points": ["静音按键", "   "],
        },
    )

    assert response.status_code == 422

def test_preview_prompt_rejects_more_than_five_selling_points() -> None:
    response = client.post(
        "/copywriting/prompt-preview",
        json={
            "product_name": "无线鼠标",
            "selling_points": ["卖点1", "卖点2", "卖点3", "卖点4", "卖点5", "卖点6"],
        },
    )

    assert response.status_code == 422
