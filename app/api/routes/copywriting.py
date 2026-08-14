from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.schemas.copywriting import (
    CopywritingGenerateResponse,
    CopywritingPromptRequest,
    CopywritingPromptResponse,
)
from app.services.ai_client import (
    AIChatClient,
    AIConfigurationError,
    AIProviderError,
    AIResponseError,
)
from app.services.prompt_service import build_copywriting_prompt


router = APIRouter(prefix="/copywriting", tags=["AI 文案"])


def get_ai_client() -> AIChatClient:
    """根据本机环境变量创建大模型客户端。"""

    return AIChatClient(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
        model=settings.ai_model,
        timeout_seconds=settings.ai_timeout_seconds,
    )


AIClientDependency = Annotated[AIChatClient, Depends(get_ai_client)]


@router.post(
    "/prompt-preview",
    response_model=CopywritingPromptResponse,
    summary="预览商品文案 Prompt",
)
def preview_copywriting_prompt(
    request: CopywritingPromptRequest,
) -> CopywritingPromptResponse:
    """在调用真实大模型前检查最终发送的 Prompt。"""

    return build_copywriting_prompt(request)


@router.post(
    "/generate",
    response_model=CopywritingGenerateResponse,
    summary="调用大模型生成商品文案",
    responses={
        502: {"description": "大模型服务连接失败或响应格式错误"},
        503: {"description": "本机尚未完成大模型配置"},
    },
)
def generate_copywriting(
    request: CopywritingPromptRequest,
    ai_client: AIClientDependency,
) -> CopywritingGenerateResponse:
    """构建 Prompt、调用大模型并返回结构化商品文案。"""

    prompt = build_copywriting_prompt(request)
    try:
        generated = ai_client.generate(prompt)
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

    return CopywritingGenerateResponse(
        **generated.model_dump(),
        model=ai_client.model,
        prompt_version=prompt.prompt_version,
    )
