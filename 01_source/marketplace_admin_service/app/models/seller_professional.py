from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SellerTierDefinition(Base):
    __tablename__ = "seller_tier_definitions"

    code = Column(String(32), primary_key=True)
    name = Column(String(128), nullable=False)
    min_gmv_cents = Column(BigInteger, nullable=False, default=0)
    max_commission_pct = Column(Numeric(5, 2), nullable=False, default=30.00)
    monthly_fee_cents = Column(BigInteger, nullable=False, default=0)
    benefits_json = Column(Text, nullable=False, default="[]")
    sort_order = Column(Integer, nullable=False, default=100)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SellerTierEnrollment(Base):
    __tablename__ = "seller_tier_enrollments"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    tier_code = Column(String(32), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class SellerComplianceProfile(Base):
    __tablename__ = "seller_compliance_profiles"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    country = Column(String(2), nullable=False, default="BR")
    tax_regime = Column(String(32), nullable=False, default="SIMPLES")
    tax_id = Column(String(32), nullable=True)
    vat_number = Column(String(32), nullable=True)
    ioss_number = Column(String(32), nullable=True)
    fiscal_status = Column(String(20), nullable=False, default="PENDING")
    cross_border_enabled = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class SellerPerformanceMonthly(Base):
    __tablename__ = "seller_performance_monthly"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    month = Column(Date, nullable=False)
    gmv_cents = Column(BigInteger, nullable=False, default=0)
    order_count = Column(Integer, nullable=False, default=0)
    avg_rating = Column(Numeric(3, 2), nullable=True)
    defect_rate_pct = Column(Numeric(5, 2), nullable=False, default=0)
    on_time_pickup_pct = Column(Numeric(5, 2), nullable=False, default=100)
    chargeback_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class SellerAgreement(Base):
    __tablename__ = "seller_agreements"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    agreement_type = Column(String(32), nullable=False)
    version = Column(String(16), nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT")
    document_ref = Column(String(255), nullable=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class SellerRiskAssessment(Base):
    __tablename__ = "seller_risk_assessments"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    risk_score = Column(Integer, nullable=False, default=50)
    risk_band = Column(String(16), nullable=False, default="MEDIUM")
    factors_json = Column(Text, nullable=False, default="[]")
    assessed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    next_review_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
