from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PartnerProductRule(Base):
    __tablename__ = "partner_product_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    category_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    allowed_temperature_zones: Mapped[str] = mapped_column(Text, nullable=False, default='["AMBIENT"]')
    max_weight_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requires_signature: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_hazardous_allowed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    overrides_global: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Locker(Base):
    __tablename__ = "lockers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    partner_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    site_id: Mapped[str] = mapped_column(String(64), nullable=False)
    slot_size: Mapped[str] = mapped_column(String(8), nullable=False)
    max_weight_g: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
