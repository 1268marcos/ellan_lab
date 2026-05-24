from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.finance import PartnerBillingPlan
from app.models.finance_catalog import FinanceLockerNetworkCatalog
from app.models.finance_ecosystem import FinancePlayerCapability, FinancePlayerRelation
from app.models.finance_professional import FinancePartnerReadiness
from app.models.finance_world_meta import FinancePlayerCountryCoverage
from app.services.finance_catalog_service import match_blueprint_for_player


def _grade(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 50:
        return "C"
    return "D"


def _score_blueprint(db: Session, row: FinanceLockerNetworkCatalog, blockers: list[str]) -> tuple[int, str | None]:
    blueprint = match_blueprint_for_player(db, row)
    if not blueprint:
        blockers.append("no_integration_blueprint")
        return 0, None

    score = 0
    cap_codes = {
        c.capability_code
        for c in db.query(FinancePlayerCapability)
        .filter(FinancePlayerCapability.catalog_code == row.code)
        .all()
    }
    if blueprint.primary_capability in cap_codes:
        score += 10
    else:
        blockers.append(f"missing_capability:{blueprint.primary_capability}")

    has_coverage = (
        db.query(FinancePlayerCountryCoverage)
        .filter(FinancePlayerCountryCoverage.catalog_code == row.code)
        .first()
        is not None
    )
    if has_coverage:
        score += 5
    elif row.regions_json and row.regions_json != "[]":
        score += 3
    else:
        blockers.append("no_country_coverage")

    if row.integration_status == "LIVE":
        score += 5
    elif row.integration_status == "PILOT":
        score += 3

    return min(20, score), blueprint.code


def _score_catalog_row(db: Session, row: FinanceLockerNetworkCatalog) -> FinancePartnerReadiness:
    blockers: list[str] = []
    integration = {"LIVE": 35, "PILOT": 24, "IN_PROGRESS": 15, "PLANNED": 6}.get(row.integration_status, 4)
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
    compliance = min(15, cap_count * 4) + min(10, rel_count * 3)
    if cap_count == 0:
        blockers.append("no_capabilities_mapped")
    if row.api_docs_url:
        compliance += 5

    blueprint_score, blueprint_code = _score_blueprint(db, row, blockers)

    integration_extra = min(10, cap_count * 2)
    integration_score = min(45, integration + integration_extra)
    billing_score = min(30, billing)
    compliance_score = min(15, compliance)
    total = min(100, integration_score + billing_score + compliance_score + blueprint_score)

    return FinancePartnerReadiness(
        catalog_code=row.code,
        readiness_score=total,
        integration_score=integration_score,
        billing_score=billing_score,
        compliance_score=compliance_score,
        blueprint_score=blueprint_score,
        integration_blueprint_code=blueprint_code,
        grade=_grade(total),
        blockers_json=json.dumps(blockers[:10]),
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
            existing.blueprint_score = scored.blueprint_score
            existing.integration_blueprint_code = scored.integration_blueprint_code
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
