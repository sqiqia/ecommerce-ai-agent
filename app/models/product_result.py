from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


if TYPE_CHECKING:
    from app.models.task import AnalysisTask


class ProductResult(Base):
    __tablename__ = "product_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_row: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    product_name: Mapped[str | None] = mapped_column(Text)
    sale_price_raw: Mapped[str | None] = mapped_column(Text)
    cost_price_raw: Mapped[str | None] = mapped_column(Text)
    shipping_fee_raw: Mapped[str | None] = mapped_column(Text)
    commission_rate_raw: Mapped[str | None] = mapped_column(Text)

    commission: Mapped[float | None] = mapped_column(Float)
    total_cost: Mapped[float | None] = mapped_column(Float)
    profit: Mapped[float | None] = mapped_column(Float)
    profit_rate: Mapped[float | None] = mapped_column(Float)
    profitable: Mapped[bool | None] = mapped_column(Boolean)
    advice: Mapped[str | None] = mapped_column(Text)
    error_reason: Mapped[str | None] = mapped_column(Text)

    task: Mapped["AnalysisTask"] = relationship(back_populates="results")
