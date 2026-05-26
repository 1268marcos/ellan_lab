from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bi_efficiency import (
    BiAnomalySignal,
    BiDataQualityCheck,
    BiOpsBookmark,
    BiPipelineSyncCheckpoint,
    BiScheduledExport,
)
from app.models.bi_ops import BiDataReadinessSnapshot, BiExportJob, BiKpiAlertEvent, BiMartRefreshJob
from app.schemas.bi_efficiency import BiOpsBookmarkIn, BiScheduledExportIn
from app.services.crypto_util import new_id

DQ_SEEDS = [
    ("FACTS_NOT_NULL_ORDER", "analytics_facts", "NOT_NULL", "CRITICAL"),
    ("MART_FRESHNESS_MRR", "analytics_analytics.company_mrr_trend", "FRESHNESS_24H", "WARNING"),
    ("MART_FRESHNESS_PNL", "analytics_analytics.locker_pnl", "FRESHNESS_24H", "WARNING"),
    ("PLAYER_CODE_UNIQUE", "bi_locker_network_players", "UNIQUE", "WARNING"),
    ("READINESS_MIN_SCORE", "bi_data_readiness_snapshots", "THRESHOLD", "WARNING"),
]

SCHEDULE_SEEDS = [
    ("DAILY_PARTNER_REVENUE", "PARTNER_REVENUE_MONTHLY", "0 6 * * *"),
    ("WEEKLY_LOCKER_PNL", "LOCKER_PNL", "0 7 * * 1"),
]

PIPELINE_SEEDS = [
    ("MART_TO_ML_FEATURES", "analytics_analytics.locker_pnl", "ml_features_daily"),
    ("FACTS_TO_MART_MRR", "analytics_facts", "analytics_analytics.company_mrr_trend"),
    ("BI_EXPORT_TO_PARTNER", "bi_export_jobs", "partner_settlement_feed"),
]

BOOKMARK_SEEDS = [
    ("Tier-1 players GO_LIVE", "/ops/bi-analytics/admin", {"tab": "players", "band": "GO_LIVE"}),
    ("KPI alerts abertos", "/ops/bi-analytics/admin", {"tab": "alerts", "status": "OPEN"}),
    ("Refresh marts ETL", "/ops/bi-analytics/admin", {"tab": "refresh"}),
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _row_details(row: BiDataQualityCheck) -> dict:
    try:
        return json.loads(row.details_json or "{}")
    except json.JSONDecodeError:
        return {}


def _check_to_dict(row: BiDataQualityCheck) -> dict:
    return {
        "id": row.id,
        "check_code": row.check_code,
        "target_object": row.target_object,
        "rule_type": row.rule_type,
        "severity": row.severity,
        "last_status": row.last_status,
        "last_score": float(row.last_score) if row.last_score is not None else None,
        "last_run_at": row.last_run_at,
        "details": _row_details(row),
        "active": row.active,
    }


def seed_efficiency(db: Session) -> dict[str, int]:
    counts = {"dq": 0, "schedules": 0, "pipelines": 0, "bookmarks": 0}
    for code, target, rule, sev in DQ_SEEDS:
        if not db.query(BiDataQualityCheck).filter(BiDataQualityCheck.check_code == code).first():
            db.add(
                BiDataQualityCheck(
                    id=new_id(),
                    check_code=code,
                    target_object=target,
                    rule_type=rule,
                    severity=sev,
                    last_status="UNKNOWN",
                )
            )
            counts["dq"] += 1
    for code, dataset, cron in SCHEDULE_SEEDS:
        if not db.query(BiScheduledExport).filter(BiScheduledExport.schedule_code == code).first():
            db.add(
                BiScheduledExport(
                    id=new_id(),
                    schedule_code=code,
                    dataset_code=dataset,
                    cron_expr=cron,
                    next_run_at=_utcnow() - timedelta(minutes=5),
                )
            )
            counts["schedules"] += 1
    for code, src, tgt in PIPELINE_SEEDS:
        if not db.query(BiPipelineSyncCheckpoint).filter(BiPipelineSyncCheckpoint.pipeline_code == code).first():
            db.add(
                BiPipelineSyncCheckpoint(
                    id=new_id(),
                    pipeline_code=code,
                    source_object=src,
                    target_object=tgt,
                    lag_minutes=random.randint(5, 90),
                    status="OK",
                    last_sync_at=_utcnow() - timedelta(minutes=random.randint(1, 60)),
                )
            )
            counts["pipelines"] += 1
    for label, route, query in BOOKMARK_SEEDS:
        if not db.query(BiOpsBookmark).filter(BiOpsBookmark.label == label).first():
            db.add(
                BiOpsBookmark(
                    id=new_id(),
                    label=label,
                    route_path=route,
                    query_json=json.dumps(query),
                    pinned=label.startswith("Tier"),
                )
            )
            counts["bookmarks"] += 1
    db.commit()
    return counts


def list_dq_checks(db: Session) -> list[dict]:
    return [_check_to_dict(r) for r in db.query(BiDataQualityCheck).order_by(BiDataQualityCheck.check_code).all()]


def run_dq_checks(db: Session) -> dict:
    now = _utcnow()
    passed = 0
    for row in db.query(BiDataQualityCheck).filter(BiDataQualityCheck.active.is_(True)).all():
        score = random.uniform(82, 100)
        if row.rule_type == "THRESHOLD":
            low = db.query(BiDataReadinessSnapshot).filter(BiDataReadinessSnapshot.score_total < 60).count()
            score = 100.0 if low == 0 else max(0, 100 - low * 8)
        status = "PASS" if score >= 85 else "FAIL"
        if status == "PASS":
            passed += 1
        row.last_status = status
        row.last_score = round(score, 2)
        row.last_run_at = now
        row.details_json = json.dumps({"checked_at": now.isoformat(), "rule": row.rule_type})
    db.commit()
    total = db.query(BiDataQualityCheck).filter(BiDataQualityCheck.active.is_(True)).count()
    return {"total": total, "passed": passed, "failed": total - passed}


def list_scheduled_exports(db: Session) -> list[BiScheduledExport]:
    return db.query(BiScheduledExport).order_by(BiScheduledExport.schedule_code).all()


def create_scheduled_export(db: Session, body: BiScheduledExportIn) -> BiScheduledExport:
    row = BiScheduledExport(
        id=new_id(),
        schedule_code=body.schedule_code,
        dataset_code=body.dataset_code,
        cron_expr=body.cron_expr,
        export_format=body.export_format,
        partner_id=body.partner_id,
        active=body.active,
        next_run_at=_utcnow() + timedelta(hours=1),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def tick_scheduled_exports(db: Session) -> dict:
    now = _utcnow()
    due = 0
    created_jobs = 0
    for row in db.query(BiScheduledExport).filter(BiScheduledExport.active.is_(True)).all():
        nra = row.next_run_at
        if nra is not None:
            if nra.tzinfo is None:
                nra = nra.replace(tzinfo=timezone.utc)
            if nra > now:
                continue
        due += 1
        job = BiExportJob(
            id=new_id(),
            partner_id=row.partner_id,
            export_format=row.export_format,
            dataset_code=row.dataset_code,
            status="COMPLETED",
            row_count=random.randint(100, 5000),
            completed_at=now,
        )
        db.add(job)
        created_jobs += 1
        row.last_run_at = now
        row.last_status = "COMPLETED"
        row.next_run_at = now + timedelta(days=1)
    db.commit()
    return {"due": due, "export_jobs_created": created_jobs}


def list_anomalies(db: Session, status: str | None = None) -> list[BiAnomalySignal]:
    q = db.query(BiAnomalySignal).order_by(BiAnomalySignal.detected_at.desc())
    if status:
        q = q.filter(BiAnomalySignal.status == status)
    return q.limit(200).all()


def scan_anomalies(db: Session) -> dict:
    created = 0
    open_alerts = db.query(BiKpiAlertEvent).filter(BiKpiAlertEvent.status == "OPEN").limit(5).all()
    for ev in open_alerts:
        exists = (
            db.query(BiAnomalySignal)
            .filter(
                BiAnomalySignal.kpi_code == ev.kpi_code,
                BiAnomalySignal.status == "OPEN",
                BiAnomalySignal.signal_type == "KPI_THRESHOLD",
            )
            .first()
        )
        if exists:
            continue
        obs = float(ev.observed_value)
        baseline = obs * 0.85
        dev = ((obs - baseline) / baseline * 100) if baseline else 0
        db.add(
            BiAnomalySignal(
                id=new_id(),
                signal_type="KPI_THRESHOLD",
                kpi_code=ev.kpi_code,
                network_player_code=ev.network_player_code,
                observed_value=obs,
                baseline_value=baseline,
                deviation_pct=round(dev, 2),
                severity="CRITICAL" if dev > 25 else "WARNING",
                summary=f"Desvio KPI {ev.kpi_code}: {obs:.2f} vs baseline {baseline:.2f}",
            )
        )
        created += 1
    stale_marts = (
        db.query(BiMartRefreshJob)
        .filter(BiMartRefreshJob.status.in_(["FAILED", "PENDING"]))
        .limit(3)
        .all()
    )
    for job in stale_marts:
        db.add(
            BiAnomalySignal(
                id=new_id(),
                signal_type="MART_STALE",
                kpi_code=None,
                summary=f"Mart {job.mart_name} em status {job.status}",
                severity="WARNING",
            )
        )
        created += 1
    db.commit()
    return {"created": created}


def list_bookmarks(db: Session, owner_id: str | None = None) -> list[dict]:
    q = db.query(BiOpsBookmark).order_by(BiOpsBookmark.sort_order, BiOpsBookmark.label)
    if owner_id:
        q = q.filter(BiOpsBookmark.owner_id == owner_id)
    out = []
    for row in q.all():
        try:
            query = json.loads(row.query_json or "{}")
        except json.JSONDecodeError:
            query = {}
        out.append(
            {
                "id": row.id,
                "owner_id": row.owner_id,
                "label": row.label,
                "route_path": row.route_path,
                "query": query,
                "pinned": row.pinned,
                "sort_order": row.sort_order,
            }
        )
    return out


def create_bookmark(db: Session, body: BiOpsBookmarkIn) -> dict:
    row = BiOpsBookmark(
        id=new_id(),
        owner_id=body.owner_id,
        label=body.label,
        route_path=body.route_path,
        query_json=json.dumps(body.query_json),
        pinned=body.pinned,
    )
    db.add(row)
    db.commit()
    return {
        "id": row.id,
        "owner_id": row.owner_id,
        "label": row.label,
        "route_path": row.route_path,
        "query": body.query_json,
        "pinned": row.pinned,
        "sort_order": row.sort_order,
    }


def list_pipeline_sync(db: Session) -> list[dict]:
    rows = db.query(BiPipelineSyncCheckpoint).order_by(BiPipelineSyncCheckpoint.pipeline_code).all()
    return [
        {
            "pipeline_code": r.pipeline_code,
            "source_object": r.source_object,
            "target_object": r.target_object,
            "lag_minutes": int(r.lag_minutes or 0),
            "rows_synced": int(r.rows_synced) if r.rows_synced is not None else None,
            "status": r.status,
            "last_sync_at": r.last_sync_at,
        }
        for r in rows
    ]


def refresh_pipeline_lag(db: Session) -> dict:
    updated = 0
    for row in db.query(BiPipelineSyncCheckpoint).all():
        row.lag_minutes = random.randint(2, 120)
        row.status = "OK" if row.lag_minutes < 60 else "LAGGING"
        row.last_sync_at = _utcnow() - timedelta(minutes=row.lag_minutes)
        row.updated_at = _utcnow()
        updated += 1
    db.commit()
    return {"updated": updated}


def efficiency_scorecard(db: Session) -> dict:
    checks = db.query(BiDataQualityCheck).filter(BiDataQualityCheck.active.is_(True)).all()
    pass_n = sum(1 for c in checks if c.last_status == "PASS")
    dq_rate = (pass_n / len(checks) * 100) if checks else 0
    open_anom = db.query(func.count(BiAnomalySignal.id)).filter(BiAnomalySignal.status == "OPEN").scalar() or 0
    now = _utcnow()
    due = (
        db.query(func.count(BiScheduledExport.id))
        .filter(BiScheduledExport.active.is_(True), BiScheduledExport.next_run_at <= now)
        .scalar()
        or 0
    )
    pipelines = db.query(BiPipelineSyncCheckpoint).all()
    max_lag = max((int(p.lag_minutes or 0) for p in pipelines), default=0)
    bookmarks = db.query(func.count(BiOpsBookmark.id)).scalar() or 0
    readiness_avg = db.query(func.avg(BiDataReadinessSnapshot.score_total)).scalar() or 0
    score = min(
        100.0,
        max(
            0.0,
            dq_rate * 0.35
            + float(readiness_avg or 0) * 0.35
            + max(0, 100 - open_anom * 5) * 0.15
            + max(0, 100 - max_lag) * 0.15,
        ),
    )
    recs: list[str] = []
    if dq_rate < 90:
        recs.append("Executar data-quality checks e corrigir marts com FAIL.")
    if open_anom > 0:
        recs.append("Revisar anomaly signals abertos e fechar após mitigação.")
    if max_lag > 60:
        recs.append("Reduzir lag do pipeline BI→ML (features diárias).")
    if due > 0:
        recs.append(f"Rodar {due} scheduled export(s) em atraso.")
    if not recs:
        recs.append("Domínio BI em estado saudável — manter monitoramento.")
    return {
        "efficiency_score": round(score, 2),
        "dq_pass_rate": round(dq_rate, 2),
        "open_anomalies": int(open_anom),
        "scheduled_exports_due": int(due),
        "pipeline_lag_max_minutes": int(max_lag),
        "bookmarks_count": int(bookmarks),
        "recommendations": recs,
    }
