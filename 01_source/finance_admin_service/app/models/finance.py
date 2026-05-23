from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FinancePartnerAccount(Base):
    __tablename__ = "finance_partner_accounts"

    id = Column(String(36), primary_key=True)
    code = Column(String(48), nullable=False, unique=True, index=True)
    name = Column(String(160), nullable=False)
    partner_type = Column(String(20), nullable=False)
    country_code = Column(String(2), nullable=True)
    tax_id = Column(String(32), nullable=True)
    currency = Column(String(8), nullable=False, default="BRL")
    active = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PartnerBillingPlan(Base):
    __tablename__ = "partner_billing_plans"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    plan_name = Column(String(128), nullable=False)
    billing_model = Column(String(30), nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    country_code = Column(String(2), nullable=True)
    monthly_fee_cents = Column(BigInteger, nullable=True)
    fee_per_delivery_cents = Column(BigInteger, nullable=True)
    fee_per_pickup_cents = Column(BigInteger, nullable=True)
    fee_per_day_stored_cents = Column(BigInteger, nullable=True)
    revenue_share_pct = Column(Numeric(6, 4), nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PartnerBillingCycle(Base):
    __tablename__ = "partner_billing_cycles"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    locker_id = Column(String(36), nullable=True)
    partner_type = Column(String(20), nullable=False)
    billing_plan_id = Column(String(36), nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    total_amount_cents = Column(BigInteger, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="OPEN")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PartnerB2bInvoice(Base):
    __tablename__ = "partner_b2b_invoices"

    id = Column(String(36), primary_key=True)
    cycle_id = Column(String(36), nullable=False, index=True)
    partner_id = Column(String(36), nullable=False, index=True)
    invoice_number = Column(String(50), nullable=True)
    document_type = Column(String(30), nullable=False, default="INVOICE")
    amount_cents = Column(BigInteger, nullable=False)
    tax_cents = Column(BigInteger, nullable=False, default=0)
    currency = Column(String(8), nullable=False, default="BRL")
    status = Column(String(20), nullable=False, default="DRAFT")
    fiscal_status = Column(String(20), nullable=False, default="PENDING")
    fiscal_access_key = Column(String(80), nullable=True)
    fiscal_pdf_url = Column(String(500), nullable=True)
    due_date = Column(Date, nullable=True)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PartnerApiKey(Base):
    __tablename__ = "partner_api_keys"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    key_prefix = Column(String(16), nullable=False)
    key_hash = Column(String(128), nullable=False)
    label = Column(String(64), nullable=True)
    scopes_json = Column(Text, nullable=False, default='["billing:read"]')
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerWebhookEndpoint(Base):
    __tablename__ = "partner_webhook_endpoints"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    url = Column(String(500), nullable=False)
    secret_hash = Column(String(128), nullable=False)
    secret_key = Column(String(256), nullable=True)
    events_json = Column(Text, nullable=False, default='["billing.*"]')
    api_version = Column(String(10), nullable=False, default="v1")
    retry_policy = Column(Text, nullable=False, default="{}")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class WalletProviderCatalog(Base):
    __tablename__ = "wallet_provider_catalog"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(80), nullable=False, unique=True)
    name = Column(String(120), nullable=False)
    metadata_json = Column(Text, nullable=False, default="{}")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(String(36), primary_key=True)
    wallet_id = Column(String(36), nullable=False, index=True)
    order_id = Column(String, nullable=True)
    type = Column(String(30), nullable=False)
    amount_cents = Column(BigInteger, nullable=False)
    balance_after_cents = Column(BigInteger, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    external_reference = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class FinanceOpsInvoice(Base):
    __tablename__ = "finance_ops_invoices"

    id = Column(String(50), primary_key=True)
    order_id = Column(String(100), nullable=False, index=True)
    country = Column(String(5), nullable=False)
    invoice_type = Column(String(20), nullable=False)
    status = Column(String(30), nullable=False)
    amount_cents = Column(BigInteger, nullable=True)
    currency = Column(String(10), nullable=True)
    locker_id = Column(String(64), nullable=True)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class BillingProcessedEvent(Base):
    __tablename__ = "billing_processed_events"

    id = Column(String(36), primary_key=True)
    event_id = Column(String(128), nullable=False, unique=True, index=True)
    order_id = Column(String(100), nullable=True, index=True)
    event_type = Column(String(64), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    payload_json = Column(Text, nullable=False, default="{}")
