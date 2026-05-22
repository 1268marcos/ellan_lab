from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Index, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PartnerSettlementBatch(Base):
    __tablename__ = "partner_settlement_batches"
    __table_args__ = (Index("idx_psb_partner_period", "partner_id", "period_start", "period_end"),)

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
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerSettlementItem(Base):
    __tablename__ = "partner_settlement_items"
    __table_args__ = (Index("idx_psi_batch", "batch_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(36), nullable=False, index=True)
    order_id = Column(String(36), nullable=False)
    order_date = Column(DateTime(timezone=True), nullable=False)
    gross_cents = Column(BigInteger, nullable=False)
    share_pct = Column(Numeric(6, 4), nullable=False)
    share_cents = Column(BigInteger, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")


class PartnerServiceArea(Base):
    __tablename__ = "partner_service_areas"
    __table_args__ = (Index("idx_psa_partner_priority", "partner_id", "priority"),)

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False, default="ECOMMERCE")
    locker_id = Column(String(36), nullable=False)
    priority = Column(Integer, nullable=False, default=100)
    exclusive = Column(Boolean, nullable=False, default=False)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerPerformanceMetric(Base):
    __tablename__ = "partner_performance_metrics"
    __table_args__ = (Index("idx_ppm_partner_month", "partner_id", "period_month"),)

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    period_month = Column(String(7), nullable=False)
    total_orders = Column(Integer, nullable=False, default=0)
    on_time_pickup_pct = Column(Numeric(5, 2), nullable=True)
    return_rate_pct = Column(Numeric(5, 2), nullable=True)
    avg_pickup_hours = Column(Numeric(6, 2), nullable=True)
    sla_compliance_pct = Column(Numeric(5, 2), nullable=True)
    webhook_success_rate = Column(Numeric(5, 2), nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerBillingPlan(Base):
    __tablename__ = "partner_billing_plans"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    plan_name = Column(String(128), nullable=False)
    billing_model = Column(String(30), nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    monthly_fee_cents = Column(BigInteger, nullable=True)
    fee_per_delivery_cents = Column(BigInteger, nullable=True)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerBillingCycle(Base):
    __tablename__ = "partner_billing_cycles"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    billing_plan_id = Column(String(36), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    total_amount_cents = Column(BigInteger, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="OPEN")
    currency = Column(String(8), nullable=False, default="BRL")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerStore(Base):
    __tablename__ = "partner_stores"

    id = Column(String(36), primary_key=True)
    name = Column(String(128), nullable=False)
    legal_name = Column(String(140), nullable=True)
    tax_id = Column(String(32), nullable=True)
    address_line = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    postal_code = Column(String(20), nullable=False)
    phone = Column(String(32), nullable=True)
    email = Column(String(128), nullable=True)
    commission_pct = Column(Numeric(5, 2), nullable=True, default=5.0)
    active = Column(Boolean, nullable=True, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerSlaAgreement(Base):
    __tablename__ = "partner_sla_agreements"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    country = Column(String(2), nullable=False, default="BR")
    sla_pickup_hours = Column(Integer, nullable=False, default=72)
    sla_return_hours = Column(Integer, nullable=False, default=24)
    penalty_pct = Column(Numeric(5, 2), nullable=True, default=0)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerStatusHistory(Base):
    __tablename__ = "partner_status_history"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=False)
    reason = Column(Text, nullable=True)
    changed_by = Column(String(36), nullable=True)
    changed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
