from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PartnerPaymentTerms(Base):
    __tablename__ = "partner_payment_terms"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    net_days = Column(Integer, nullable=False, default=30)
    grace_days = Column(Integer, nullable=False, default=0)
    early_payment_discount_pct = Column(Numeric(6, 4), nullable=True)
    currency = Column(String(8), nullable=False, default="BRL")
    is_default = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class FinanceFxRate(Base):
    __tablename__ = "finance_fx_rates"

    id = Column(String(36), primary_key=True)
    base_currency = Column(String(8), nullable=False)
    quote_currency = Column(String(8), nullable=False)
    rate_date = Column(Date, nullable=False)
    rate = Column(Numeric(18, 8), nullable=False)
    source = Column(String(40), nullable=False, default="MANUAL")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerCommercialTier(Base):
    __tablename__ = "partner_commercial_tiers"

    tier_code = Column(String(24), primary_key=True)
    name = Column(String(80), nullable=False)
    min_monthly_orders = Column(Integer, nullable=False, default=0)
    min_gmv_cents = Column(BigInteger, nullable=False, default=0)
    default_revenue_share_pct = Column(Numeric(6, 4), nullable=True)
    sort_order = Column(Integer, nullable=False, default=100)


class PartnerTierAssignment(Base):
    __tablename__ = "partner_tier_assignments"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    tier_code = Column(String(24), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date, nullable=True)
    assigned_by = Column(String(80), nullable=False, default="system")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerDunningPolicy(Base):
    __tablename__ = "partner_dunning_policies"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=True, index=True)
    stage = Column(Integer, nullable=False)
    days_overdue = Column(Integer, nullable=False)
    action = Column(String(40), nullable=False)
    notify_channel = Column(String(20), nullable=False, default="EMAIL")
    active = Column(Boolean, nullable=False, default=True)


class PartnerDunningCase(Base):
    __tablename__ = "partner_dunning_cases"

    id = Column(String(36), primary_key=True)
    invoice_id = Column(String(36), nullable=False, index=True)
    partner_id = Column(String(36), nullable=False, index=True)
    stage = Column(Integer, nullable=False, default=1)
    amount_due_cents = Column(BigInteger, nullable=False)
    status = Column(String(20), nullable=False, default="OPEN")
    next_action_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SettlementReconciliationRun(Base):
    __tablename__ = "settlement_reconciliation_runs"

    id = Column(String(36), primary_key=True)
    batch_id = Column(String(36), nullable=False, index=True)
    run_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    status = Column(String(20), nullable=False, default="COMPLETED")
    matched_count = Column(Integer, nullable=False, default=0)
    unmatched_count = Column(Integer, nullable=False, default=0)
    variance_cents = Column(BigInteger, nullable=False, default=0)


class SettlementReconciliationMatch(Base):
    __tablename__ = "settlement_reconciliation_matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(36), nullable=False, index=True)
    settlement_item_id = Column(Integer, nullable=True)
    order_id = Column(String(36), nullable=False)
    wallet_tx_id = Column(String(36), nullable=True)
    match_status = Column(String(20), nullable=False)
    variance_cents = Column(BigInteger, nullable=False, default=0)


class PartnerTaxCorridor(Base):
    __tablename__ = "partner_tax_corridors"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    origin_country = Column(String(2), nullable=False)
    destination_country = Column(String(2), nullable=False)
    document_type = Column(String(30), nullable=False, default="NF_B2B")
    tax_regime = Column(String(40), nullable=False)
    withholding_pct = Column(Numeric(6, 4), nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerInvoiceDocument(Base):
    __tablename__ = "partner_invoice_documents"

    id = Column(String(36), primary_key=True)
    invoice_id = Column(String(36), nullable=False, index=True)
    document_kind = Column(String(20), nullable=False)
    storage_uri = Column(String(500), nullable=True)
    access_key = Column(String(80), nullable=True)
    fiscal_invoice_id = Column(String(60), nullable=True)
    country = Column(String(2), nullable=False)
    invoice_type = Column(String(30), nullable=False, default="B2B")
    issued_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class FinanceAuditLog(Base):
    __tablename__ = "finance_audit_log"

    id = Column(String(36), primary_key=True)
    actor_id = Column(String(80), nullable=False, default="system")
    action = Column(String(60), nullable=False)
    entity_type = Column(String(40), nullable=False)
    entity_id = Column(String(60), nullable=False, index=True)
    before_json = Column(Text, nullable=False, default="{}")
    after_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
