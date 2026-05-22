from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MarketplacePlayerCertification(Base):
    __tablename__ = "marketplace_player_certifications"
    __table_args__ = (
        UniqueConstraint("channel_partner_id", "certification_type", name="uq_mkt_player_cert"),
    )

    id = Column(String(36), primary_key=True)
    channel_partner_id = Column(
        String(36), ForeignKey("marketplace_channel_partners.id", ondelete="CASCADE"), nullable=False, index=True
    )
    partner_code = Column(String(48), nullable=False, index=True)
    certification_type = Column(String(40), nullable=False)
    status = Column(String(20), nullable=False, default="VALID")
    source = Column(String(32), nullable=False, default="SEED")
    partner_certification_id = Column(String(36), nullable=True, index=True)
    issuer = Column(String(120), nullable=True)
    issued_at = Column(Date, nullable=True)
    expires_at = Column(Date, nullable=True)
    evidence_url = Column(String(500), nullable=True)
    scope_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class MarketplaceGlobalCorridor(Base):
    __tablename__ = "marketplace_global_corridors"

    id = Column(String(36), primary_key=True)
    corridor_code = Column(String(48), nullable=False, unique=True)
    name = Column(String(160), nullable=False)
    origin_country = Column(String(2), nullable=False)
    dest_country = Column(String(2), nullable=False)
    primary_channel_partner_id = Column(String(36), ForeignKey("marketplace_channel_partners.id"), nullable=False)
    primary_partner_code = Column(String(48), nullable=False)
    fallback_channel_partner_id = Column(String(36), ForeignKey("marketplace_channel_partners.id"), nullable=True)
    fallback_partner_code = Column(String(48), nullable=True)
    handoff_type = Column(String(32), nullable=False, default="LOCKER_TO_LOCKER")
    service_level = Column(String(20), nullable=False, default="STANDARD")
    transit_days_min = Column(Integer, nullable=False, default=1)
    transit_days_max = Column(Integer, nullable=False, default=5)
    supports_returns = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=100)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class MarketplaceCorridorSla(Base):
    __tablename__ = "marketplace_corridor_sla"

    id = Column(String(36), primary_key=True)
    corridor_id = Column(
        String(36), ForeignKey("marketplace_global_corridors.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    corridor_code = Column(String(48), nullable=False, index=True)
    uptime_target_pct = Column(Numeric(5, 2), nullable=False, default=99.50)
    on_time_delivery_pct = Column(Numeric(5, 2), nullable=False, default=95.00)
    max_transit_hours = Column(Integer, nullable=False, default=72)
    webhook_p95_latency_ms = Column(Integer, nullable=False, default=2000)
    compliance_status = Column(String(20), nullable=False, default="COMPLIANT")
    breach_count = Column(Integer, nullable=False, default=0)
    last_breach_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    measured_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MarketplaceCorridorPlayerStep(Base):
    __tablename__ = "marketplace_corridor_player_steps"
    __table_args__ = (UniqueConstraint("corridor_id", "step_order", name="uq_mkt_corridor_step"),)

    id = Column(String(36), primary_key=True)
    corridor_id = Column(String(36), ForeignKey("marketplace_global_corridors.id", ondelete="CASCADE"), nullable=False)
    step_order = Column(Integer, nullable=False, default=1)
    channel_partner_id = Column(String(36), ForeignKey("marketplace_channel_partners.id"), nullable=False)
    partner_code = Column(String(48), nullable=False)
    step_role = Column(String(32), nullable=False, default="HANDOFF")
    notes = Column(Text, nullable=True)
