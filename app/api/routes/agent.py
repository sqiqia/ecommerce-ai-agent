from fastapi import APIRouter, HTTPException, status

from app.api.routes.copywriting import AIClientDependency
from app.schemas.agent import AgentAnalyzeRequest, AgentAnalyzeResponse
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
) -> AgentAnalyzeResponse:
    """执行利润工具与大模型编排，并返回完整执行轨迹。"""

    try:
        return run_ecommerce_agent(request, ai_client)
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
