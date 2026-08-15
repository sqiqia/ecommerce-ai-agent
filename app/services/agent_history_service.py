from sqlalchemy.orm import Session

from app.models.agent_run import AgentRun
from app.repositories.agent_run_repository import (
    add_agent_run,
    get_agent_run,
    list_agent_runs,
)
from app.schemas.agent import (
    AgentAnalyzeRequest,
    AgentAnalyzeResponse,
    AgentRunDetailResponse,
    AgentRunSummaryResponse,
)


def save_agent_run(
    database: Session,
    request: AgentAnalyzeRequest,
    result: AgentAnalyzeResponse,
) -> AgentRun:
    """保存安全的业务输入与 Agent 结构化结果，不包含 API Key。"""

    run = AgentRun(
        product_name=request.product_name,
        business_goal=request.business_goal,
        model=result.model,
        profit=result.product_analysis.profit,
        profit_rate_percent=result.product_analysis.profit_rate_percent,
        overall_assessment=result.strategy.overall_assessment,
        request_json=request.model_dump_json(),
        result_json=result.model_dump_json(),
    )
    return add_agent_run(database, run)


def to_agent_run_summary(run: AgentRun) -> AgentRunSummaryResponse:
    return AgentRunSummaryResponse(
        id=run.id,
        product_name=run.product_name,
        business_goal=run.business_goal,
        model=run.model,
        profit=run.profit,
        profit_rate_percent=run.profit_rate_percent,
        overall_assessment=run.overall_assessment,
        created_at=run.created_at,
    )


def to_agent_run_detail(run: AgentRun) -> AgentRunDetailResponse:
    request = AgentAnalyzeRequest.model_validate_json(run.request_json)
    result = AgentAnalyzeResponse.model_validate_json(run.result_json)
    result.run_id = run.id
    return AgentRunDetailResponse(
        **to_agent_run_summary(run).model_dump(),
        request=request,
        result=result,
    )


def query_agent_runs(
    database: Session,
    *,
    offset: int,
    limit: int,
) -> tuple[int, list[AgentRun]]:
    return list_agent_runs(database, offset=offset, limit=limit)


def query_agent_run_detail(database: Session, run_id: int) -> AgentRun | None:
    return get_agent_run(database, run_id)
