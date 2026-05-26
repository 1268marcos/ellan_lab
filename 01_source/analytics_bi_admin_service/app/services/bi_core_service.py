from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bi_core import AnalyticsFact, BiKpiDefinition, BiReportCatalog
from app.models.bi_marts import CompanyMrrTrend, LockerPnl, PartnerRevenueMonthly
from app.models.bi_partners import BiDataPartner
from app.models.bi_players import BiLockerNetworkPlayer, BiPlayerRelation
from app.models.bi_webhooks import BiCapabilityWebhook
from app.models.bi_ops import (
    BiDataLineageEdge,
    BiDataReadinessSnapshot,
    BiExportJob,
    BiKpiAlertEvent,
    BiMartRefreshJob,
    BiPlayerMarketPresence,
)
from app.schemas.bi_core import (
    AnalyticsFactIn,
    BiDashboardOut,
    BiKpiDefinitionIn,
    BiReportCatalogIn,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _payload_dict(payload) -> dict:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        return json.loads(payload)
    return {}


def list_facts(db: Session, limit: int = 100, order_id: str | None = None) -> list[AnalyticsFact]:
    q = db.query(AnalyticsFact)
    if order_id:
        q = q.filter(AnalyticsFact.order_id == order_id)
    return q.order_by(AnalyticsFact.occurred_at.desc()).limit(limit).all()


def create_fact(db: Session, body: AnalyticsFactIn) -> AnalyticsFact:
    if db.query(AnalyticsFact).filter(AnalyticsFact.fact_key == body.fact_key).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="fact_key_exists")
    payload_val: dict | str = body.payload
    url = str(db.get_bind().url)
    if url.startswith("sqlite"):
        payload_val = json.dumps(body.payload)
    row = AnalyticsFact(
        id=uuid.uuid4(),
        fact_key=body.fact_key,
        fact_name=body.fact_name,
        order_id=body.order_id,
        order_channel=body.order_channel,
        region_code=body.region_code,
        slot_id=body.slot_id,
        payload=payload_val,
        occurred_at=body.occurred_at,
        created_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_fact(db: Session, fact_id: uuid.UUID) -> None:
    row = db.get(AnalyticsFact, fact_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="fact_not_found")
    db.delete(row)
    db.commit()


def list_kpis(db: Session) -> list[BiKpiDefinition]:
    return db.query(BiKpiDefinition).order_by(BiKpiDefinition.code).all()


def create_kpi(db: Session, body: BiKpiDefinitionIn) -> BiKpiDefinition:
    if db.query(BiKpiDefinition).filter(BiKpiDefinition.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="kpi_code_exists")
    row = BiKpiDefinition(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_reports(db: Session) -> list[BiReportCatalog]:
    return db.query(BiReportCatalog).order_by(BiReportCatalog.code).all()


def create_report(db: Session, body: BiReportCatalogIn) -> BiReportCatalog:
    if db.query(BiReportCatalog).filter(BiReportCatalog.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="report_code_exists")
    row = BiReportCatalog(
        id=new_id(),
        code=body.code,
        name=body.name,
        report_type=body.report_type,
        metabase_dashboard_id=body.metabase_dashboard_id,
        description=body.description,
        tags_json=json.dumps(body.tags),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def dashboard(db: Session) -> BiDashboardOut:
    since = _utcnow() - timedelta(hours=24)
    facts_count = db.query(func.count(AnalyticsFact.id)).scalar() or 0
    facts_24h = (
        db.query(func.count(AnalyticsFact.id)).filter(AnalyticsFact.occurred_at >= since).scalar() or 0
    )
    mrr_rows = db.query(func.count()).select_from(CompanyMrrTrend).scalar() or 0
    pnl_rows = db.query(func.count()).select_from(LockerPnl).scalar() or 0
    rev_rows = db.query(func.count()).select_from(PartnerRevenueMonthly).scalar() or 0
    open_months = db.query(func.count(func.distinct(CompanyMrrTrend.month_ref))).scalar() or 0
    readiness_rows = db.query(BiDataReadinessSnapshot).all()
    readiness_go = sum(1 for r in readiness_rows if r.readiness_band == "GO_LIVE")
    readiness_avg = (
        sum(float(r.score_total) for r in readiness_rows) / len(readiness_rows) if readiness_rows else 0
    )
    since = _utcnow() - timedelta(hours=24)
    return BiDashboardOut(
        facts_count=int(facts_count),
        facts_24h=int(facts_24h),
        partners=db.query(func.count(BiDataPartner.id)).scalar() or 0,
        kpi_definitions=db.query(func.count(BiKpiDefinition.id)).scalar() or 0,
        report_catalog=db.query(func.count(BiReportCatalog.id)).scalar() or 0,
        network_players=db.query(func.count(BiLockerNetworkPlayer.id)).scalar() or 0,
        player_relations=db.query(func.count(BiPlayerRelation.id)).scalar() or 0,
        mrr_rows=int(mrr_rows),
        locker_pnl_rows=int(pnl_rows),
        partner_revenue_rows=int(rev_rows),
        capability_webhooks=db.query(func.count(BiCapabilityWebhook.id)).scalar() or 0,
        open_marts_months=int(open_months),
        readiness_rows=len(readiness_rows),
        readiness_go_live=readiness_go,
        readiness_avg_score=round(readiness_avg, 2),
        open_kpi_alerts=db.query(func.count(BiKpiAlertEvent.id))
        .filter(BiKpiAlertEvent.status == "OPEN")
        .scalar()
        or 0,
        mart_jobs_pending=db.query(func.count(BiMartRefreshJob.id))
        .filter(BiMartRefreshJob.status.in_(["PENDING", "RUNNING"]))
        .scalar()
        or 0,
        lineage_edges=db.query(func.count(BiDataLineageEdge.id)).scalar() or 0,
        market_presence_rows=db.query(func.count(BiPlayerMarketPresence.id)).scalar() or 0,
        export_jobs_24h=db.query(func.count(BiExportJob.id)).filter(BiExportJob.created_at >= since).scalar() or 0,
    )


def fact_out(row: AnalyticsFact) -> dict:
    data = {
        "id": row.id,
        "fact_key": row.fact_key,
        "fact_name": row.fact_name,
        "order_id": row.order_id,
        "order_channel": row.order_channel,
        "region_code": row.region_code,
        "slot_id": row.slot_id,
        "payload": _payload_dict(row.payload),
        "occurred_at": row.occurred_at,
        "created_at": row.created_at,
    }
    return data
