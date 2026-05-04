from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Product(Base):
    __tablename__ = "products"

    sku_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    partner_sku: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[str] = mapped_column(String(64), ForeignKey("categories.id"), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="BRL")
    images: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    requires_signature: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_hazardous: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    temperature_zone: Mapped[str] = mapped_column(String(32), nullable=False, default="AMBIENT")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    dimensions: Mapped["ProductDimensions | None"] = relationship(
        "ProductDimensions", back_populates="product", uselist=False, cascade="all, delete-orphan"
    )


class ProductVersion(Base):
    __tablename__ = "product_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sku_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.sku_id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
