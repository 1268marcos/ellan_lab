from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.reconciliation_pending import ReconciliationPending

logger = logging.getLogger(__name__)

DEFAULT_MAX_ATTEMPTS = 5


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _next_retry_at_for(attempt_count: int) -> datetime:
    now = _utc_now()
    if attempt_count <= 1:
        return now + timedelta(seconds=15)
    if attempt_count == 2:
        return now + timedelta(seconds=60)
    if attempt_count == 3:
        return now + timedelta(minutes=5)
    return now + timedelta(minutes=15)


def _dedupe_key(*, order_id: str, reason: str) -> str:
    return f"order:{order_id}:reason:{reason}".strip().lower()


def enqueue_reconciliation_pending(
    *,
    db: Session,
    order_id: str,
    reason: str,
    payload: dict,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> ReconciliationPending:
    order_id_norm = str(order_id or "").strip()
    reason_norm = str(reason or "").strip().lower()
    if not order_id_norm:
        raise ValueError("order_id obrigatório para pendência de reconciliação")
    if not reason_norm:
        raise ValueError("reason obrigatório para pendência de reconciliação")

    key = _dedupe_key(order_id=order_id_norm, reason=reason_norm)
    existing = (
        db.query(ReconciliationPending)
        .filter(ReconciliationPending.dedupe_key == key)
        .first()
    )
    if existing:
        if existing.status in {"DONE", "PROCESSING"}:
            return existing
        existing.payload_json = payload or {}
        existing.status = "PENDING"
        existing.next_retry_at = None
        existing.last_error = None
        existing.updated_at = _utc_now()
        db.flush()
        return existing

    now = _utc_now()
    row = ReconciliationPending(
        id=f"rcp_{uuid4().hex}",
        dedupe_key=key,
        order_id=order_id_norm,
        reason=reason_norm,
        status="PENDING",
        payload_json=payload or {},
        attempt_count=0,
        max_attempts=max(int(max_attempts or DEFAULT_MAX_ATTEMPTS), 1),
        next_retry_at=None,
        processing_started_at=None,
        last_error=None,
        completed_at=None,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.flush()
    logger.warning(
        "reconciliation_pending_enqueued order_id=%s reason=%s pending_id=%s",
        order_id_norm,
        reason_norm,
        row.id,
    )
    return row


def claim_reconciliation_pending_batch(
    db: Session,
    *,
    batch_size: int = 50,
) -> list[ReconciliationPending]:
    now = _utc_now()
    stale_processing_before = now - timedelta(minutes=5)
    rows = (
        db.query(ReconciliationPending)
        .filter(
            (
                (ReconciliationPending.status == "PENDING")
                & (
                    (ReconciliationPending.next_retry_at.is_(None))
                    | (ReconciliationPending.next_retry_at <= now)
                )
            )
            | (
                (ReconciliationPending.status == "FAILED")
                & (
                    (ReconciliationPending.next_retry_at.is_(None))
                    | (ReconciliationPending.next_retry_at <= now)
                )
            )
            | (
                (ReconciliationPending.status == "PROCESSING")
                & (ReconciliationPending.processing_started_at <= stale_processing_before)
            )
        )
        .order_by(ReconciliationPending.created_at.asc())
        .limit(max(int(batch_size or 50), 1))
        .all()
    )

    for row in rows:
        row.status = "PROCESSING"
        row.processing_started_at = now
        row.updated_at = now
    if rows:
        db.commit()
    return rows


def mark_reconciliation_pending_done(db: Session, *, pending_id: str) -> None:
    row = db.query(ReconciliationPending).filter(ReconciliationPending.id == pending_id).first()
    if not row:
        return
    now = _utc_now()
    row.status = "DONE"
    row.completed_at = now
    row.processing_started_at = None
    row.next_retry_at = None
    row.last_error = None
    row.updated_at = now
    db.commit()


def mark_reconciliation_pending_failed(
    db: Session,
    *,
    pending_id: str,
    error_message: str,
) -> None:
    row = db.query(ReconciliationPending).filter(ReconciliationPending.id == pending_id).first()
    if not row:
        return
    now = _utc_now()
    row.attempt_count = int(row.attempt_count or 0) + 1
    row.last_error = str(error_message or "")[:4000]
    row.processing_started_at = None
    row.updated_at = now

    if int(row.attempt_count or 0) >= int(row.max_attempts or DEFAULT_MAX_ATTEMPTS):
        row.status = "FAILED_FINAL"
        row.next_retry_at = None
        row.completed_at = now
    else:
        row.status = "FAILED"
        row.next_retry_at = _next_retry_at_for(int(row.attempt_count or 0))
    db.commit()


def list_reconciliation_pending(
    db: Session,
    *,
    status: str | None = None,
    limit: int = 50,
) -> list[ReconciliationPending]:
    q = db.query(ReconciliationPending)
    status_norm = str(status or "").strip().upper()
    if status_norm:
        q = q.filter(ReconciliationPending.status == status_norm)
    return (
        q.order_by(ReconciliationPending.updated_at.desc(), ReconciliationPending.id.desc())
        .limit(max(int(limit or 50), 1))
        .all()
    )
