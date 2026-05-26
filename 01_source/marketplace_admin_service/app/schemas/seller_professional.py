from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class TierDefinitionOut(BaseModel):
    code: str
    name: str
    min_gmv_cents: int
    max_commission_pct: Decimal
    monthly_fee_cents: int
    benefits_json: str
    sort_order: int
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TierDefinitionListOut(BaseModel):
    tiers: list[TierDefinitionOut]
    total: int


class TierEnrollmentCreateIn(BaseModel):
    seller_id: str
    tier_code: str
    effective_from: date
    effective_to: Optional[date] = None
    notes: Optional[str] = None
    status: str = "ACTIVE"


class TierEnrollmentOut(BaseModel):
    id: str
    seller_id: str
    tier_code: str
    status: str
    effective_from: date
    effective_to: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TierEnrollmentListOut(BaseModel):
    enrollments: list[TierEnrollmentOut]
    total: int


class ComplianceProfileCreateIn(BaseModel):
    seller_id: str
    country: str = "BR"
    tax_regime: str = "SIMPLES"
    tax_id: Optional[str] = None
    vat_number: Optional[str] = None
    ioss_number: Optional[str] = None
    fiscal_status: str = "PENDING"
    cross_border_enabled: bool = False
    notes: Optional[str] = None


class ComplianceProfileUpdateIn(BaseModel):
    tax_regime: Optional[str] = None
    tax_id: Optional[str] = None
    vat_number: Optional[str] = None
    ioss_number: Optional[str] = None
    fiscal_status: Optional[str] = None
    cross_border_enabled: Optional[bool] = None
    notes: Optional[str] = None


class ComplianceProfileOut(BaseModel):
    id: str
    seller_id: str
    country: str
    tax_regime: str
    tax_id: Optional[str] = None
    vat_number: Optional[str] = None
    ioss_number: Optional[str] = None
    fiscal_status: str
    cross_border_enabled: bool
    notes: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComplianceProfileListOut(BaseModel):
    profiles: list[ComplianceProfileOut]
    total: int


class PerformanceMonthlyCreateIn(BaseModel):
    seller_id: str
    month: date
    gmv_cents: int = 0
    order_count: int = 0
    avg_rating: Optional[Decimal] = None
    defect_rate_pct: Decimal = Field(default=Decimal("0"))
    on_time_pickup_pct: Decimal = Field(default=Decimal("100"))
    chargeback_count: int = 0


class PerformanceMonthlyOut(BaseModel):
    id: str
    seller_id: str
    month: date
    gmv_cents: int
    order_count: int
    avg_rating: Optional[Decimal] = None
    defect_rate_pct: Decimal
    on_time_pickup_pct: Decimal
    chargeback_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PerformanceMonthlyListOut(BaseModel):
    rows: list[PerformanceMonthlyOut]
    total: int


class AgreementCreateIn(BaseModel):
    seller_id: str
    agreement_type: str
    version: str
    status: str = "DRAFT"
    document_ref: Optional[str] = None
    expires_at: Optional[datetime] = None


class AgreementUpdateIn(BaseModel):
    status: Optional[str] = None
    document_ref: Optional[str] = None
    signed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class AgreementOut(BaseModel):
    id: str
    seller_id: str
    agreement_type: str
    version: str
    status: str
    document_ref: Optional[str] = None
    signed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgreementListOut(BaseModel):
    agreements: list[AgreementOut]
    total: int


class RiskAssessmentCreateIn(BaseModel):
    seller_id: str
    risk_score: int = Field(ge=0, le=100, default=50)
    risk_band: str = "MEDIUM"
    factors_json: str = "[]"
    next_review_at: Optional[datetime] = None


class RiskAssessmentOut(BaseModel):
    id: str
    seller_id: str
    risk_score: int
    risk_band: str
    factors_json: str
    assessed_at: datetime
    next_review_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RiskAssessmentListOut(BaseModel):
    assessments: list[RiskAssessmentOut]
    total: int


class SellerProfessionalSummaryOut(BaseModel):
    tier_enrollments_active: int
    compliance_profiles_verified: int
    agreements_signed: int
    latest_risk_band: Optional[str] = None
    latest_risk_score: Optional[int] = None
    performance_rows: int
