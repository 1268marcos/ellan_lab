from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.bi_core import (
    AnalyticsFactIn,
    AnalyticsFactListOut,
    AnalyticsFactOut,
    BiDashboardOut,
    BiKpiDefinitionIn,
    BiKpiDefinitionListOut,
    BiKpiDefinitionOut,
    BiReportCatalogIn,
    BiReportCatalogListOut,
    BiReportCatalogOut,
    MartListOut,
)
from app.services import bi_core_service, bi_marts_service

router = APIRouter(tags=["bi-analytics-core"])


@router.get("/dashboard", response_model=BiDashboardOut)
def bi_dashboard(db: Session = Depends(get_db)) -> BiDashboardOut:
    return bi_core_service.dashboard(db)


@router.get("/analytics-facts", response_model=AnalyticsFactListOut)
def list_facts(
    limit: int = Query(100, ge=1, le=500),
    order_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> AnalyticsFactListOut:
    rows = bi_core_service.list_facts(db, limit=limit, order_id=order_id)
    items = [AnalyticsFactOut.model_validate(bi_core_service.fact_out(r)) for r in rows]
    return AnalyticsFactListOut(items=items, total=len(items))


@router.post("/analytics-facts", response_model=AnalyticsFactOut, status_code=status.HTTP_201_CREATED)
def create_fact(body: AnalyticsFactIn, db: Session = Depends(get_db)) -> AnalyticsFactOut:
    row = bi_core_service.create_fact(db, body)
    return AnalyticsFactOut.model_validate(bi_core_service.fact_out(row))


@router.delete("/analytics-facts/{fact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fact(fact_id: UUID, db: Session = Depends(get_db)) -> None:
    bi_core_service.delete_fact(db, fact_id)


@router.get("/kpi-definitions", response_model=BiKpiDefinitionListOut)
def list_kpis(db: Session = Depends(get_db)) -> BiKpiDefinitionListOut:
    rows = bi_core_service.list_kpis(db)
    return BiKpiDefinitionListOut(
        items=[BiKpiDefinitionOut.model_validate(r) for r in rows],
        total=len(rows),
    )


@router.post("/kpi-definitions", response_model=BiKpiDefinitionOut, status_code=status.HTTP_201_CREATED)
def create_kpi(body: BiKpiDefinitionIn, db: Session = Depends(get_db)) -> BiKpiDefinitionOut:
    return BiKpiDefinitionOut.model_validate(bi_core_service.create_kpi(db, body))


def _report_out(row) -> dict:
    import json

    return {
        "id": row.id,
        "code": row.code,
        "name": row.name,
        "report_type": row.report_type,
        "metabase_dashboard_id": row.metabase_dashboard_id,
        "description": row.description,
        "tags": json.loads(row.tags_json or "[]"),
        "active": row.active,
        "created_at": row.created_at,
    }


@router.get("/report-catalog", response_model=BiReportCatalogListOut)
def list_reports(db: Session = Depends(get_db)) -> BiReportCatalogListOut:
    rows = bi_core_service.list_reports(db)
    return BiReportCatalogListOut(
        items=[BiReportCatalogOut.model_validate(_report_out(r)) for r in rows],
        total=len(rows),
    )


@router.post("/report-catalog", response_model=BiReportCatalogOut, status_code=status.HTTP_201_CREATED)
def create_report(body: BiReportCatalogIn, db: Session = Depends(get_db)) -> BiReportCatalogOut:
    row = bi_core_service.create_report(db, body)
    return BiReportCatalogOut.model_validate(_report_out(row))


@router.get("/marts", response_model=MartListOut)
def list_marts(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)) -> MartListOut:
    return bi_marts_service.list_marts(db, limit=limit)
