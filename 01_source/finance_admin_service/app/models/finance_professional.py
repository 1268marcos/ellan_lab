from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PartnerCommercialContract(Base):
    __tablename__ = "partner_commercial_contracts"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    catalog_code = Column(String(48), nullable=True, index=True)
    contract_type = Column(String(40), nullable=False)
    title = Column(String(200), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date, nullable=True)
    currency = Column(String(8), nullable=False, default="BRL")
    status = Column(String(20), nullable=False, default="ACTIVE")
    billing_plan_id = Column(String(36), nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class FinanceIntegrationMilestone(Base):
    __tablename__ = "finance_integration_milestones"

    id = Column(String(36), primary_key=True)
    catalog_code = Column(String(48), nullable=False, index=True)
    phase = Column(String(40), nullable=False)
    title = Column(String(160), nullable=False)
    target_date = Column(Date, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")
    owner = Column(String(80), nullable=True)
    blocker_notes = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=100)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class FinancePartnerReadiness(Base):
    __tablename__ = "finance_partner_readiness"

    catalog_code = Column(String(48), primary_key=True)
    readiness_score = Column(Integer, nullable=False, default=0)
    integration_score = Column(Integer, nullable=False, default=0)
    billing_score = Column(Integer, nullable=False, default=0)
    compliance_score = Column(Integer, nullable=False, default=0)
    grade = Column(String(4), nullable=False, default="D")
    blockers_json = Column(Text, nullable=False, default="[]")
    computed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerSlaDefinition(Base):
    __tablename__ = "partner_sla_definitions"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    catalog_code = Column(String(48), nullable=True)
    metric_code = Column(String(60), nullable=False)
    metric_name = Column(String(120), nullable=False)
    target_value = Column(Numeric(12, 4), nullable=False)
    target_unit = Column(String(20), nullable=False)
    window_days = Column(Integer, nullable=False, default=30)
    penalty_credit_pct = Column(Numeric(6, 4), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerSlaBreach(Base):
    __tablename__ = "partner_sla_breaches"

    id = Column(String(36), primary_key=True)
    sla_id = Column(String(36), nullable=False, index=True)
    partner_id = Column(String(36), nullable=False, index=True)
    observed_value = Column(Numeric(12, 4), nullable=False)
    breach_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, default="OPEN")
    credit_note_id = Column(String(36), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
