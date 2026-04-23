from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.order import Order
from app.services.order_reconciliation_service import (
    reconcile_order_compensation,
    resolve_latest_allocation,
    resolve_latest_pickup,
)
from app.services.reconciliation_pending_service import (
    claim_reconciliation_pending_batch,
    mark_reconciliation_pending_done,
    mark_reconciliation_pending_failed,
)
from app.services.ops_audit_service import record_ops_action_audit

logger = logging.getLogger(__name__)


def _safe_record_worker_audit(
    *,
    action: str,
    result: str,
    correlation_id: str,
    order_id: str | None = None,
    error_message: str | None = None,
    details: dict | None = None,
) -> None:
    audit_db = SessionLocal()
    try:
        record_ops_action_audit(
            db=audit_db,
            action=action,
            result=result,
            correlation_id=correlation_id,
            user_id=None,
            role="system_worker",
            order_id=order_id,
            error_message=error_message,
            details=details or {},
        )
        audit_db.commit()
    except Exception:
        audit_db.rollback()
        logger.exception(
            "reconciliation_retry_audit_failed action=%s correlation_id=%s",
            action,
            correlation_id,
        )
    finally:
        audit_db.close()


def run_reconciliation_retry_once(
    db: Session,
    *,
    batch_size: int = 25,
) -> int:
    rows = claim_reconciliation_pending_batch(db, batch_size=batch_size)
    if not rows:
        return 0

    processed = 0
    for row in rows:
        try:
            order = db.get(Order, row.order_id)
            if not order:
                raise RuntimeError(f"order_not_found:{row.order_id}")

            allocation = resolve_latest_allocation(db, order=order)
            pickup = resolve_latest_pickup(db, order=order)
            result = reconcile_order_compensation(
                db=db,
                order=order,
                allocation=allocation,
                pickup=pickup,
                cancel_reason="async_reconciliation_retry",
                record_pending_on_failure=False,
            )

            has_error = bool(result.slot_release_error or result.credit_restore_error)
            if has_error:
                error_message = result.slot_release_error or result.credit_restore_error or "unknown_error"
                raise RuntimeError(str(error_message))

            mark_reconciliation_pending_done(db, pending_id=row.id)
            processed += 1
            _safe_record_worker_audit(
                action="SYSTEM_RECON_RETRY_PROCESS",
                result="SUCCESS",
                correlation_id=f"recon-worker-{row.id}",
                order_id=row.order_id,
                details={
                    "pending_id": row.id,
                    "attempt_count": int(row.attempt_count or 0),
                },
            )
            logger.info(
                "reconciliation_retry_done pending_id=%s order_id=%s",
                row.id,
                row.order_id,
            )
        except Exception as exc:
            mark_reconciliation_pending_failed(db, pending_id=row.id, error_message=str(exc))
            _safe_record_worker_audit(
                action="SYSTEM_RECON_RETRY_PROCESS",
                result="ERROR",
                correlation_id=f"recon-worker-{row.id}",
                order_id=row.order_id,
                error_message=str(exc),
                details={
                    "pending_id": row.id,
                    "attempt_count": int((row.attempt_count or 0) + 1),
                },
            )
            logger.warning(
                "reconciliation_retry_failed pending_id=%s order_id=%s error=%s",
                row.id,
                row.order_id,
                str(exc),
            )
    return processed
