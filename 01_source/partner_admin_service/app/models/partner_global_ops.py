from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PartnerPlayerCertification(Base):
    __tablename__ = "partner_player_certifications"
    __table_args__ = (
        UniqueConstraint("ecosystem_player_id", "certification_type", name="uq_partner_player_cert"),
    )

    id = Column(String(36), primary_key=True)
    ecosystem_player_id = Column(
        String(36), ForeignKey("partner_ecosystem_players.id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_code = Column(String(48), nullable=False, index=True)
    certification_type = Column(String(40), nullable=False)
    status = Column(String(20), nullable=False, default="VALID")
    source = Column(String(32), nullable=False, default="SEED")
    marketplace_certification_id = Column(String(36), nullable=True, index=True)
    issuer = Column(String(120), nullable=True)
    issued_at = Column(Date, nullable=True)
    expires_at = Column(Date, nullable=True)
    evidence_url = Column(String(500), nullable=True)
    scope_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PartnerGlobalCorridor(Base):
    __tablename__ = "partner_global_corridors"

    id = Column(String(36), primary_key=True)
    corridor_code = Column(String(48), nullable=False, unique=True)
    name = Column(String(160), nullable=False)
    origin_country = Column(String(2), nullable=False)
    dest_country = Column(String(2), nullable=False)
    primary_player_id = Column(String(36), ForeignKey("partner_ecosystem_players.id"), nullable=False)
    primary_player_code = Column(String(48), nullable=False)
    fallback_player_id = Column(String(36), ForeignKey("partner_ecosystem_players.id"), nullable=True)
    fallback_player_code = Column(String(48), nullable=True)
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


class PartnerEcosystemReadiness(Base):
    __tablename__ = "partner_ecosystem_readiness"

    ecosystem_player_id = Column(
        String(36), ForeignKey("partner_ecosystem_players.id", ondelete="CASCADE"), primary_key=True
    )
    player_code = Column(String(48), nullable=False, unique=True)
    score_total = Column(Numeric(5, 2), nullable=False, default=0)
    score_certifications = Column(Numeric(5, 2), nullable=False, default=0)
    score_capabilities = Column(Numeric(5, 2), nullable=False, default=0)
    score_corridors = Column(Numeric(5, 2), nullable=False, default=0)
    score_webhooks = Column(Numeric(5, 2), nullable=False, default=0)
    readiness_band = Column(String(16), nullable=False, default="PLANNED")
    blockers_json = Column(Text, nullable=False, default="[]")
    computed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerCorridorSla(Base):
    __tablename__ = "partner_corridor_sla"

    id = Column(String(36), primary_key=True)
    corridor_id = Column(
        String(36), ForeignKey("partner_global_corridors.id", ondelete="CASCADE"), nullable=False, unique=True
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


class PartnerRelationHealth(Base):
    __tablename__ = "partner_relation_health"

    id = Column(String(36), primary_key=True)
    relation_id = Column(
        String(36), ForeignKey("partner_player_relations.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    from_player_code = Column(String(48), nullable=False)
    to_player_code = Column(String(48), nullable=False)
    relation_type = Column(String(32), nullable=False)
    health_status = Column(String(20), nullable=False, default="HEALTHY")
    cascade_from_player_code = Column(String(48), nullable=True)
    last_check_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    details_json = Column(Text, nullable=False, default="{}")
