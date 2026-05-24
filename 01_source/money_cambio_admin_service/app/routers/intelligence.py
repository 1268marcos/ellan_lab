from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.intelligence import (
    EcosystemInsightListOut,
    EcosystemInsightOut,
    FxAlertEventListOut,
    FxAlertEventOut,
    FxAlertRuleIn,
    FxAlertRuleListOut,
    FxAlertRuleOut,
    IntelligenceAnalyzeOut,
    IntelligenceDashboardOut,
    PlayerReadinessListOut,
    PlayerReadinessOut,
    SettlementScheduleIn,
    SettlementScheduleListOut,
    SettlementScheduleOut,
)
from app.services import intelligence_service as intel_svc

router = APIRouter(prefix="/money-intelligence", tags=["money-intelligence"])


@router.get("/dashboard", response_model=IntelligenceDashboardOut)
def intelligence_dashboard(db: Session = Depends(get_db)) -> IntelligenceDashboardOut:
    return intel_svc.intelligence_dashboard(db)


@router.post("/analyze", response_model=IntelligenceAnalyzeOut)
def analyze_ecosystem(db: Session = Depends(get_db)) -> IntelligenceAnalyzeOut:
    return intel_svc.analyze_ecosystem(db)


@router.get("/readiness", response_model=PlayerReadinessListOut)
def list_readiness(
    min_score: int | None = None,
    grade: str | None = None,
    db: Session = Depends(get_db),
) -> PlayerReadinessListOut:
    rows = intel_svc.list_readiness(db, min_score=min_score, grade=grade)
    items = [PlayerReadinessOut.model_validate(r) for r in rows]
    avg = round(sum(r.readiness_score for r in rows) / len(rows), 1) if rows else 0.0
    return PlayerReadinessListOut(items=items, total=len(items), avg_score=avg)


@router.get("/insights", response_model=EcosystemInsightListOut)
def list_insights(
    status: str | None = Query("OPEN"),
    severity: str | None = None,
    player_code: str | None = None,
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> EcosystemInsightListOut:
    rows = intel_svc.list_insights(
        db, status=status, severity=severity, player_code=player_code, limit=limit
    )
    items = [EcosystemInsightOut.model_validate(r) for r in rows]
    from app.models.intelligence import MoneyEcosystemInsight

    sev_rows = (
        db.query(MoneyEcosystemInsight.severity, func.count(MoneyEcosystemInsight.id))
        .filter(MoneyEcosystemInsight.status == (status or "OPEN").upper())
        .group_by(MoneyEcosystemInsight.severity)
        .all()
    )
    by_sev = {s: int(c) for s, c in sev_rows}
    return EcosystemInsightListOut(items=items, total=len(items), open_by_severity=by_sev)


@router.post("/insights/{insight_id}/resolve", response_model=EcosystemInsightOut)
def resolve_insight(insight_id: str, db: Session = Depends(get_db)) -> EcosystemInsightOut:
    row = intel_svc.resolve_insight(db, insight_id)
    return EcosystemInsightOut.model_validate(row)


@router.get("/fx-alert-rules", response_model=FxAlertRuleListOut)
def list_fx_rules(db: Session = Depends(get_db)) -> FxAlertRuleListOut:
    rows = intel_svc.list_fx_rules(db)
    items = [FxAlertRuleOut.model_validate(r) for r in rows]
    return FxAlertRuleListOut(items=items, total=len(items))


@router.post("/fx-alert-rules", response_model=FxAlertRuleOut, status_code=status.HTTP_201_CREATED)
def create_fx_rule(body: FxAlertRuleIn, db: Session = Depends(get_db)) -> FxAlertRuleOut:
    row = intel_svc.create_fx_rule(db, body)
    return FxAlertRuleOut.model_validate(row)


@router.get("/fx-alert-events", response_model=FxAlertEventListOut)
def list_fx_events(status: str | None = Query("OPEN"), db: Session = Depends(get_db)) -> FxAlertEventListOut:
    rows = intel_svc.list_fx_events(db, status=status)
    items = [FxAlertEventOut.model_validate(r) for r in rows]
    return FxAlertEventListOut(items=items, total=len(items))


@router.post("/fx-alert-events/{event_id}/acknowledge", response_model=FxAlertEventOut)
def ack_fx_event(event_id: str, db: Session = Depends(get_db)) -> FxAlertEventOut:
    row = intel_svc.acknowledge_fx_event(db, event_id)
    return FxAlertEventOut.model_validate(row)


@router.get("/settlement-schedules", response_model=SettlementScheduleListOut)
def list_settlements(
    scope_code: str | None = None, db: Session = Depends(get_db)
) -> SettlementScheduleListOut:
    rows = intel_svc.list_settlement_schedules(db, scope_code=scope_code)
    items = [SettlementScheduleOut.model_validate(r) for r in rows]
    return SettlementScheduleListOut(items=items, total=len(items))


@router.post("/settlement-schedules", response_model=SettlementScheduleOut, status_code=status.HTTP_201_CREATED)
def create_settlement(body: SettlementScheduleIn, db: Session = Depends(get_db)) -> SettlementScheduleOut:
    row = intel_svc.create_settlement_schedule(db, body)
    return SettlementScheduleOut.model_validate(row)
