from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.allocation import Allocation, AllocationState
from app.models.credit import Credit, CreditStatus
from app.models.reconciliation_pending import ReconciliationPending

OPS_MONITORING_ROLES = frozenset({"admin_operacao", "auditoria", "suporte"})

_ACTIVE_ALLOCATION_STATES = (
    AllocationState.RESERVED_PENDING_PAYMENT,
    AllocationState.RESERVED_PAID_PENDING_PICKUP,
    AllocationState.OPENED_FOR_PICKUP,
    AllocationState.FRAUD_REVIEW,
    AllocationState.ERROR,
    AllocationState.MAINTENANCE,
)

_OPEN_RECON_STATUSES = ("PENDING", "FAILED", "PROCESSING")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _start_of_utc_day(ref: datetime) -> datetime:
    r = ref.astimezone(timezone.utc) if ref.tzinfo else ref.replace(tzinfo=timezone.utc)
    return r.replace(hour=0, minute=0, second=0, microsecond=0)


def _as_aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    aware = _as_aware_utc(value)
    return aware.isoformat() if aware else None


def fetch_credits_health(
    db: Session,
    *,
    expiring_within_days: int = 7,
    top_users_limit: int = 10,
) -> dict[str, Any]:
    now = _utc_now()
    day_start = _start_of_utc_day(now)
    expiring_before = now + timedelta(days=max(int(expiring_within_days), 1))

    total_credits = int(db.query(func.count(Credit.id)).scalar() or 0)

    used_today = int(
        db.query(func.count(Credit.id))
        .filter(
            Credit.status == CreditStatus.USED,
            Credit.used_at.isnot(None),
            Credit.used_at >= day_start,
        )
        .scalar()
        or 0
    )

    expired_today = int(
        db.query(func.count(Credit.id))
        .filter(
            Credit.status == CreditStatus.EXPIRED,
            Credit.updated_at >= day_start,
        )
        .scalar()
        or 0
    )

    by_status_rows = (
        db.query(Credit.status, func.count(Credit.id))
        .group_by(Credit.status)
        .all()
    )
    by_status = {
        str(getattr(row[0], "value", row[0])): int(row[1] or 0) for row in by_status_rows
    }

    top_rows = (
        db.query(
            Credit.user_id,
            func.count(Credit.id).label("credits_count"),
            func.min(Credit.expires_at).label("nearest_expires_at"),
            func.sum(Credit.amount_cents).label("total_amount_cents"),
        )
        .filter(
            Credit.status == CreditStatus.AVAILABLE,
            Credit.user_id.isnot(None),
            Credit.expires_at > now,
            Credit.expires_at <= expiring_before,
        )
        .group_by(Credit.user_id)
        .order_by(func.count(Credit.id).desc(), func.min(Credit.expires_at).asc())
        .limit(max(int(top_users_limit), 1))
        .all()
    )

    top_users_expiring = [
        {
            "user_id": str(row.user_id),
            "credits_count": int(row.credits_count or 0),
            "nearest_expires_at": _iso(row.nearest_expires_at),
            "total_amount_cents": int(row.total_amount_cents or 0),
        }
        for row in top_rows
        if row.user_id
    ]

    available_expiring_soon = int(
        db.query(func.count(Credit.id))
        .filter(
            Credit.status == CreditStatus.AVAILABLE,
            Credit.expires_at > now,
            Credit.expires_at <= expiring_before,
        )
        .scalar()
        or 0
    )

    return {
        "ok": True,
        "as_of": now.isoformat(),
        "period_utc_day_start": day_start.isoformat(),
        "total_credits": total_credits,
        "used_today": used_today,
        "expired_today": expired_today,
        "available_expiring_within_days": available_expiring_soon,
        "expiring_within_days": int(expiring_within_days),
        "by_status": by_status,
        "top_users_expiring": top_users_expiring,
    }


def fetch_reconciliation_lag(db: Session) -> dict[str, Any]:
    now = _utc_now()

    status_rows = (
        db.query(ReconciliationPending.status, func.count(ReconciliationPending.id))
        .group_by(ReconciliationPending.status)
        .all()
    )
    status_distribution = {
        str(row[0] or "UNKNOWN").upper(): int(row[1] or 0) for row in status_rows
    }

    open_rows = (
        db.query(ReconciliationPending)
        .filter(ReconciliationPending.status.in_(_OPEN_RECON_STATUSES))
        .all()
    )

    ages_sec: list[float] = []
    oldest: dict[str, Any] | None = None
    max_age_sec = 0.0

    for row in open_rows:
        created = _as_aware_utc(row.created_at)
        if not created:
            continue
        age_sec = max(0.0, (now - created).total_seconds())
        ages_sec.append(age_sec)
        if age_sec >= max_age_sec:
            max_age_sec = age_sec
            oldest = {
                "pending_id": row.id,
                "order_id": row.order_id,
                "reason": row.reason,
                "status": row.status,
                "created_at": _iso(created),
                "age_sec": int(age_sec),
                "attempt_count": int(row.attempt_count or 0),
            }

    avg_pending_age_sec = round(sum(ages_sec) / len(ages_sec), 2) if ages_sec else 0.0
    open_count = len(open_rows)

    stale_processing_cutoff = now - timedelta(minutes=5)
    stale_processing_count = int(
        db.query(func.count(ReconciliationPending.id))
        .filter(
            ReconciliationPending.status == "PROCESSING",
            ReconciliationPending.processing_started_at.isnot(None),
            ReconciliationPending.processing_started_at <= stale_processing_cutoff,
        )
        .scalar()
        or 0
    )

    alert = max_age_sec > 3600 or stale_processing_count > 0

    return {
        "ok": True,
        "as_of": now.isoformat(),
        "open_pending_count": open_count,
        "avg_pending_age_sec": avg_pending_age_sec,
        "max_pending_age_sec": int(max_age_sec),
        "oldest_open": oldest,
        "status_distribution": status_distribution,
        "stale_processing_count": stale_processing_count,
        "alert": alert,
    }


def fetch_runtime_deadlocks(
    db: Session,
    *,
    lock_age_sec: int = 3600,
    limit: int = 100,
) -> dict[str, Any]:
    now = _utc_now()
    cutoff = now - timedelta(seconds=max(int(lock_age_sec), 60))
    cutoff_naive = cutoff.replace(tzinfo=None)

    try:
        rows = (
            db.query(Allocation)
            .filter(
                Allocation.state.in_(_ACTIVE_ALLOCATION_STATES),
                Allocation.updated_at <= cutoff_naive,
            )
            .order_by(Allocation.updated_at.asc())
            .limit(max(int(limit), 1))
            .all()
        )
    except Exception as exc:
        return {
            "ok": True,
            "as_of": now.isoformat(),
            "lock_age_threshold_sec": int(lock_age_sec),
            "stuck_count": 0,
            "items": [],
            "alert": False,
            "skipped": True,
            "message": f"allocations indisponível: {exc.__class__.__name__}",
        }

    items: list[dict[str, Any]] = []
    for alloc in rows:
        updated = alloc.updated_at
        if updated and getattr(updated, "tzinfo", None) is None:
            updated_aware = updated.replace(tzinfo=timezone.utc)
        else:
            updated_aware = _as_aware_utc(updated) if updated else None
        age_sec = int(max(0.0, (now - updated_aware).total_seconds())) if updated_aware else None

        locked_until = alloc.locked_until
        lock_expired = False
        if locked_until is not None:
            lu = (
                locked_until.replace(tzinfo=timezone.utc)
                if locked_until.tzinfo is None
                else locked_until.astimezone(timezone.utc)
            )
            lock_expired = lu < now

        items.append(
            {
                "allocation_id": alloc.id,
                "order_id": alloc.order_id,
                "locker_id": alloc.locker_id,
                "slot": int(alloc.slot),
                "state": str(getattr(alloc.state, "value", alloc.state)),
                "locked_until": _iso(locked_until) if locked_until else None,
                "lock_expired": lock_expired,
                "updated_at": _iso(updated),
                "age_sec": age_sec,
            }
        )

    return {
        "ok": True,
        "as_of": now.isoformat(),
        "lock_age_threshold_sec": int(lock_age_sec),
        "stuck_count": len(items),
        "items": items,
        "alert": len(items) > 0,
    }


def fetch_ops_monitoring_summary(db: Session) -> dict[str, Any]:
    credits = fetch_credits_health(db)
    reconciliation = fetch_reconciliation_lag(db)
    runtime = fetch_runtime_deadlocks(db)

    alerts: list[dict[str, str]] = []
    if reconciliation.get("alert"):
        alerts.append(
            {
                "code": "RECONCILIATION_LAG",
                "severity": "HIGH",
                "message": "Pendências de reconciliação acima do limite ou PROCESSING obsoleto.",
            }
        )
    if runtime.get("alert"):
        alerts.append(
            {
                "code": "RUNTIME_ALLOCATION_STUCK",
                "severity": "HIGH",
                "message": "Alocações ativas sem progresso há mais de 1 hora.",
            }
        )
    if int(credits.get("available_expiring_within_days") or 0) > 0:
        alerts.append(
            {
                "code": "CREDITS_EXPIRING_SOON",
                "severity": "MEDIUM",
                "message": "Créditos AVAILABLE expirando nos próximos dias.",
            }
        )

    overall_ok = not any(a["severity"] == "HIGH" for a in alerts)

    return {
        "ok": overall_ok,
        "as_of": _utc_now().isoformat(),
        "alerts": alerts,
        "credits_health": credits,
        "reconciliation_lag": reconciliation,
        "runtime_deadlocks": runtime,
    }
