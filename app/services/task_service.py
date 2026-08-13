from typing import Any

from sqlalchemy.orm import Session

from app.models.product_result import ProductResult
from app.models.task import AnalysisTask
from app.repositories.task_repository import add_task, get_task_with_results, list_tasks
from app.schemas.product import ExcelAnalyzeResponse, ExcelRowResult


def raw_to_text(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def result_to_model(result: ExcelRowResult) -> ProductResult:
    analysis = result.analysis
    return ProductResult(
        source_row=result.source_row,
        status=result.status,
        product_name=result.product_name,
        sale_price_raw=raw_to_text(result.sale_price),
        cost_price_raw=raw_to_text(result.cost_price),
        shipping_fee_raw=raw_to_text(result.shipping_fee),
        commission_rate_raw=raw_to_text(result.commission_rate),
        commission=analysis.commission if analysis else None,
        total_cost=analysis.total_cost if analysis else None,
        profit=analysis.profit if analysis else None,
        profit_rate=analysis.profit_rate if analysis else None,
        profitable=analysis.profitable if analysis else None,
        advice=analysis.advice if analysis else None,
        error_reason=result.error_reason,
    )


def save_analysis_task(
    database: Session,
    batch: ExcelAnalyzeResponse,
) -> AnalysisTask:
    task = AnalysisTask(
        filename=batch.filename,
        status="completed",
        total_rows=batch.total_rows,
        success_count=batch.success_count,
        error_count=batch.error_count,
        results=[result_to_model(result) for result in batch.results],
    )
    return add_task(database, task)


def query_tasks(
    database: Session,
    *,
    offset: int,
    limit: int,
) -> tuple[int, list[AnalysisTask]]:
    return list_tasks(database, offset=offset, limit=limit)


def query_task_detail(database: Session, task_id: int) -> AnalysisTask | None:
    return get_task_with_results(database, task_id)
