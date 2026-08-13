from collections.abc import Generator
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy.orm import Session, sessionmaker

from app.database.connection import Base, create_database_engine, get_db
from app.main import app


def create_sample_excel() -> bytes:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(["商品名称", "售价", "成本", "运费", "佣金率"])
    worksheet.append(["无线鼠标", 79, 35, 8, 0.05])
    worksheet.append(["手机壳", 19, 15, 5, 0.05])
    worksheet.append([None, 29, 10, 4, 0.05])
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    temp_directory = Path("tests/.tmp")
    temp_directory.mkdir(parents=True, exist_ok=True)
    database_path = temp_directory / f"test_tasks_{uuid4().hex}.db"
    test_engine = create_database_engine(f"sqlite:///{database_path}")
    testing_session = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )
    Base.metadata.create_all(bind=test_engine)

    def override_get_db() -> Generator[Session, None, None]:
        database = testing_session()
        try:
            yield database
        finally:
            database.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()
        database_path.unlink(missing_ok=True)


def test_create_list_and_get_task(client: TestClient) -> None:
    create_response = client.post(
        "/tasks/analyze-excel",
        files={"file": ("products.xlsx", create_sample_excel())},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] == 1
    assert created["filename"] == "products.xlsx"
    assert created["status"] == "completed"
    assert created["total_rows"] == 3
    assert created["success_count"] == 2
    assert created["error_count"] == 1
    assert len(created["results"]) == 3
    assert created["results"][0]["profit"] == 32.05
    assert created["results"][2]["status"] == "error"

    list_response = client.get("/tasks")
    assert list_response.status_code == 200
    listing = list_response.json()
    assert listing["total"] == 1
    assert listing["items"][0]["id"] == 1
    assert "results" not in listing["items"][0]

    detail_response = client.get("/tasks/1")
    assert detail_response.status_code == 200
    assert detail_response.json() == created


def test_task_data_persists_across_database_sessions(client: TestClient) -> None:
    response = client.post(
        "/tasks/analyze-excel",
        files={"file": ("products.xlsx", create_sample_excel())},
    )
    assert response.status_code == 201

    first_request = client.get("/tasks/1")
    second_request = client.get("/tasks/1")

    assert first_request.status_code == 200
    assert second_request.status_code == 200
    assert second_request.json()["results"][0]["product_name"] == "无线鼠标"


def test_get_unknown_task_returns_404(client: TestClient) -> None:
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "任务不存在"


def test_task_list_supports_pagination(client: TestClient) -> None:
    for filename in ("first.xlsx", "second.xlsx"):
        response = client.post(
            "/tasks/analyze-excel",
            files={"file": (filename, create_sample_excel())},
        )
        assert response.status_code == 201

    response = client.get("/tasks", params={"offset": 0, "limit": 1})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1
    assert body["items"][0]["filename"] == "second.xlsx"
