from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.bi_efficiency import (
    BiAnomalySignalOut,
    BiDataQualityCheckOut,
    BiEfficiencyScorecardOut,
    BiOpsBookmarkIn,
    BiOpsBookmarkOut,
    BiPipelineSyncOut,
    BiScheduledExportIn,
    BiScheduledExportOut,
)
from app.services import bi_efficiency_service

router = APIRouter(prefix="/efficiency", tags=["bi-efficiency"])


@router.get("/scorecard", response_model=BiEfficiencyScorecardOut)
def scorecard(db: Session = Depends(get_db)) -> BiEfficiencyScorecardOut:
    return BiEfficiencyScorecardOut.model_validate(bi_efficiency_service.efficiency_scorecard(db))


@router.get("/data-quality-checks")
def list_dq(db: Session = Depends(get_db)) -> dict:
    rows = bi_efficiency_service.list_dq_checks(db)
    return {"checks": [BiDataQualityCheckOut.model_validate(r) for r in rows], "total": len(rows)}


@router.post("/data-quality-checks/run")
def run_dq(db: Session = Depends(get_db)) -> dict:
    return bi_efficiency_service.run_dq_checks(db)


@router.get("/scheduled-exports")
def list_schedules(db: Session = Depends(get_db)) -> dict:
    rows = bi_efficiency_service.list_scheduled_exports(db)
    return {
        "schedules": [BiScheduledExportOut.model_validate(r) for r in rows],
        "total": len(rows),
    }


@router.post("/scheduled-exports", response_model=BiScheduledExportOut, status_code=status.HTTP_201_CREATED)
def create_schedule(body: BiScheduledExportIn, db: Session = Depends(get_db)) -> BiScheduledExportOut:
    return BiScheduledExportOut.model_validate(bi_efficiency_service.create_scheduled_export(db, body))


@router.post("/scheduled-exports/tick")
def tick_schedules(db: Session = Depends(get_db)) -> dict:
    return bi_efficiency_service.tick_scheduled_exports(db)


@router.get("/anomaly-signals")
def list_anomalies(status: str | None = Query(None), db: Session = Depends(get_db)) -> dict:
    rows = bi_efficiency_service.list_anomalies(db, status=status)
    return {
        "signals": [BiAnomalySignalOut.model_validate(r) for r in rows],
        "total": len(rows),
    }


@router.post("/anomaly-signals/scan")
def scan_anomalies(db: Session = Depends(get_db)) -> dict:
    return bi_efficiency_service.scan_anomalies(db)


@router.get("/bookmarks")
def list_bookmarks(owner_id: str | None = Query(None), db: Session = Depends(get_db)) -> dict:
    rows = bi_efficiency_service.list_bookmarks(db, owner_id=owner_id)
    return {"bookmarks": [BiOpsBookmarkOut.model_validate(r) for r in rows], "total": len(rows)}


@router.post("/bookmarks", response_model=BiOpsBookmarkOut, status_code=status.HTTP_201_CREATED)
def create_bookmark(body: BiOpsBookmarkIn, db: Session = Depends(get_db)) -> BiOpsBookmarkOut:
    return BiOpsBookmarkOut.model_validate(bi_efficiency_service.create_bookmark(db, body))


@router.get("/pipeline-sync", response_model=list[BiPipelineSyncOut])
def pipeline_sync(db: Session = Depends(get_db)) -> list[BiPipelineSyncOut]:
    rows = bi_efficiency_service.list_pipeline_sync(db)
    return [BiPipelineSyncOut.model_validate(r) for r in rows]


@router.post("/pipeline-sync/refresh")
def refresh_pipeline(db: Session = Depends(get_db)) -> dict:
    return bi_efficiency_service.refresh_pipeline_lag(db)


@router.post("/seed")
def seed_efficiency(db: Session = Depends(get_db)) -> dict:
    return bi_efficiency_service.seed_efficiency(db)
