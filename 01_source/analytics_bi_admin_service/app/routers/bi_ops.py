from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.bi_ops import (
    BiExportJobIn,
    BiExportJobOut,
    BiKpiAlertRuleIn,
    BiKpiAlertRuleOut,
    BiKpiAlertEventOut,
    BiLineageEdgeIn,
    BiLineageEdgeOut,
    BiMarketPresenceOut,
    BiMartRefreshJobIn,
    BiMartRefreshJobListOut,
    BiMartRefreshJobOut,
    BiOpsIntelligenceSummaryOut,
    BiReadinessListOut,
    BiReadinessOut,
    BiTaxonomyOut,
)
from app.services import bi_ops_service

router = APIRouter(tags=["bi-ops"])


@router.get("/ops-intelligence/summary", response_model=BiOpsIntelligenceSummaryOut)
def ops_summary(db: Session = Depends(get_db)) -> BiOpsIntelligenceSummaryOut:
    return bi_ops_service.ops_intelligence_summary(db)


@router.post("/ops-intelligence/seed-professional")
def seed_professional(db: Session = Depends(get_db)) -> dict:
    out = bi_ops_service.seed_taxonomy_and_lineage(db)
    out["market_presence"] = bi_ops_service.seed_market_presence(db)
    out["readiness_recomputed"] = bi_ops_service.recompute_all_readiness(db)
    return out


@router.get("/data-readiness", response_model=BiReadinessListOut)
def list_readiness(
    band: str | None = Query(None), db: Session = Depends(get_db)
) -> BiReadinessListOut:
    data = bi_ops_service.readiness_summary(db)
    rows = data["rows"]
    if band:
        rows = [r for r in rows if r["readiness_band"] == band]
    return BiReadinessListOut(
        rows=[BiReadinessOut.model_validate(r) for r in rows],
        total=len(rows),
        bands=data["bands"],
        avg_score=data["avg_score"],
    )


@router.post("/data-readiness/recompute")
def recompute_readiness(db: Session = Depends(get_db)) -> dict:
    return {"recomputed": bi_ops_service.recompute_all_readiness(db)}


@router.get("/mart-refresh-jobs", response_model=BiMartRefreshJobListOut)
def list_mart_jobs(db: Session = Depends(get_db)) -> BiMartRefreshJobListOut:
    jobs = bi_ops_service.list_mart_jobs(db)
    return BiMartRefreshJobListOut(
        jobs=[BiMartRefreshJobOut.model_validate(j) for j in jobs],
        total=len(jobs),
    )


@router.post("/mart-refresh-jobs", response_model=BiMartRefreshJobOut)
def trigger_mart(body: BiMartRefreshJobIn, db: Session = Depends(get_db)) -> BiMartRefreshJobOut:
    return BiMartRefreshJobOut.model_validate(bi_ops_service.trigger_mart_refresh(db, body))


@router.get("/kpi-alert-rules")
def list_rules(db: Session = Depends(get_db)) -> dict:
    rules = bi_ops_service.list_alert_rules(db)
    return {
        "rules": [BiKpiAlertRuleOut.model_validate(r) for r in rules],
        "total": len(rules),
    }


@router.post("/kpi-alert-rules", response_model=BiKpiAlertRuleOut)
def create_rule(body: BiKpiAlertRuleIn, db: Session = Depends(get_db)) -> BiKpiAlertRuleOut:
    return BiKpiAlertRuleOut.model_validate(bi_ops_service.create_alert_rule(db, body))


@router.get("/kpi-alert-events")
def list_events(status: str | None = Query(None), db: Session = Depends(get_db)) -> dict:
    events = bi_ops_service.list_alert_events(db, status=status)
    return {
        "events": [BiKpiAlertEventOut.model_validate(e) for e in events],
        "total": len(events),
    }


@router.get("/data-lineage")
def list_lineage(db: Session = Depends(get_db)) -> dict:
    edges = bi_ops_service.list_lineage(db)
    return {
        "edges": [BiLineageEdgeOut.model_validate(e) for e in edges],
        "total": len(edges),
    }


@router.post("/data-lineage", response_model=BiLineageEdgeOut)
def create_lineage(body: BiLineageEdgeIn, db: Session = Depends(get_db)) -> BiLineageEdgeOut:
    return BiLineageEdgeOut.model_validate(bi_ops_service.create_lineage(db, body))


@router.get("/export-jobs")
def list_exports(db: Session = Depends(get_db)) -> dict:
    jobs = bi_ops_service.list_export_jobs(db)
    return {
        "jobs": [BiExportJobOut.model_validate(j) for j in jobs],
        "total": len(jobs),
    }


@router.post("/export-jobs", response_model=BiExportJobOut)
def create_export(body: BiExportJobIn, db: Session = Depends(get_db)) -> BiExportJobOut:
    return BiExportJobOut.model_validate(bi_ops_service.create_export_job(db, body))


@router.get("/player-segment-taxonomy")
def list_taxonomy(db: Session = Depends(get_db)) -> dict:
    rows = bi_ops_service.list_taxonomy(db)
    return {"segments": [BiTaxonomyOut.model_validate(r) for r in rows], "total": len(rows)}


@router.get("/player-market-presence")
def list_presence(
    player_code: str | None = Query(None), db: Session = Depends(get_db)
) -> dict:
    rows = bi_ops_service.list_market_presence(db, player_code=player_code)
    return {
        "presence": [BiMarketPresenceOut.model_validate(r) for r in rows],
        "total": len(rows),
    }


@router.post("/player-market-presence/seed")
def seed_presence(db: Session = Depends(get_db)) -> dict:
    return {"inserted": bi_ops_service.seed_market_presence(db)}


@router.get("/unified-domain-links")
def domain_links(db: Session = Depends(get_db)) -> dict:
    rows = bi_ops_service.list_domain_links(db)
    return {
        "links": [
            {
                "id": r.id,
                "domain_code": r.domain_code,
                "label": r.label,
                "admin_route": r.admin_route,
                "health_path": r.health_path,
                "sort_order": r.sort_order,
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.get("/ops-audit-log")
def audit_log(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)) -> dict:
    rows = bi_ops_service.list_audit(db, limit=limit)
    return {
        "events": [
            {
                "id": r.id,
                "event_type": r.event_type,
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "summary": r.summary,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
        "total": len(rows),
    }
