from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.types import BigIntPK


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CapabilityProfileWebhook(Base):
    __tablename__ = "capability_profile_webhook"
    __table_args__ = (UniqueConstraint("profile_id", name="uq_capability_profile_webhook_profile"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("capability_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profile_code: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    secret_preview: Mapped[str | None] = mapped_column(String(32), nullable=True)
    event_types_json: Mapped[str] = mapped_column(Text, nullable=False, default='["capability.profile.changed"]')
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    profile: Mapped["CapabilityProfile"] = relationship(back_populates="webhooks")


class CapabilityProfileApiKey(Base):
    __tablename__ = "capability_profile_api_key"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("capability_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profile_code: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rotated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)

    profile: Mapped["CapabilityProfile"] = relationship(back_populates="api_keys")
