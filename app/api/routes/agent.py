from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.routes.copywriting import AIClientDependency
from app.database.connection import get_db
from app.schemas.agent import (
    AgentAnalyzeRequest,
    AgentAnalyzeResponse,
    AgentFeedbackRequest,
    AgentFeedbackResponse,
    AgentRunDetailResponse,
    AgentRunListResponse,
    AgentRuntimeMetrics,
)
from app.services.agent_feedback_service import save_agent_feedback
from app.services.agent_history_service import (
    query_agent_run_detail,
    query_agent_runs,
    save_agent_run,
    to_agent_run_detail,
    to_agent_run_summary,
)
from app.services.agent_service import run_ecommerce_agent
from app.services.ai_client import (
    AIConfigurationError,
    AIProviderError,
    AIResponseError,
)


router = APIRouter(prefix="/agent", tags=["电商运营 Agent"])


@router.post(
    "/analyze",
    response_model=AgentAnalyzeResponse,
    summary="调用工具并生成商品运营方案",
    responses={
        502: {"description": "大模型连接失败或响应格式错误"},
        503: {"description": "本机尚未完成大模型配置"},
    },
)
def analyze_with_agent(
    request: AgentAnalyzeRequest,
    ai_client: AIClientDependency,
    database: Session = Depends(get_db),
) -> AgentAnalyzeResponse:
    """执行利润工具与大模型编排，并返回完整执行轨迹。"""

    started_at = perf_counter()
    try:
        result = run_ecommerce_agent(request, ai_client)
    except AIConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except (AIProviderError, AIResponseError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    result.runtime_metrics = AgentRuntimeMetrics(
        duration_ms=round((perf_counter() - started_at) * 1000),
        model_call_count=1,
    )
    saved_run = save_agent_run(database, request, result)
    result.run_id = saved_run.id
    return result


@router.get(
    "/runs",
    response_model=AgentRunListResponse,
    summary="查看 Agent 历史记录",
)
def list_agent_run_history(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    database: Session = Depends(get_db),
) -> AgentRunListResponse:
    total, runs = query_agent_runs(database, offset=offset, limit=limit)
    return AgentRunListResponse(
        total=total,
        items=[to_agent_run_summary(database, run) for run in runs],
    )


@router.post(
    "/runs/{run_id}/feedback",
    response_model=AgentFeedbackResponse,
    summary="保存用户对 Agent 结果的反馈",
)
def submit_agent_run_feedback(
    run_id: int,
    request: AgentFeedbackRequest,
    database: Session = Depends(get_db),
) -> AgentFeedbackResponse:
    if query_agent_run_detail(database, run_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent 运行记录不存在",
        )
    return save_agent_feedback(database, run_id, request)


@router.get(
    "/runs/{run_id}",
    response_model=AgentRunDetailResponse,
    summary="回放一次 Agent 运行详情",
)
def get_agent_run_history(
    run_id: int,
    database: Session = Depends(get_db),
) -> AgentRunDetailResponse:
    run = query_agent_run_detail(database, run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent 运行记录不存在",
        )
    return to_agent_run_detail(database, run)
