from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.products import router as products_router
from app.api.routes.tasks import router as tasks_router
from app.core.config import settings
from app.database.init_db import init_db


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
    application.include_router(health_router)
    application.include_router(products_router)
    application.include_router(tasks_router)

    @application.get("/", tags=["首页"])
    def root() -> dict[str, str]:
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
        }

    return application


app = create_app()
