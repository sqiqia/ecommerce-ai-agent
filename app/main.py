from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.copywriting import router as copywriting_router
from app.api.routes.health import router as health_router
from app.api.routes.products import router as products_router
from app.api.routes.tasks import router as tasks_router
from app.core.config import settings
from app.database.init_db import init_db


WEB_DIR = Path(__file__).resolve().parent / "web"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="商品数据分析、利润计算、AI 文案生成和自动化处理系统",
        lifespan=lifespan,
    )
    application.include_router(copywriting_router)
    application.include_router(health_router)
    application.include_router(products_router)
    application.include_router(tasks_router)
    application.mount(
        "/static",
        StaticFiles(directory=WEB_DIR),
        name="static",
    )

    @application.get("/", include_in_schema=False, response_class=FileResponse)
    def root() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")

    @application.get("/api-info", tags=["系统信息"], summary="查看应用基本信息")
    def api_info() -> dict[str, str | bool]:
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "ai_model": settings.ai_model or "未配置",
            "ai_configured": bool(
                settings.ai_api_key
                and settings.ai_base_url
                and settings.ai_model
            ),
        }

    return application


app = create_app()
