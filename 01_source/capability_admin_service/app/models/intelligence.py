from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.types import BigIntPK, JsonType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CapabilityFeatureFlag(Base):
    __tablename__ = "capability_feature_flag"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(48), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[str] = mapped_column(String(32), nullable=False, default="GLOBAL")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class CapabilityCorridor(Base):
    __tablename__ = "capability_corridor"
    __table_args__ = (UniqueConstraint("code", name="uq_capability_corridor_code"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    from_region_code: Mapped[str] = mapped_column(String(20), nullable=False)
    to_region_code: Mapped[str] = mapped_column(String(20), nullable=False)
    channel_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    default_currency: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)


class CapabilityProfileReadiness(Base):
    __tablename__ = "capability_profile_readiness"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("capability_profile.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    profile_code: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    grade: Mapped[str] = mapped_column(String(2), nullable=False, default="F")
    dimensions_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    gaps_json: Mapped[list] = mapped_column(JsonType, nullable=False, default=list, server_default="[]")
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)


class CapabilityInsight(Base):
    __tablename__ = "capability_insight"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="INFO")
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    entity_type: Mapped[str | None] = mapped_column(String(48), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN", index=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
