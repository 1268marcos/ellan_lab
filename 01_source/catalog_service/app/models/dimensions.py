from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProductDimensions(Base):
    __tablename__ = "product_dimensions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    product_sku_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.sku_id"), nullable=False, unique=True)
    width_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    depth_mm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    product = relationship("Product", back_populates="dimensions")  # type: ignore[var-annotated]
