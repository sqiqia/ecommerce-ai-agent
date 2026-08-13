from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class StoredProductResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_row: int
    status: Literal["success", "error"]
    product_name: str | None
    sale_price_raw: str | None
    cost_price_raw: str | None
    shipping_fee_raw: str | None
    commission_rate_raw: str | None
    commission: float | None
    total_cost: float | None
    profit: float | None
    profit_rate: float | None
    profitable: bool | None
    advice: str | None
    error_reason: str | None


class TaskSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    status: str
    total_rows: int
    success_count: int
    error_count: int
    created_at: datetime


class TaskDetailResponse(TaskSummaryResponse):
    results: list[StoredProductResultResponse]


class TaskListResponse(BaseModel):
    total: int
    items: list[TaskSummaryResponse]
