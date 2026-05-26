from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.types import BigIntPK, JsonType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CapabilityIntegrationMode(Base):
    __tablename__ = "capability_integration_mode"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CapabilityPlayerIntegration(Base):
    __tablename__ = "capability_player_integration"
    __table_args__ = (
        UniqueConstraint("player_id", "integration_mode_code", "direction", name="uq_capability_player_integration"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("capability_ecosystem_player.id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_code: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    integration_mode_code: Mapped[str] = mapped_column(
        String(40), ForeignKey("capability_integration_mode.code"), nullable=False
    )
    direction: Mapped[str] = mapped_column(String(10), nullable=False, default="OUTBOUND")
    auth_type: Mapped[str] = mapped_column(String(32), nullable=False, default="API_KEY")
    base_url_template: Mapped[str | None] = mapped_column(String(500), nullable=True)
    webhook_supported: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sandbox_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    production_ready: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)

    player: Mapped["CapabilityEcosystemPlayer"] = relationship(back_populates="integrations")


class CapabilityPlayerLockerPresence(Base):
    __tablename__ = "capability_player_locker_presence"
    __table_args__ = (
        UniqueConstraint("player_id", "program_code", name="uq_capability_player_locker_presence"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("capability_ecosystem_player.id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_code: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    locker_role: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    program_code: Mapped[str] = mapped_column(String(48), nullable=False)
    program_name: Mapped[str] = mapped_column(String(160), nullable=False)
    region_scope: Mapped[str] = mapped_column(String(80), nullable=False, default="GLOBAL")
    supports_inbound: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    supports_outbound: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    supports_returns: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)

    player: Mapped["CapabilityEcosystemPlayer"] = relationship(back_populates="locker_presences")


class CapabilityPlayerRelation(Base):  # noqa: D101
    __tablename__ = "capability_player_relation"
    __table_args__ = (
        UniqueConstraint("from_player_id", "to_player_id", "relation_type", name="uq_capability_player_relation"),
    )

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    from_player_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("capability_ecosystem_player.id", ondelete="CASCADE"), nullable=False
    )
    to_player_id: Mapped[int] = mapped_column(
        BigIntPK, ForeignKey("capability_ecosystem_player.id", ondelete="CASCADE"), nullable=False
    )
    from_player_code: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    to_player_code: Mapped[str] = mapped_column(String(48), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict, server_default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utcnow)
