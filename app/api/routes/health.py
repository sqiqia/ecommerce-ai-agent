from datetime import UTC, datetime

from fastapi import APIRouter


router = APIRouter(prefix="/health", tags=["系统状态"])


@router.get("")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "电商运营自动化 Agent 正常运行",
        "time": datetime.now(UTC).isoformat(timespec="seconds"),
    }
