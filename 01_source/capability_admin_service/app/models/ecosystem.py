from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.types import BigIntPK, JsonType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CapabilityEcosystemSegment(Base):
    __tablename__ = "capability_ecosystem_segment"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    players: Mapped[list["CapabilityEcosystemPlayer"]] = relationship(back_populates="segment")


class CapabilityEcosystemPlayer(Base):
    __tablename__ = "capability_ecosystem_player"
    __table_args__ = (UniqueConstraint("code", name="uq_capability_ecosystem_player_code"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(48), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    segment_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("capability_ecosystem_segment.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    country_codes: Mapped[str] = mapped_column(String(120), nullable=False, default="*")
    headquarters_country: Mapped[str | None] = mapped_column(String(2), nullable=True)
    integration_protocol: Mapped[str] = mapped_column(String(20), nullable=False, default="REST")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    segment: Mapped["CapabilityEcosystemSegment"] = relationship(back_populates="players")
    bindings: Mapped[list["CapabilityProfilePlayerBinding"]] = relationship(back_populates="player")
    integrations: Mapped[list["CapabilityPlayerIntegration"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )
    locker_presences: Mapped[list["CapabilityPlayerLockerPresence"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )


class CapabilityProfilePlayerBinding(Base):
    __tablename__ = "capability_profile_player_binding"
    __table_args__ = (
        UniqueConstraint("profile_id", "player_id", name="uq_capability_profile_player_binding"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    profile_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("capability_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("capability_ecosystem_player.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profile_code: Mapped[str] = mapped_column(String(160), nullable=False)
    player_code: Mapped[str] = mapped_column(String(48), nullable=False)
    binding_role: Mapped[str] = mapped_column(String(32), nullable=False, default="PRIMARY")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)

    player: Mapped["CapabilityEcosystemPlayer"] = relationship(back_populates="bindings")


class CapabilityProfileAuditLog(Base):
    __tablename__ = "capability_profile_audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile_id: Mapped[int | None] = mapped_column(BigIntPK, ForeignKey("capability_profile.id", ondelete="SET NULL"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(48), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    actor: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)


class CapabilityProfileWebhookDelivery(Base):
    __tablename__ = "capability_profile_webhook_delivery"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    webhook_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("capability_profile_webhook.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(48), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DELIVERED")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    dead_lettered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
