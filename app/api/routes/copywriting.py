from fastapi import APIRouter

from app.schemas.copywriting import (
    CopywritingPromptRequest,
    CopywritingPromptResponse,
)
from app.services.prompt_service import build_copywriting_prompt


router = APIRouter(prefix="/copywriting", tags=["AI 文案"])


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
