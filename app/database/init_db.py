from app.database.connection import Base, engine
from app.models import product_result, task  # noqa: F401


def init_db() -> None:
    """创建尚不存在的数据表；不会删除已有数据。"""

    Base.metadata.create_all(bind=engine)
