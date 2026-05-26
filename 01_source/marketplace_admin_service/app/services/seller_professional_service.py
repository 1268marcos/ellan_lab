from __future__ import annotations

import json
from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.seller_professional import (
    SellerAgreement,
    SellerComplianceProfile,
    SellerPerformanceMonthly,
    SellerRiskAssessment,
    SellerTierDefinition,
    SellerTierEnrollment,
)
from app.schemas.seller_professional import (
    AgreementCreateIn,
    AgreementUpdateIn,
    ComplianceProfileCreateIn,
    ComplianceProfileUpdateIn,
    PerformanceMonthlyCreateIn,
    RiskAssessmentCreateIn,
    SellerProfessionalSummaryOut,
    TierEnrollmentCreateIn,
)
from app.services.crypto_util import new_id
from app.services.seller_service import get_seller_or_404


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


TIER_DEFINITIONS_SEED = [
    {
        "code": "STARTER",
        "name": "Starter — onboarding",
        "min_gmv_cents": 0,
        "max_commission_pct": 12.0,
        "monthly_fee_cents": 0,
        "benefits_json": '["LOCKER_BASIC","EMAIL_SUPPORT"]',
        "sort_order": 10,
    },
    {
        "code": "GROWTH",
        "name": "Growth — Magalu / ML scale",
        "min_gmv_cents": 500_000,
        "max_commission_pct": 10.0,
        "monthly_fee_cents": 9900,
        "benefits_json": '["PRIORITY_LISTING","MULTI_CHANNEL","DEDICATED_SLA"]',
        "sort_order": 20,
    },
    {
        "code": "ENTERPRISE",
        "name": "Enterprise — global corridors",
        "min_gmv_cents": 5_000_000,
        "max_commission_pct": 8.0,
        "monthly_fee_cents": 49900,
        "benefits_json": '["CUSTOM_COMMISSION","IOSS_VAT","GLOBAL_CORRIDOR","API_DEDICATED"]',
        "sort_order": 30,
    },
]


def seed_tier_definitions(db: Session) -> int:
    n = 0
    for spec in TIER_DEFINITIONS_SEED:
        if not db.get(SellerTierDefinition, spec["code"]):
            db.add(SellerTierDefinition(**spec, active=True, created_at=_utcnow()))
            n += 1
    db.commit()
    return n


def list_tier_definitions(db: Session, active_only: bool = False) -> list[SellerTierDefinition]:
    q = db.query(SellerTierDefinition)
    if active_only:
        q = q.filter(SellerTierDefinition.active.is_(True))
    return q.order_by(SellerTierDefinition.sort_order).all()


def list_tier_enrollments(db: Session, seller_id: str | None = None) -> list[SellerTierEnrollment]:
    q = db.query(SellerTierEnrollment)
    if seller_id:
        q = q.filter(SellerTierEnrollment.seller_id == seller_id)
    return q.order_by(SellerTierEnrollment.effective_from.desc()).all()


def create_tier_enrollment(db: Session, body: TierEnrollmentCreateIn) -> SellerTierEnrollment:
    get_seller_or_404(db, body.seller_id)
    if not db.get(SellerTierDefinition, body.tier_code):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="tier_not_found")
    now = _utcnow()
    row = SellerTierEnrollment(id=new_id(), created_at=now, updated_at=now, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_compliance_profiles(db: Session, seller_id: str | None = None) -> list[SellerComplianceProfile]:
    q = db.query(SellerComplianceProfile)
    if seller_id:
        q = q.filter(SellerComplianceProfile.seller_id == seller_id)
    return q.order_by(SellerComplianceProfile.country).all()


def create_compliance_profile(db: Session, body: ComplianceProfileCreateIn) -> SellerComplianceProfile:
    get_seller_or_404(db, body.seller_id)
    exists = (
        db.query(SellerComplianceProfile)
        .filter(
            SellerComplianceProfile.seller_id == body.seller_id,
            SellerComplianceProfile.country == body.country.upper(),
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="compliance_profile_exists")
    now = _utcnow()
    data = body.model_dump()
    data["country"] = body.country.upper()
    row = SellerComplianceProfile(id=new_id(), created_at=now, updated_at=now, **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_compliance_profile(
    db: Session, profile_id: str, body: ComplianceProfileUpdateIn
) -> SellerComplianceProfile:
    row = db.get(SellerComplianceProfile, profile_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="compliance_profile_not_found")
    data = body.model_dump(exclude_unset=True)
    if data.get("fiscal_status") == "VERIFIED" and not row.verified_at:
        row.verified_at = _utcnow()
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def list_performance_monthly(db: Session, seller_id: str | None = None) -> list[SellerPerformanceMonthly]:
    q = db.query(SellerPerformanceMonthly)
    if seller_id:
        q = q.filter(SellerPerformanceMonthly.seller_id == seller_id)
    return q.order_by(SellerPerformanceMonthly.month.desc()).all()


def upsert_performance_monthly(db: Session, body: PerformanceMonthlyCreateIn) -> SellerPerformanceMonthly:
    get_seller_or_404(db, body.seller_id)
    row = (
        db.query(SellerPerformanceMonthly)
        .filter(
            SellerPerformanceMonthly.seller_id == body.seller_id,
            SellerPerformanceMonthly.month == body.month,
        )
        .first()
    )
    now = _utcnow()
    if row:
        for k, v in body.model_dump().items():
            setattr(row, k, v)
        row.updated_at = now
    else:
        row = SellerPerformanceMonthly(id=new_id(), created_at=now, updated_at=now, **body.model_dump())
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_agreements(db: Session, seller_id: str | None = None) -> list[SellerAgreement]:
    q = db.query(SellerAgreement)
    if seller_id:
        q = q.filter(SellerAgreement.seller_id == seller_id)
    return q.order_by(SellerAgreement.created_at.desc()).all()


def create_agreement(db: Session, body: AgreementCreateIn) -> SellerAgreement:
    get_seller_or_404(db, body.seller_id)
    now = _utcnow()
    row = SellerAgreement(id=new_id(), created_at=now, updated_at=now, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_agreement(db: Session, agreement_id: str, body: AgreementUpdateIn) -> SellerAgreement:
    row = db.get(SellerAgreement, agreement_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="agreement_not_found")
    data = body.model_dump(exclude_unset=True)
    if data.get("status") == "SIGNED" and not row.signed_at:
        row.signed_at = data.get("signed_at") or _utcnow()
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def list_risk_assessments(db: Session, seller_id: str | None = None) -> list[SellerRiskAssessment]:
    q = db.query(SellerRiskAssessment)
    if seller_id:
        q = q.filter(SellerRiskAssessment.seller_id == seller_id)
    return q.order_by(SellerRiskAssessment.assessed_at.desc()).all()


def create_risk_assessment(db: Session, body: RiskAssessmentCreateIn) -> SellerRiskAssessment:
    get_seller_or_404(db, body.seller_id)
    factors = body.factors_json
    try:
        json.loads(factors)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_factors_json")
    now = _utcnow()
    row = SellerRiskAssessment(
        id=new_id(),
        created_at=now,
        assessed_at=now,
        **body.model_dump(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def professional_summary(db: Session, seller_id: str | None = None) -> SellerProfessionalSummaryOut:
    eq = seller_id
    enroll_q = db.query(SellerTierEnrollment).filter(SellerTierEnrollment.status == "ACTIVE")
    comp_q = db.query(SellerComplianceProfile).filter(SellerComplianceProfile.fiscal_status == "VERIFIED")
    agr_q = db.query(SellerAgreement).filter(SellerAgreement.status == "SIGNED")
    perf_q = db.query(SellerPerformanceMonthly)
    risk_q = db.query(SellerRiskAssessment)
    if eq:
        enroll_q = enroll_q.filter(SellerTierEnrollment.seller_id == eq)
        comp_q = comp_q.filter(SellerComplianceProfile.seller_id == eq)
        agr_q = agr_q.filter(SellerAgreement.seller_id == eq)
        perf_q = perf_q.filter(SellerPerformanceMonthly.seller_id == eq)
        risk_q = risk_q.filter(SellerRiskAssessment.seller_id == eq)
    latest = risk_q.order_by(SellerRiskAssessment.assessed_at.desc()).first()
    return SellerProfessionalSummaryOut(
        tier_enrollments_active=enroll_q.count(),
        compliance_profiles_verified=comp_q.count(),
        agreements_signed=agr_q.count(),
        latest_risk_band=latest.risk_band if latest else None,
        latest_risk_score=latest.risk_score if latest else None,
        performance_rows=perf_q.count(),
    )


def seed_seller_professional_demo(db: Session, seller_id: str = "mk-seller-demo-001") -> dict[str, int]:
    seed_tier_definitions(db)
    counts = {
        "tier_enrollments": 0,
        "compliance_profiles": 0,
        "performance_rows": 0,
        "agreements": 0,
        "risk_assessments": 0,
    }
    now = _utcnow()
    month = date.today().replace(day=1)

    if not db.query(SellerTierEnrollment).filter(SellerTierEnrollment.id == "mk-tier-enroll-001").first():
        db.add(
            SellerTierEnrollment(
                id="mk-tier-enroll-001",
                seller_id=seller_id,
                tier_code="GROWTH",
                status="ACTIVE",
                effective_from=month,
                notes="Demo Magalu + Mercado Livre scale",
                created_at=now,
                updated_at=now,
            )
        )
        counts["tier_enrollments"] += 1

    if not db.get(SellerComplianceProfile, "mk-compliance-br-001"):
        db.add(
            SellerComplianceProfile(
                id="mk-compliance-br-001",
                seller_id=seller_id,
                country="BR",
                tax_regime="SIMPLES",
                tax_id="12.345.678/0001-90",
                fiscal_status="VERIFIED",
                cross_border_enabled=False,
                verified_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        counts["compliance_profiles"] += 1

    if not db.get(SellerComplianceProfile, "mk-compliance-eu-001"):
        db.add(
            SellerComplianceProfile(
                id="mk-compliance-eu-001",
                seller_id=seller_id,
                country="ES",
                tax_regime="OSS",
                vat_number="ESB12345678",
                ioss_number="IM1234567890",
                fiscal_status="VERIFIED",
                cross_border_enabled=True,
                notes="El Corte Ingles / Amazon EU corridor",
                verified_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        counts["compliance_profiles"] += 1

    perf_id = "mk-perf-demo-001"
    if not db.get(SellerPerformanceMonthly, perf_id):
        db.add(
            SellerPerformanceMonthly(
                id=perf_id,
                seller_id=seller_id,
                month=month,
                gmv_cents=1_250_000,
                order_count=42,
                avg_rating=4.2,
                defect_rate_pct=1.5,
                on_time_pickup_pct=96.5,
                chargeback_count=0,
                created_at=now,
                updated_at=now,
            )
        )
        counts["performance_rows"] += 1

    if not db.get(SellerAgreement, "mk-agreement-001"):
        db.add(
            SellerAgreement(
                id="mk-agreement-001",
                seller_id=seller_id,
                agreement_type="MARKETPLACE_TERMS",
                version="2026.05",
                status="SIGNED",
                document_ref="s3://ellanlab-demo/agreements/mk-seller-demo-001-terms.pdf",
                signed_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        counts["agreements"] += 1

    if not db.get(SellerAgreement, "mk-agreement-002"):
        db.add(
            SellerAgreement(
                id="mk-agreement-002",
                seller_id=seller_id,
                agreement_type="DATA_PROCESSING",
                version="2026.05",
                status="SIGNED",
                document_ref="s3://ellanlab-demo/agreements/mk-seller-demo-001-dpa.pdf",
                signed_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        counts["agreements"] += 1

    if not db.get(SellerRiskAssessment, "mk-risk-001"):
        db.add(
            SellerRiskAssessment(
                id="mk-risk-001",
                seller_id=seller_id,
                risk_score=28,
                risk_band="LOW",
                factors_json='[{"code":"KYC_VERIFIED","weight":-15},{"code":"LOW_CHARGEBACK","weight":-10}]',
                assessed_at=now,
                next_review_at=now,
                created_at=now,
            )
        )
        counts["risk_assessments"] += 1

    db.commit()
    return counts
