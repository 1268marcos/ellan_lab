from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PartnerBillingLineItem(Base):
    __tablename__ = "partner_billing_line_items"

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


class PartnerSettlementBatch(Base):
    __tablename__ = "partner_settlement_batches"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False, default="ECOMMERCE")
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    total_orders = Column(Integer, nullable=False, default=0)
    gross_revenue_cents = Column(BigInteger, nullable=False, default=0)
    revenue_share_pct = Column(Numeric(6, 4), nullable=False)
    revenue_share_cents = Column(BigInteger, nullable=False, default=0)
    fees_cents = Column(BigInteger, nullable=False, default=0)
    net_amount_cents = Column(BigInteger, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="DRAFT")
    settled_at = Column(DateTime(timezone=True), nullable=True)
    settlement_ref = Column(String(128), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PartnerSettlementItem(Base):
    __tablename__ = "partner_settlement_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(36), nullable=False, index=True)
    order_id = Column(String(36), nullable=False)
    order_date = Column(DateTime(timezone=True), nullable=False)
    gross_cents = Column(BigInteger, nullable=False)
    share_pct = Column(Numeric(6, 4), nullable=False)
    share_cents = Column(BigInteger, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")


class PartnerCreditNote(Base):
    __tablename__ = "partner_credit_notes"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    original_invoice_id = Column(String(36), nullable=True)
    cycle_id = Column(String(36), nullable=True)
    reason_code = Column(String(40), nullable=False)
    description = Column(Text, nullable=False)
    amount_cents = Column(BigInteger, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    status = Column(String(20), nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PartnerPaymentHold(Base):
    __tablename__ = "partner_payment_holds"

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

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    commission_percentage = Column(Numeric(5, 2), nullable=False)
    revenue_threshold_cents = Column(BigInteger, nullable=True)
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class CostCenter(Base):
    __tablename__ = "cost_centers"

    id = Column(String(36), primary_key=True)
    locker_id = Column(String(120), nullable=False, unique=True, index=True)
    region_code = Column(String(20), nullable=True)
    network_code = Column(String(48), nullable=True)
    operational_cost_monthly_cents = Column(BigInteger, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class CostCenterMonthly(Base):
    __tablename__ = "cost_center_monthly"

    id = Column(String(36), primary_key=True)
    locker_id = Column(String(120), nullable=False, index=True)
    month = Column(Date, nullable=False)
    rent_cents = Column(BigInteger, nullable=False, default=0)
    maintenance_preventive_cents = Column(BigInteger, nullable=False, default=0)
    maintenance_corrective_cents = Column(BigInteger, nullable=False, default=0)
    connectivity_cents = Column(BigInteger, nullable=False, default=0)
    energy_cents = Column(BigInteger, nullable=False, default=0)
    insurance_cents = Column(BigInteger, nullable=False, default=0)
    payment_gateway_fee_cents = Column(BigInteger, nullable=False, default=0)
    depreciation_cents = Column(BigInteger, nullable=False, default=0)
    cleaning_cents = Column(BigInteger, nullable=False, default=0)
    security_cents = Column(BigInteger, nullable=False, default=0)
    marketing_cents = Column(BigInteger, nullable=False, default=0)
    other_cents = Column(BigInteger, nullable=False, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    @property
    def total_opex_cents(self) -> int:
        return int(
            (self.rent_cents or 0)
            + (self.maintenance_preventive_cents or 0)
            + (self.maintenance_corrective_cents or 0)
            + (self.connectivity_cents or 0)
            + (self.energy_cents or 0)
            + (self.insurance_cents or 0)
            + (self.payment_gateway_fee_cents or 0)
            + (self.cleaning_cents or 0)
            + (self.security_cents or 0)
            + (self.marketing_cents or 0)
            + (self.other_cents or 0)
        )

    @property
    def total_costs_cents(self) -> int:
        return self.total_opex_cents + int(self.depreciation_cents or 0)


class FiscalReconciliationGap(Base):
    __tablename__ = "fiscal_reconciliation_gaps"

    id = Column(String(60), primary_key=True)
    dedupe_key = Column(String(180), nullable=False, unique=True, index=True)
    gap_type = Column(String(80), nullable=False)
    severity = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    order_id = Column(String(100), nullable=True, index=True)
    invoice_id = Column(String(50), nullable=True)
    details_json = Column(Text, nullable=False, default="{}")
    first_detected_at = Column(DateTime(timezone=True), nullable=False)
    last_detected_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class PartnerWebhookDelivery(Base):
    __tablename__ = "partner_webhook_deliveries"

    id = Column(String(36), primary_key=True)
    endpoint_id = Column(String(36), nullable=False, index=True)
    event_id = Column(String(36), nullable=False)
    event_type = Column(String(80), nullable=False)
    payload_json = Column(Text, nullable=False, default="{}")
    http_status = Column(Integer, nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="PENDING")
    last_error = Column(Text, nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
