from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Index, Integer, Numeric, String, Text
from sqlalchemy.types import JSON

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PartnerWebhookDelivery(Base):
    __tablename__ = "partner_webhook_deliveries"
    __table_args__ = (Index("idx_pwd_endpoint_status", "endpoint_id", "status"),)

    id = Column(String(36), primary_key=True)
    endpoint_id = Column(String(36), nullable=False, index=True)
    event_id = Column(String(36), nullable=False)
    event_type = Column(String(80), nullable=False)
    payload_json = Column(Text, nullable=False, default="{}")
    payload_hash = Column(String(64), nullable=True)
    http_status = Column(Integer, nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="PENDING")
    last_error = Column(Text, nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerIntegrationHealth(Base):
    __tablename__ = "partner_integration_health"
    __table_args__ = (Index("idx_pih_partner_time", "partner_id", "checked_at"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    endpoint_url = Column(String(500), nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    status = Column(String(20), nullable=False)
    latency_ms = Column(Integer, nullable=True)
    http_status = Column(Integer, nullable=True)
    error_message = Column(String(500), nullable=True)


class PartnerOrderEventOutbox(Base):
    __tablename__ = "partner_order_events_outbox"
    __table_args__ = (Index("idx_poeo_partner_status", "partner_id", "status"),)

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    order_id = Column(String(36), nullable=False)
    event_type = Column(String(50), nullable=False)
    payload_json = Column(JSON, nullable=False, default=dict)
    api_version = Column(String(10), nullable=False, default="v1")
    status = Column(String(20), nullable=False, default="PENDING")
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerB2bInvoice(Base):
    __tablename__ = "partner_b2b_invoices"
    __table_args__ = (Index("idx_pbi_partner_status", "partner_id", "status"),)

    id = Column(String(36), primary_key=True)
    cycle_id = Column(String(36), nullable=False, index=True)
    partner_id = Column(String(36), nullable=False, index=True)
    invoice_number = Column(String(50), nullable=True)
    document_type = Column(String(30), nullable=False, default="INVOICE")
    amount_cents = Column(BigInteger, nullable=False)
    tax_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(8), nullable=False, default="BRL")
    country_code = Column(String(2), nullable=True)
    due_date = Column(Date, nullable=True)
    taker_name = Column(String(140), nullable=True)
    taker_email = Column(String(128), nullable=True)
    status = Column(String(20), nullable=False, default="DRAFT")
    issued_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerBillingLineItem(Base):
    __tablename__ = "partner_billing_line_items"
    __table_args__ = (Index("idx_pbli_cycle", "cycle_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    cycle_id = Column(String(36), nullable=False, index=True)
    partner_id = Column(String(36), nullable=False, index=True)
    locker_id = Column(String(36), nullable=True)
    line_type = Column(String(40), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(12, 4), nullable=False, default=1)
    unit_price_cents = Column(BigInteger, nullable=False)
    total_cents = Column(BigInteger, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerCreditNote(Base):
    __tablename__ = "partner_credit_notes"
    __table_args__ = (Index("idx_pcn_partner_status", "partner_id", "status"),)

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    original_invoice_id = Column(String(36), nullable=True)
    cycle_id = Column(String(36), nullable=True)
    reason_code = Column(String(40), nullable=False)
    description = Column(Text, nullable=False)
    amount_cents = Column(BigInteger, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    status = Column(String(20), nullable=False, default="PENDING")
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerPaymentHold(Base):
    __tablename__ = "partner_payment_holds"
    __table_args__ = (Index("idx_pph_partner_status", "partner_id", "status"),)

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    invoice_id = Column(String(36), nullable=False)
    hold_amount_cents = Column(BigInteger, nullable=False)
    release_schedule = Column(String(30), nullable=False, default="AFTER_15_DAYS")
    released_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="HELD")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerCommissionStructure(Base):
    __tablename__ = "partner_commission_structure"
    __table_args__ = (Index("idx_pcs_partner", "partner_id"),)

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String(36), nullable=False, index=True)
    commission_percentage = Column(Numeric(5, 2), nullable=True)
    revenue_threshold_cents = Column(BigInteger, nullable=True)
    effective_from = Column(Date, nullable=True)


class PartnerOnboardingMilestone(Base):
    """Checklist de onboarding B2B (KYC → sandbox → go-live)."""

    __tablename__ = "partner_onboarding_milestones"
    __table_args__ = (Index("idx_pom_partner_code", "partner_id", "milestone_code"),)

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    milestone_code = Column(String(40), nullable=False)
    milestone_label = Column(String(128), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    sort_order = Column(Integer, nullable=False, default=100)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(String(36), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
