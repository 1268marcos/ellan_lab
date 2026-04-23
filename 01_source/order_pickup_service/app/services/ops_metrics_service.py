from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ops_action_audit import OpsActionAudit
from app.models.reconciliation_pending import ReconciliationPending


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def build_ops_metrics(
    *,
    db: Session,
    lookback_hours: int = 24,
    pending_open_threshold: int = 10,
    error_rate_threshold: float = 0.25,
    failed_final_threshold: int = 1,
) -> dict:
    now = _utc_now()
    window_start = now - timedelta(hours=max(int(lookback_hours or 24), 1))

    total_actions = int(
        db.query(func.count(OpsActionAudit.id))
        .filter(OpsActionAudit.created_at >= window_start)
        .scalar()
        or 0
    )
    success_actions = int(
        db.query(func.count(OpsActionAudit.id))
        .filter(
            OpsActionAudit.created_at >= window_start,
            OpsActionAudit.result == "SUCCESS",
        )
        .scalar()
        or 0
    )
    error_actions = int(
        db.query(func.count(OpsActionAudit.id))
        .filter(
            OpsActionAudit.created_at >= window_start,
            OpsActionAudit.result == "ERROR",
        )
        .scalar()
        or 0
    )
    error_rate = (float(error_actions) / float(total_actions)) if total_actions > 0 else 0.0

    recon_actions = int(
        db.query(func.count(OpsActionAudit.id))
        .filter(
            OpsActionAudit.created_at >= window_start,
            OpsActionAudit.action.in_(
                [
                    "OPS_RECONCILE_ORDER",
                    "OPS_RECON_PENDING_RUN_ONCE",
                    "SYSTEM_RECON_RETRY_PROCESS",
                ]
            ),
        )
        .scalar()
        or 0
    )

    pending_open_rows = (
        db.query(ReconciliationPending)
        .filter(ReconciliationPending.status.in_(["PENDING", "FAILED", "PROCESSING"]))
        .all()
    )
    pending_open_count = len(pending_open_rows)
    pending_failed_final_count = int(
        db.query(func.count(ReconciliationPending.id))
        .filter(ReconciliationPending.status == "FAILED_FINAL")
        .scalar()
        or 0
    )
    pending_due_retry_count = int(
        db.query(func.count(ReconciliationPending.id))
        .filter(
            ReconciliationPending.status == "FAILED",
            ReconciliationPending.next_retry_at.is_not(None),
            ReconciliationPending.next_retry_at <= now,
        )
        .scalar()
        or 0
    )
    stale_cutoff = now - timedelta(minutes=5)
    pending_processing_stale_count = int(
        db.query(func.count(ReconciliationPending.id))
        .filter(
            ReconciliationPending.status == "PROCESSING",
            ReconciliationPending.processing_started_at.is_not(None),
            ReconciliationPending.processing_started_at <= stale_cutoff,
        )
        .scalar()
        or 0
    )

    avg_open_pending_age_min = 0.0
    if pending_open_rows:
        ages = []
        for row in pending_open_rows:
            created_at = _as_aware_utc(row.created_at)
            if not created_at:
                continue
            ages.append(max((now - created_at).total_seconds() / 60.0, 0.0))
        if ages:
            avg_open_pending_age_min = round(sum(ages) / len(ages), 2)

    alerts: list[dict] = []
    if pending_open_count >= int(pending_open_threshold or 10):
        alerts.append(
            {
                "severity": "WARN",
                "code": "PENDING_BACKLOG_HIGH",
                "message": "Backlog de pendências de reconciliação acima do threshold.",
                "value": pending_open_count,
                "threshold": int(pending_open_threshold or 10),
            }
        )
    if total_actions >= 5 and error_rate >= float(error_rate_threshold or 0.25):
        alerts.append(
            {
                "severity": "HIGH",
                "code": "OPS_ERROR_RATE_HIGH",
                "message": "Taxa de erro operacional acima do threshold da janela.",
                "value": round(error_rate, 4),
                "threshold": float(error_rate_threshold or 0.25),
            }
        )
    if pending_failed_final_count >= int(failed_final_threshold or 1):
        alerts.append(
            {
                "severity": "HIGH",
                "code": "PENDING_FAILED_FINAL",
                "message": "Existem pendências em estado final de falha.",
                "value": pending_failed_final_count,
                "threshold": int(failed_final_threshold or 1),
            }
        )
    if pending_processing_stale_count > 0:
        alerts.append(
            {
                "severity": "WARN",
                "code": "PENDING_PROCESSING_STALE",
                "message": "Existem pendências presas em PROCESSING há mais de 5 minutos.",
                "value": pending_processing_stale_count,
                "threshold": 0,
            }
        )

    return {
        "window": {
            "lookback_hours": int(lookback_hours or 24),
            "from": window_start.isoformat(),
            "to": now.isoformat(),
        },
        "kpis": {
            "total_ops_actions": total_actions,
            "success_actions": success_actions,
            "error_actions": error_actions,
            "error_rate": round(error_rate, 4),
            "reconciliation_actions": recon_actions,
            "pending_open_count": pending_open_count,
            "pending_due_retry_count": pending_due_retry_count,
            "pending_processing_stale_count": pending_processing_stale_count,
            "pending_failed_final_count": pending_failed_final_count,
            "avg_open_pending_age_min": avg_open_pending_age_min,
        },
        "alerts": alerts,
    }
