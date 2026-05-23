from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.finance import PartnerBillingPlan
from app.models.finance_catalog import FinanceLockerNetworkCatalog
from app.models.finance_ecosystem import FinancePlayerCapability, FinancePlayerRelation
from app.models.finance_professional import FinancePartnerReadiness


def _grade(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 50:
        return "C"
    return "D"


def _score_catalog_row(db: Session, row: FinanceLockerNetworkCatalog) -> FinancePartnerReadiness:
    blockers: list[str] = []
    integration = {"LIVE": 40, "PILOT": 28, "IN_PROGRESS": 18, "PLANNED": 8}.get(
        row.integration_status, 5
    )
    if row.integration_status != "LIVE":
        blockers.append(f"integration_status={row.integration_status}")

    billing = 0
    if row.finance_partner_id:
        billing += 15
        has_plan = (
            db.query(PartnerBillingPlan)
            .filter(
                PartnerBillingPlan.partner_id == row.finance_partner_id,
                PartnerBillingPlan.is_active.is_(True),
            )
            .first()
        )
        if has_plan:
            billing += 15
        else:
            blockers.append("no_active_billing_plan")
    else:
        blockers.append("no_finance_partner")

    cap_count = (
        db.query(FinancePlayerCapability)
        .filter(FinancePlayerCapability.catalog_code == row.code)
        .count()
    )
    rel_count = (
        db.query(FinancePlayerRelation)
        .filter(
            (FinancePlayerRelation.from_catalog_code == row.code)
            | (FinancePlayerRelation.to_catalog_code == row.code)
        )
        .count()
    )
    compliance = min(20, cap_count * 5) + min(10, rel_count * 3)
    if cap_count == 0:
        blockers.append("no_capabilities_mapped")
    if row.api_docs_url:
        compliance += 5

    integration_extra = min(15, cap_count * 3)
    integration_score = min(50, integration + integration_extra)
    billing_score = min(30, billing)
    compliance_score = min(20, compliance)
    total = min(100, integration_score + billing_score + compliance_score)

    return FinancePartnerReadiness(
        catalog_code=row.code,
        readiness_score=total,
        integration_score=integration_score,
        billing_score=billing_score,
        compliance_score=compliance_score,
        grade=_grade(total),
        blockers_json=json.dumps(blockers[:8]),
        computed_at=datetime.now(timezone.utc),
    )


def recompute_all_readiness(db: Session) -> tuple[int, float]:
    rows = db.query(FinanceLockerNetworkCatalog).filter(FinanceLockerNetworkCatalog.active.is_(True)).all()
    scores: list[int] = []
    for row in rows:
        scored = _score_catalog_row(db, row)
        existing = db.get(FinancePartnerReadiness, row.code)
        if existing:
            existing.readiness_score = scored.readiness_score
            existing.integration_score = scored.integration_score
            existing.billing_score = scored.billing_score
            existing.compliance_score = scored.compliance_score
            existing.grade = scored.grade
            existing.blockers_json = scored.blockers_json
            existing.computed_at = scored.computed_at
        else:
            db.add(scored)
        scores.append(scored.readiness_score)
    db.commit()
    avg = sum(scores) / len(scores) if scores else 0.0
    return len(scores), avg


def list_readiness(db: Session, *, min_score: int | None = None, grade: str | None = None) -> list[FinancePartnerReadiness]:
    q = db.query(FinancePartnerReadiness).order_by(
        FinancePartnerReadiness.readiness_score.desc(),
        FinancePartnerReadiness.catalog_code,
    )
    if min_score is not None:
        q = q.filter(FinancePartnerReadiness.readiness_score >= min_score)
    if grade:
        q = q.filter(FinancePartnerReadiness.grade == grade)
    return q.all()
