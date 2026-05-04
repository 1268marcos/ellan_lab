from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.core.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProductsCache(Base):
    __tablename__ = "products_cache"

    sku_id = Column(String(255), primary_key=True)
    partner_id = Column(String(36), nullable=True, index=True)
    partner_sku = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(String(64), nullable=False, index=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    width_mm = Column(Integer, nullable=True)
    height_mm = Column(Integer, nullable=True)
    depth_mm = Column(Integer, nullable=True)
    weight_g = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    requires_signature = Column(Boolean, nullable=False, default=False)
    is_hazardous = Column(Boolean, nullable=False, default=False)
    temperature_zone = Column(String(32), nullable=False, default="AMBIENT")
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    synced_at = Column(DateTime(timezone=True), nullable=True)
