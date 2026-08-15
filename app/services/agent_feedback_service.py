from sqlalchemy.orm import Session

from app.models.agent_feedback import AgentFeedback
from app.repositories.agent_feedback_repository import (
    get_agent_feedback,
    upsert_agent_feedback,
)
from app.schemas.agent import AgentFeedbackRequest, AgentFeedbackResponse


def to_feedback_response(feedback: AgentFeedback | None) -> AgentFeedbackResponse | None:
    if feedback is None:
        return None
    return AgentFeedbackResponse(
        run_id=feedback.run_id,
        rating=feedback.rating,
        comment=feedback.comment,
        created_at=feedback.created_at,
    )


def query_agent_feedback(database: Session, run_id: int) -> AgentFeedbackResponse | None:
    return to_feedback_response(get_agent_feedback(database, run_id))


def save_agent_feedback(
    database: Session,
    run_id: int,
    request: AgentFeedbackRequest,
) -> AgentFeedbackResponse:
    feedback = upsert_agent_feedback(
        database,
        run_id=run_id,
        rating=request.rating,
        comment=request.comment.strip(),
    )
    response = to_feedback_response(feedback)
    if response is None:  # 防御性判断；刚保存的反馈按设计一定存在。
        raise RuntimeError("反馈保存失败")
    return response
