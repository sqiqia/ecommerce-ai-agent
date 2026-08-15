from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.agent_run import AgentRun


def add_agent_run(database: Session, run: AgentRun) -> AgentRun:
    database.add(run)
    database.commit()
    database.refresh(run)
    return run


def list_agent_runs(
    database: Session,
    *,
    offset: int,
    limit: int,
) -> tuple[int, list[AgentRun]]:
    total = database.scalar(select(func.count()).select_from(AgentRun)) or 0
    statement = (
        select(AgentRun)
        .order_by(AgentRun.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return total, list(database.scalars(statement).all())


def get_agent_run(database: Session, run_id: int) -> AgentRun | None:
    return database.get(AgentRun, run_id)
