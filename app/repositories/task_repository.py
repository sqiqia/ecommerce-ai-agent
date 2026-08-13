from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.task import AnalysisTask


def add_task(database: Session, task: AnalysisTask) -> AnalysisTask:
    database.add(task)
    database.commit()
    database.refresh(task)
    return task


def list_tasks(
    database: Session,
    *,
    offset: int,
    limit: int,
) -> tuple[int, list[AnalysisTask]]:
    total = database.scalar(select(func.count()).select_from(AnalysisTask)) or 0
    statement = (
        select(AnalysisTask)
        .order_by(AnalysisTask.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return total, list(database.scalars(statement).all())


def get_task_with_results(
    database: Session,
    task_id: int,
) -> AnalysisTask | None:
    statement = (
        select(AnalysisTask)
        .where(AnalysisTask.id == task_id)
        .options(selectinload(AnalysisTask.results))
    )
    return database.scalar(statement)
