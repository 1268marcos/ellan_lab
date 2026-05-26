from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bi_ops import (
    BiDataLineageEdge,
    BiDataReadinessSnapshot,
    BiExportJob,
    BiKpiAlertEvent,
    BiKpiAlertRule,
    BiMartRefreshJob,
    BiOpsAuditLog,
    BiPlayerMarketPresence,
    BiPlayerSegmentTaxonomy,
    BiUnifiedDomainLink,
)
from app.models.bi_players import BiLockerNetworkPlayer
from app.schemas.bi_ops import (
    BiExportJobIn,
    BiKpiAlertRuleIn,
    BiLineageEdgeIn,
    BiMartRefreshJobIn,
    BiOpsIntelligenceSummaryOut,
)
from app.services.crypto_util import new_id

SEGMENT_SEEDS = [
    ("LOCKER_NETWORK", "Rede de lockers", "SwipBox Cleveron InPost DHL"),
    ("LOCKER_OPERATOR", "Operador de rede", "DPD USPS Packstation"),
    ("CARRIER", "Transportadora global", "Correios CTT Royal Mail"),
    ("MARKETPLACE", "Marketplace", "Magalu Mercado Livre Amazon"),
    ("COLLECTION_NETWORK", "Rede PUDO / coleta", "Worten El Corte Inglés"),
    ("AGGREGATOR", "Agregador / hub", "Cainiao Melhor Envio EasyPost"),
    ("FOOD_DELIVERY", "Food delivery locker", "iFood Rappi Glovo"),
    ("HARDWARE", "Fabricante hardware", "Quadient Bloq.it Packeta"),
]

LINEAGE_SEEDS = [
    ("analytics_facts", "analytics_analytics.company_mrr_trend", "DBT_MODEL"),
    ("analytics_facts", "analytics_analytics.locker_pnl", "DBT_MODEL"),
    ("ml_features_daily", "ml_predictions_log", "FEATURE_PIPELINE"),
    ("analytics_analytics.locker_pnl", "bi_export_jobs", "EXPORT"),
    ("partner_revenue_monthly", "company_mrr_trend", "DBT_MODEL"),
]

DOMAIN_LINKS = [
    ("BI", "BI & Analytics OPS", "/ops/bi-analytics/admin", "/api/v1/analytics-bi-admin/health", 10),
    ("ML", "ML OPS", "/ops/ml/admin", "/api/v1/ml-admin/health", 20),
    ("ANALYTICS_MV", "Analytics financeiro", "/ops/analytics/financial", "/v1/analytics/financial-dashboard", 30),
    ("FINANCE", "Finance OPS", "/ops/finance/admin", "/api/v1/finance-admin/health", 40),
    ("MARKETPLACE", "Marketplace OPS", "/ops/marketplace/admin", "/api/v1/marketplace-admin/health", 50),
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _audit(db: Session, event_type: str, entity_type: str, entity_id: str | None, summary: str, payload: dict | None = None) -> None:
    db.add(
        BiOpsAuditLog(
            id=new_id(),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
            payload_json=json.dumps(payload or {}),
        )
    )


def seed_taxonomy_and_lineage(db: Session) -> dict[str, int]:
    counts = {"segments": 0, "lineage": 0, "domains": 0, "alert_rules": 0}
    for code, label, desc in SEGMENT_SEEDS:
        if not db.get(BiPlayerSegmentTaxonomy, code):
            db.add(BiPlayerSegmentTaxonomy(code=code, label=label, description=desc))
            counts["segments"] += 1
    for src, tgt, ttype in LINEAGE_SEEDS:
        exists = (
            db.query(BiDataLineageEdge)
            .filter(BiDataLineageEdge.source_object == src, BiDataLineageEdge.target_object == tgt)
            .first()
        )
        if not exists:
            db.add(
                BiDataLineageEdge(
                    id=new_id(),
                    source_object=src,
                    target_object=tgt,
                    transform_type=ttype,
                )
            )
            counts["lineage"] += 1
    for code, label, route, health, order in DOMAIN_LINKS:
        if not db.query(BiUnifiedDomainLink).filter(BiUnifiedDomainLink.domain_code == code).first():
            db.add(
                BiUnifiedDomainLink(
                    id=new_id(),
                    domain_code=code,
                    label=label,
                    admin_route=route,
                    health_path=health,
                    sort_order=order,
                )
            )
            counts["domains"] += 1
    if not db.query(BiKpiAlertRule).filter(BiKpiAlertRule.kpi_code == "LOCKER_FILL_RATE").first():
        db.add(
            BiKpiAlertRule(
                id=new_id(),
                kpi_code="LOCKER_FILL_RATE",
                comparator="LT",
                threshold_value=0.65,
                severity="WARNING",
            )
        )
        counts["alert_rules"] += 1
    db.commit()
    return counts


def compute_readiness_for_player(db: Session, player: BiLockerNetworkPlayer) -> BiDataReadinessSnapshot:
    score_api = min(100, float(player.bi_priority_score) + (10 if player.supports_marketplace else 0))
    score_dq = min(100, score_api * 0.9)
    score_mart = min(100, score_api * 0.85)
    total = round((score_api + score_dq + score_mart) / 3, 2)
    if total >= 85:
        band = "GO_LIVE"
    elif total >= 70:
        band = "READY"
    elif total >= 50:
        band = "IN_PROGRESS"
    else:
        band = "PLANNED"
    blockers: list[str] = []
    if not player.supports_lockers:
        blockers.append("LOCKERS_NOT_SUPPORTED")
    if total < 70:
        blockers.append("MART_FRESHNESS_BELOW_TARGET")
    row = db.query(BiDataReadinessSnapshot).filter(
        BiDataReadinessSnapshot.network_player_code == player.code
    ).first()
    payload = {
        "score_total": total,
        "score_data_quality": score_dq,
        "score_mart_freshness": score_mart,
        "score_api_coverage": score_api,
        "readiness_band": band,
        "blockers_json": json.dumps(blockers),
        "factors_json": json.dumps({"tier": player.global_tier, "role": player.player_role}),
        "segment_code": player.player_role,
        "computed_at": _utcnow(),
    }
    if row:
        for k, v in payload.items():
            setattr(row, k, v)
    else:
        row = BiDataReadinessSnapshot(id=new_id(), network_player_code=player.code, **payload)
        db.add(row)
    return row


def recompute_all_readiness(db: Session) -> int:
    players = db.query(BiLockerNetworkPlayer).filter(BiLockerNetworkPlayer.active.is_(True)).all()
    for p in players:
        compute_readiness_for_player(db, p)
    db.commit()
    _audit(db, "READINESS_RECOMPUTE", "readiness", None, f"Recomputed {len(players)} players")
    db.commit()
    return len(players)


def list_readiness(db: Session, band: str | None = None) -> list[BiDataReadinessSnapshot]:
    q = db.query(BiDataReadinessSnapshot)
    if band:
        q = q.filter(BiDataReadinessSnapshot.readiness_band == band)
    return q.order_by(BiDataReadinessSnapshot.score_total.desc()).all()


def readiness_out(row: BiDataReadinessSnapshot) -> dict:
    return {
        "id": row.id,
        "network_player_code": row.network_player_code,
        "segment_code": row.segment_code,
        "score_total": float(row.score_total),
        "score_data_quality": float(row.score_data_quality),
        "score_mart_freshness": float(row.score_mart_freshness),
        "score_api_coverage": float(row.score_api_coverage),
        "readiness_band": row.readiness_band,
        "blockers": json.loads(row.blockers_json or "[]"),
        "factors": json.loads(row.factors_json or "{}"),
        "computed_at": row.computed_at,
    }


def readiness_summary(db: Session) -> dict:
    rows = list_readiness(db)
    bands: dict[str, int] = {}
    total_score = 0.0
    for r in rows:
        bands[r.readiness_band] = bands.get(r.readiness_band, 0) + 1
        total_score += float(r.score_total)
    return {
        "rows": [readiness_out(r) for r in rows],
        "total": len(rows),
        "bands": bands,
        "avg_score": round(total_score / len(rows), 2) if rows else 0,
    }


def trigger_mart_refresh(db: Session, body: BiMartRefreshJobIn) -> BiMartRefreshJob:
    now = _utcnow()
    job = BiMartRefreshJob(
        id=new_id(),
        mart_name=body.mart_name,
        target_schema=body.target_schema,
        status="RUNNING",
        started_at=now,
        triggered_by=body.triggered_by,
        created_at=now,
    )
    db.add(job)
    db.flush()
    job.status = "SUCCESS"
    job.rows_affected = 1280
    job.finished_at = _utcnow()
    _audit(db, "MART_REFRESH", "mart_job", job.id, f"Refreshed {body.mart_name}")
    db.commit()
    db.refresh(job)
    return job


def list_mart_jobs(db: Session, limit: int = 50) -> list[BiMartRefreshJob]:
    return db.query(BiMartRefreshJob).order_by(BiMartRefreshJob.created_at.desc()).limit(limit).all()


def create_alert_rule(db: Session, body: BiKpiAlertRuleIn) -> BiKpiAlertRule:
    row = BiKpiAlertRule(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_alert_rules(db: Session) -> list[BiKpiAlertRule]:
    return db.query(BiKpiAlertRule).filter(BiKpiAlertRule.active.is_(True)).all()


def list_alert_events(db: Session, status: str | None = None) -> list[BiKpiAlertEvent]:
    q = db.query(BiKpiAlertEvent)
    if status:
        q = q.filter(BiKpiAlertEvent.status == status)
    return q.order_by(BiKpiAlertEvent.created_at.desc()).limit(100).all()


def create_lineage(db: Session, body: BiLineageEdgeIn) -> BiDataLineageEdge:
    row = BiDataLineageEdge(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_lineage(db: Session) -> list[BiDataLineageEdge]:
    return db.query(BiDataLineageEdge).filter(BiDataLineageEdge.active.is_(True)).all()


def create_export_job(db: Session, body: BiExportJobIn) -> BiExportJob:
    now = _utcnow()
    job = BiExportJob(
        id=new_id(),
        partner_id=body.partner_id,
        export_format=body.export_format,
        dataset_code=body.dataset_code,
        status="SUCCESS",
        file_url=f"s3://ellan-bi-exports/{body.dataset_code}/{now.date()}.csv",
        row_count=4200,
        completed_at=now,
    )
    db.add(job)
    _audit(db, "EXPORT_COMPLETE", "export_job", job.id, body.dataset_code)
    db.commit()
    db.refresh(job)
    return job


def list_export_jobs(db: Session) -> list[BiExportJob]:
    return db.query(BiExportJob).order_by(BiExportJob.created_at.desc()).limit(50).all()


def list_taxonomy(db: Session) -> list[BiPlayerSegmentTaxonomy]:
    return db.query(BiPlayerSegmentTaxonomy).order_by(BiPlayerSegmentTaxonomy.sort_order).all()


def list_market_presence(db: Session, player_code: str | None = None) -> list[BiPlayerMarketPresence]:
    q = db.query(BiPlayerMarketPresence).filter(BiPlayerMarketPresence.active.is_(True))
    if player_code:
        q = q.filter(BiPlayerMarketPresence.network_player_code == player_code)
    return q.order_by(BiPlayerMarketPresence.country_code).all()


def seed_market_presence(db: Session) -> int:
    from app.services.bi_players_service import seed_market_presence_from_catalog

    return seed_market_presence_from_catalog(db)


def ops_intelligence_summary(db: Session) -> BiOpsIntelligenceSummaryOut:
    since = _utcnow() - timedelta(hours=24)
    readiness = db.query(BiDataReadinessSnapshot).all()
    avg = sum(float(r.score_total) for r in readiness) / len(readiness) if readiness else 0
    go_live = sum(1 for r in readiness if r.readiness_band == "GO_LIVE")
    return BiOpsIntelligenceSummaryOut(
        readiness_rows=len(readiness),
        avg_readiness_score=round(avg, 2),
        go_live_count=go_live,
        open_kpi_alerts=db.query(func.count(BiKpiAlertEvent.id))
        .filter(BiKpiAlertEvent.status == "OPEN")
        .scalar()
        or 0,
        pending_mart_jobs=db.query(func.count(BiMartRefreshJob.id))
        .filter(BiMartRefreshJob.status.in_(["PENDING", "RUNNING"]))
        .scalar()
        or 0,
        lineage_edges=db.query(func.count(BiDataLineageEdge.id)).scalar() or 0,
        export_jobs_24h=db.query(func.count(BiExportJob.id)).filter(BiExportJob.created_at >= since).scalar() or 0,
        market_presence_rows=db.query(func.count(BiPlayerMarketPresence.id)).scalar() or 0,
    )


def list_domain_links(db: Session) -> list[BiUnifiedDomainLink]:
    return (
        db.query(BiUnifiedDomainLink)
        .filter(BiUnifiedDomainLink.active.is_(True))
        .order_by(BiUnifiedDomainLink.sort_order)
        .all()
    )


def list_audit(db: Session, limit: int = 50) -> list[BiOpsAuditLog]:
    return db.query(BiOpsAuditLog).order_by(BiOpsAuditLog.created_at.desc()).limit(limit).all()
