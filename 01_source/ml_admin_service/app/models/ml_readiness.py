from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MlIntegrationReadinessSnapshot(Base):
    __tablename__ = "ml_integration_readiness_snapshots"

    id = Column(String(36), primary_key=True)
    network_player_id = Column(
        String(36), ForeignKey("ml_locker_network_players.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    network_player_code = Column(String(48), nullable=False, index=True)
    marketplace_channel_id = Column(String(36), nullable=True)
    score_total = Column(Numeric(5, 2), nullable=False, default=0)
    score_capabilities = Column(Numeric(5, 2), nullable=False, default=0)
    score_telemetry = Column(Numeric(5, 2), nullable=False, default=0)
    score_ml_ops = Column(Numeric(5, 2), nullable=False, default=0)
    readiness_band = Column(String(16), nullable=False, default="PLANNED")
    blockers_json = Column(Text, nullable=False, default="[]")
    factors_json = Column(Text, nullable=False, default="{}")
    computed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MlOpsAuditLog(Base):
    __tablename__ = "ml_ops_audit_log"

    id = Column(String(36), primary_key=True)
    event_type = Column(String(40), nullable=False)
    entity_type = Column(String(32), nullable=False)
    entity_id = Column(String(48), nullable=True)
    summary = Column(String(255), nullable=False)
    payload_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
