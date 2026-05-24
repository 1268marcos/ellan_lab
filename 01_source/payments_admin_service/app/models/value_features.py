from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from app.core.database import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaymentIntegrationMilestone(Base):
    __tablename__ = "payment_integration_milestone"

    id = Column(String(36), primary_key=True)
    player_code = Column(String(64), nullable=False, index=True)
    phase = Column(String(30), nullable=False)
    title = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default="PLANNED")
    target_date = Column(Date, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    owner_team = Column(String(80), nullable=True)
    blockers_json = Column(JsonType, nullable=False, default=list)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PaymentSettlementCorridor(Base):
    __tablename__ = "payment_settlement_corridor"

    id = Column(String(36), primary_key=True)
    corridor_code = Column(String(64), nullable=False, unique=True, index=True)
    origin_country = Column(String(2), nullable=False)
    destination_country = Column(String(2), nullable=False)
    source_player_code = Column(String(64), nullable=False)
    settlement_player_code = Column(String(64), nullable=False)
    source_currency = Column(String(8), nullable=False)
    settlement_currency = Column(String(8), nullable=False)
    fx_provider_code = Column(String(64), nullable=True)
    fee_basis_points = Column(Integer, nullable=False, default=0)
    settlement_delay_days = Column(Integer, nullable=False, default=2)
    is_active = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PaymentPlayerCompliance(Base):
    __tablename__ = "payment_player_compliance"

    id = Column(String(36), primary_key=True)
    player_code = Column(String(64), nullable=False, index=True)
    country_code = Column(String(2), nullable=False, index=True)
    regulatory_framework = Column(String(40), nullable=False)
    kyc_level = Column(String(20), nullable=False, default="STANDARD")
    pci_scope = Column(String(20), nullable=False, default="SAQ_A")
    gdpr_ready = Column(Boolean, nullable=False, default=False)
    local_license_ref = Column(String(120), nullable=True)
    audit_status = Column(String(20), nullable=False, default="PENDING")
    last_audit_at = Column(Date, nullable=True)
    risk_tier = Column(String(10), nullable=False, default="MEDIUM")
    notes = Column(Text, nullable=True)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PaymentRoutingRule(Base):
    __tablename__ = "payment_routing_rule"

    id = Column(String(36), primary_key=True)
    rule_code = Column(String(64), nullable=False, unique=True, index=True)
    tenant_id = Column(String(36), nullable=True)
    country_code = Column(String(2), nullable=False)
    payment_method = Column(String(40), nullable=False)
    sales_channel = Column(String(50), nullable=True)
    primary_player_code = Column(String(64), nullable=False)
    fallback_player_code = Column(String(64), nullable=True)
    priority = Column(Integer, nullable=False, default=100)
    min_amount_cents = Column(Integer, nullable=True)
    max_amount_cents = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    rationale = Column(Text, nullable=True)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PaymentIntegrationIncident(Base):
    __tablename__ = "payment_integration_incident"

    id = Column(String(36), primary_key=True)
    player_code = Column(String(64), nullable=False, index=True)
    severity = Column(String(10), nullable=False)
    incident_type = Column(String(40), nullable=False)
    title = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default="OPEN")
    started_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    impact_pct = Column(Numeric(5, 2), nullable=True)
    affected_orders_estimate = Column(Integer, nullable=True)
    root_cause = Column(Text, nullable=True)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
