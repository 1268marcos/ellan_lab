from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MarketplaceIntegrationReadiness(Base):
    __tablename__ = "marketplace_integration_readiness"

    channel_partner_id = Column(String(36), primary_key=True)
    partner_code = Column(String(48), nullable=False, index=True)
    score_total = Column(Numeric(5, 2), nullable=False, default=0)
    score_capabilities = Column(Numeric(5, 2), nullable=False, default=0)
    score_api = Column(Numeric(5, 2), nullable=False, default=0)
    score_operations = Column(Numeric(5, 2), nullable=False, default=0)
    readiness_band = Column(String(16), nullable=False, default="PLANNED")
    blockers_json = Column(Text, nullable=False, default="[]")
    ml_network_code = Column(String(48), nullable=True)
    computed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MarketplaceIntegrationIncident(Base):
    __tablename__ = "marketplace_integration_incidents"

    id = Column(String(36), primary_key=True)
    channel_partner_id = Column(String(36), nullable=False, index=True)
    partner_code = Column(String(48), nullable=False)
    severity = Column(String(16), nullable=False, default="WARNING")
    incident_type = Column(String(32), nullable=False, default="API_DEGRADED")
    title = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default="OPEN")
    details_json = Column(Text, nullable=False, default="{}")
    opened_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class MarketplaceSyncAuditLog(Base):
    __tablename__ = "marketplace_sync_audit_log"

    id = Column(String(36), primary_key=True)
    event_type = Column(String(40), nullable=False)
    entity_type = Column(String(32), nullable=False)
    entity_id = Column(String(48), nullable=True)
    actor_id = Column(String(64), nullable=True)
    summary = Column(String(255), nullable=False)
    payload_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
