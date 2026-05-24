from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finance_intelligence import (
    BenchmarkListOut,
    EcosystemInsightListOut,
    EcosystemInsightOut,
    HealthCheckListOut,
    HealthCheckOut,
    IntelligenceAnalyzeOut,
    IntelligenceDashboardOut,
    PlayerBenchmarkOut,
    RecommendationListOut,
    RecommendationOut,
)
from app.services import finance_ecosystem_intelligence_service as intel_svc

router = APIRouter(prefix="/ecosystem-intelligence", tags=["ecosystem-intelligence"])


@router.get("/dashboard", response_model=IntelligenceDashboardOut)
def intelligence_dashboard(db: Session = Depends(get_db)) -> IntelligenceDashboardOut:
    data = intel_svc.intelligence_dashboard(db)
    return IntelligenceDashboardOut(
        open_insights=data["open_insights"],
        critical_insights=data["critical_insights"],
        players_analyzed=data["players_analyzed"],
        avg_readiness=data["avg_readiness"],
        avg_composite_score=data["avg_composite_score"],
        top_benchmarks=[PlayerBenchmarkOut.model_validate(b) for b in data["top_benchmarks"]],
        recent_insights=[EcosystemInsightOut.model_validate(i) for i in data["recent_insights"]],
        health_summary=data["health_summary"],
    )


@router.get("/insights", response_model=EcosystemInsightListOut)
def list_insights(
    catalog_code: str | None = Query(None),
    status: str | None = Query("OPEN"),
    severity: str | None = Query(None),
    db: Session = Depends(get_db),
) -> EcosystemInsightListOut:
    rows = intel_svc.list_insights(db, catalog_code=catalog_code, status=status, severity=severity)
    items = [EcosystemInsightOut.model_validate(r) for r in rows]
    by_sev: dict[str, int] = {}
    for i in items:
        by_sev[i.severity] = by_sev.get(i.severity, 0) + 1
    open_count = len([i for i in items if i.status == "OPEN"])
    return EcosystemInsightListOut(
        items=items,
        total=len(items),
        open_count=open_count,
        by_severity=by_sev,
    )


@router.post("/insights/{insight_id}/resolve", response_model=EcosystemInsightOut)
def resolve_insight(insight_id: str, db: Session = Depends(get_db)) -> EcosystemInsightOut:
    row = intel_svc.resolve_insight(db, insight_id)
    if not row:
        raise HTTPException(status_code=404, detail="insight_not_found")
    return EcosystemInsightOut.model_validate(row)


@router.get("/benchmarks", response_model=BenchmarkListOut)
def list_benchmarks(
    segment_code: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
) -> BenchmarkListOut:
    rows = intel_svc.list_benchmarks(db, segment_code=segment_code, limit=limit)
    items = [PlayerBenchmarkOut.model_validate(r) for r in rows]
    return BenchmarkListOut(items=items, total=len(items), top_global=items[:10])


@router.get("/health-checks", response_model=HealthCheckListOut)
def list_health_checks(
    catalog_code: str | None = Query(None),
    db: Session = Depends(get_db),
) -> HealthCheckListOut:
    rows = intel_svc.list_health_checks(db, catalog_code)
    items = [HealthCheckOut.model_validate(r) for r in rows]
    healthy = sum(1 for i in items if i.status == "HEALTHY")
    degraded = sum(1 for i in items if i.status == "DEGRADED")
    return HealthCheckListOut(items=items, total=len(items), healthy_count=healthy, degraded_count=degraded)


@router.get("/recommendations/{catalog_code}", response_model=RecommendationListOut)
def get_recommendations(catalog_code: str, db: Session = Depends(get_db)) -> RecommendationListOut:
    items_raw = intel_svc.get_recommendations(db, catalog_code)
    items = [RecommendationOut.model_validate(x) for x in items_raw]
    return RecommendationListOut(catalog_code=catalog_code.upper(), items=items, total=len(items))


@router.post("/generate-milestones/{catalog_code}")
def generate_milestones(catalog_code: str, db: Session = Depends(get_db)) -> dict[str, str | int]:
    n = intel_svc.generate_playbook_milestones(db, catalog_code)
    return {"catalog_code": catalog_code.upper(), "milestones_created": n}


@router.post("/analyze", response_model=IntelligenceAnalyzeOut)
def analyze_ecosystem(db: Session = Depends(get_db)) -> IntelligenceAnalyzeOut:
    result = intel_svc.run_full_intelligence_scan(db)
    return IntelligenceAnalyzeOut(**result)
