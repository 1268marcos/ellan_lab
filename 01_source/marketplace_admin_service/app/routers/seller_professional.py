from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.seller_professional import (
    AgreementCreateIn,
    AgreementListOut,
    AgreementOut,
    AgreementUpdateIn,
    ComplianceProfileCreateIn,
    ComplianceProfileListOut,
    ComplianceProfileOut,
    ComplianceProfileUpdateIn,
    PerformanceMonthlyCreateIn,
    PerformanceMonthlyListOut,
    PerformanceMonthlyOut,
    RiskAssessmentCreateIn,
    RiskAssessmentListOut,
    RiskAssessmentOut,
    SellerProfessionalSummaryOut,
    TierDefinitionListOut,
    TierDefinitionOut,
    TierEnrollmentCreateIn,
    TierEnrollmentListOut,
    TierEnrollmentOut,
)
from app.services import seller_professional_service as svc

router = APIRouter(tags=["seller-professional"])


@router.post("/seller-professional/seed")
def seed_seller_professional(db: Session = Depends(get_db)) -> dict:
    svc.seed_tier_definitions(db)
    return svc.seed_seller_professional_demo(db)


@router.get("/seller-professional/summary", response_model=SellerProfessionalSummaryOut)
def professional_summary(
    seller_id: str | None = Query(None), db: Session = Depends(get_db)
) -> SellerProfessionalSummaryOut:
    return svc.professional_summary(db, seller_id=seller_id)


@router.get("/seller-tier-definitions", response_model=TierDefinitionListOut)
def list_tier_definitions(active_only: bool = Query(False), db: Session = Depends(get_db)) -> TierDefinitionListOut:
    rows = svc.list_tier_definitions(db, active_only=active_only)
    out = [TierDefinitionOut.model_validate(r) for r in rows]
    return TierDefinitionListOut(tiers=out, total=len(out))


@router.get("/seller-tier-enrollments", response_model=TierEnrollmentListOut)
def list_tier_enrollments(
    seller_id: str | None = Query(None), db: Session = Depends(get_db)
) -> TierEnrollmentListOut:
    rows = svc.list_tier_enrollments(db, seller_id=seller_id)
    out = [TierEnrollmentOut.model_validate(r) for r in rows]
    return TierEnrollmentListOut(enrollments=out, total=len(out))


@router.post("/seller-tier-enrollments", response_model=TierEnrollmentOut, status_code=status.HTTP_201_CREATED)
def create_tier_enrollment(body: TierEnrollmentCreateIn, db: Session = Depends(get_db)) -> TierEnrollmentOut:
    return TierEnrollmentOut.model_validate(svc.create_tier_enrollment(db, body))


@router.get("/seller-compliance-profiles", response_model=ComplianceProfileListOut)
def list_compliance_profiles(
    seller_id: str | None = Query(None), db: Session = Depends(get_db)
) -> ComplianceProfileListOut:
    rows = svc.list_compliance_profiles(db, seller_id=seller_id)
    out = [ComplianceProfileOut.model_validate(r) for r in rows]
    return ComplianceProfileListOut(profiles=out, total=len(out))


@router.post("/seller-compliance-profiles", response_model=ComplianceProfileOut, status_code=status.HTTP_201_CREATED)
def create_compliance_profile(body: ComplianceProfileCreateIn, db: Session = Depends(get_db)) -> ComplianceProfileOut:
    return ComplianceProfileOut.model_validate(svc.create_compliance_profile(db, body))


@router.patch("/seller-compliance-profiles/{profile_id}", response_model=ComplianceProfileOut)
def update_compliance_profile(
    profile_id: str, body: ComplianceProfileUpdateIn, db: Session = Depends(get_db)
) -> ComplianceProfileOut:
    return ComplianceProfileOut.model_validate(svc.update_compliance_profile(db, profile_id, body))


@router.get("/seller-performance-monthly", response_model=PerformanceMonthlyListOut)
def list_performance_monthly(
    seller_id: str | None = Query(None), db: Session = Depends(get_db)
) -> PerformanceMonthlyListOut:
    rows = svc.list_performance_monthly(db, seller_id=seller_id)
    out = [PerformanceMonthlyOut.model_validate(r) for r in rows]
    return PerformanceMonthlyListOut(rows=out, total=len(out))


@router.put("/seller-performance-monthly", response_model=PerformanceMonthlyOut)
def upsert_performance_monthly(body: PerformanceMonthlyCreateIn, db: Session = Depends(get_db)) -> PerformanceMonthlyOut:
    return PerformanceMonthlyOut.model_validate(svc.upsert_performance_monthly(db, body))


@router.get("/seller-agreements", response_model=AgreementListOut)
def list_agreements(seller_id: str | None = Query(None), db: Session = Depends(get_db)) -> AgreementListOut:
    rows = svc.list_agreements(db, seller_id=seller_id)
    out = [AgreementOut.model_validate(r) for r in rows]
    return AgreementListOut(agreements=out, total=len(out))


@router.post("/seller-agreements", response_model=AgreementOut, status_code=status.HTTP_201_CREATED)
def create_agreement(body: AgreementCreateIn, db: Session = Depends(get_db)) -> AgreementOut:
    return AgreementOut.model_validate(svc.create_agreement(db, body))


@router.patch("/seller-agreements/{agreement_id}", response_model=AgreementOut)
def update_agreement(agreement_id: str, body: AgreementUpdateIn, db: Session = Depends(get_db)) -> AgreementOut:
    return AgreementOut.model_validate(svc.update_agreement(db, agreement_id, body))


@router.get("/seller-risk-assessments", response_model=RiskAssessmentListOut)
def list_risk_assessments(
    seller_id: str | None = Query(None), db: Session = Depends(get_db)
) -> RiskAssessmentListOut:
    rows = svc.list_risk_assessments(db, seller_id=seller_id)
    out = [RiskAssessmentOut.model_validate(r) for r in rows]
    return RiskAssessmentListOut(assessments=out, total=len(out))


@router.post("/seller-risk-assessments", response_model=RiskAssessmentOut, status_code=status.HTTP_201_CREATED)
def create_risk_assessment(body: RiskAssessmentCreateIn, db: Session = Depends(get_db)) -> RiskAssessmentOut:
    return RiskAssessmentOut.model_validate(svc.create_risk_assessment(db, body))
