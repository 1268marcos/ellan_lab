from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from app.core.database import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaymentEcosystemSegment(Base):
    __tablename__ = "payment_ecosystem_segment"

    code = Column(String(40), primary_key=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=100)
    default_protocol = Column(String(20), nullable=False, default="REST")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PaymentEcosystemPlayer(Base):
    __tablename__ = "payment_ecosystem_player"

    id = Column(String(36), primary_key=True)
    code = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(160), nullable=False)
    segment = Column(String(40), nullable=False)
    countries_json = Column(JsonType, nullable=False, default=list)
    parent_player_code = Column(String(64), nullable=True)
    integration_status = Column(String(20), nullable=False, default="SANDBOX")
    metadata_json = Column(JsonType, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PaymentOrderContext(Base):
    __tablename__ = "payment_order_context"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, unique=True, index=True)
    tenant_id = Column(String(36), nullable=True, index=True)
    primary_transaction_id = Column(String(36), nullable=True)
    locker_id = Column(String(120), nullable=True, index=True)
    region_code = Column(String(20), nullable=True)
    sales_channel = Column(String(50), nullable=True)
    marketplace_partner_id = Column(String(36), nullable=True)
    carrier_partner_id = Column(String(36), nullable=True)
    locker_network_code = Column(String(64), nullable=True)
    status = Column(String(30), nullable=False, default="OPEN")
    total_amount_cents = Column(Integer, nullable=False, default=0)
    currency = Column(String(8), nullable=False, default="BRL")
    metadata_json = Column(JsonType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PaymentContextPlayerLink(Base):
    __tablename__ = "payment_context_player_link"

    id = Column(String(36), primary_key=True)
    order_context_id = Column(String(36), nullable=False, index=True)
    player_code = Column(String(64), nullable=False)
    role = Column(String(40), nullable=False)
    amount_cents = Column(Integer, nullable=True)
    share_pct = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PaymentReconciliationBatch(Base):
    __tablename__ = "payment_reconciliation_batch"

    id = Column(String(36), primary_key=True)
    batch_code = Column(String(64), nullable=False, unique=True, index=True)
    region_code = Column(String(20), nullable=True)
    gateway = Column(String(50), nullable=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="OPEN")
    expected_count = Column(Integer, nullable=False, default=0)
    matched_count = Column(Integer, nullable=False, default=0)
    mismatch_count = Column(Integer, nullable=False, default=0)
    total_amount_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(8), nullable=False, default="BRL")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    closed_at = Column(DateTime(timezone=True), nullable=True)


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(String(36), primary_key=True)
    endpoint_id = Column(String(36), nullable=False, index=True)
    event_name = Column(String(100), nullable=False)
    aggregate_type = Column(String(50), nullable=True)
    aggregate_id = Column(String(36), nullable=True)
    payload_json = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    last_status_code = Column(Integer, nullable=True)
    last_response_body = Column(Text, nullable=True)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    next_attempt_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerPaymentHold(Base):
    __tablename__ = "partner_payment_holds"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    invoice_id = Column(String(36), nullable=False)
    order_id = Column(String(64), nullable=True)
    hold_amount_cents = Column(BigInteger, nullable=False)
    release_schedule = Column(String(30), nullable=False, default="AFTER_15_DAYS")
    released_at = Column(DateTime(timezone=True), nullable=True)
    released_amount_cents = Column(BigInteger, nullable=True)
    dispute_opened_at = Column(DateTime(timezone=True), nullable=True)
    dispute_resolved_at = Column(DateTime(timezone=True), nullable=True)
    dispute_result = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, default="HELD")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PaymentPlayerCountryCoverage(Base):
    __tablename__ = "payment_player_country_coverage"

    id = Column(String(36), primary_key=True)
    player_code = Column(String(64), nullable=False, index=True)
    country_code = Column(String(2), nullable=False, index=True)
    coverage_role = Column(String(40), nullable=False)
    is_primary_market = Column(Boolean, nullable=False, default=False)
    locker_density = Column(String(20), nullable=False, default="MEDIUM")
    metadata_json = Column(JsonType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PaymentPlayerIntegration(Base):
    __tablename__ = "payment_player_integration"

    id = Column(String(36), primary_key=True)
    player_code = Column(String(64), nullable=False, unique=True, index=True)
    integration_protocol = Column(String(20), nullable=False, default="REST")
    api_base_url = Column(String(500), nullable=True)
    webhook_inbound_path = Column(String(255), nullable=True)
    sandbox_ready = Column(Boolean, nullable=False, default=False)
    production_ready = Column(Boolean, nullable=False, default=False)
    payment_capture_mode = Column(String(30), nullable=False, default="CAPTURE_NOW")
    split_settlement_supported = Column(Boolean, nullable=False, default=False)
    cross_border_supported = Column(Boolean, nullable=False, default=False)
    readiness_score = Column(Integer, nullable=False, default=0)
    linked_domains_json = Column(JsonType, nullable=False, default=list)
    integration_notes = Column(Text, nullable=True)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PaymentPlayerRelation(Base):
    __tablename__ = "payment_player_relation"

    id = Column(String(36), primary_key=True)
    from_player_code = Column(String(64), nullable=False, index=True)
    to_player_code = Column(String(64), nullable=False, index=True)
    relation_type = Column(String(32), nullable=False)
    notes = Column(Text, nullable=True)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SavedPaymentMethod(Base):
    __tablename__ = "saved_payment_methods"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    method_code = Column(String(80), nullable=False)
    gateway_token = Column(String(255), nullable=False)
    last4 = Column(String(4), nullable=True)
    card_brand = Column(String(50), nullable=True)
    cardholder_name = Column(String(255), nullable=True)
    expiry_month = Column(Integer, nullable=True)
    expiry_year = Column(Integer, nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
