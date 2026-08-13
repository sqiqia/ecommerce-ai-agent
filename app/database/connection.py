from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """所有 SQLAlchemy 数据库模型的基类。"""


def create_database_engine(database_url: str):
    connect_args = (
        {"check_same_thread": False}
        if database_url.startswith("sqlite")
        else {}
    )
    return create_engine(database_url, connect_args=connect_args)


engine = create_database_engine(settings.database_url)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """为一次 HTTP 请求提供一个数据库会话，并在结束后关闭。"""

    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
