from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent_feedback import AgentFeedback


def get_agent_feedback(database: Session, run_id: int) -> AgentFeedback | None:
    statement = select(AgentFeedback).where(AgentFeedback.run_id == run_id)
    return database.scalar(statement)


def upsert_agent_feedback(
    database: Session,
    *,
    run_id: int,
    rating: str,
    comment: str,
) -> AgentFeedback:
    feedback = get_agent_feedback(database, run_id)
    if feedback is None:
        feedback = AgentFeedback(run_id=run_id, rating=rating, comment=comment)
        database.add(feedback)
    else:
        feedback.rating = rating
        feedback.comment = comment
    database.commit()
    database.refresh(feedback)
    return feedback
