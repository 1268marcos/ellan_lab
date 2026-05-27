from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.order import Order
from app.services.order_reconciliation_service import (
    compensation_steps_for_reason,
    pending_step_succeeded,
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


def _retry_payload_patch(*, reason: str, result, attempt_count: int) -> dict:
    return {
        "last_retry_reason": str(reason or "").strip().lower(),
        "last_retry_attempt_count": int(attempt_count or 0),
        "compensation_result": result.to_payload_dict(),
    }


def _target_step_error(*, reason: str, result) -> str | None:
    reason_norm = str(reason or "").strip().lower()
    if reason_norm == "slot_release_failed":
        return result.slot_release_error
    if reason_norm == "credit_restore_failed":
        return result.credit_restore_error
    return result.slot_release_error or result.credit_restore_error


def run_reconciliation_retry_once(
    db: Session,
    *,
    batch_size: int = 25,
) -> int:
    """
    Processa pendências de reconciliação com retentativa seletiva por passo.

    Cada linha em ``reconciliation_pending`` representa um passo falho
    (``slot_release_failed`` ou ``credit_restore_failed``). O worker reexecuta
    apenas o passo alvo; se ele tiver sucesso, a pendência vai para DONE mesmo
    que o outro passo tenha falhado em outra linha ou execução anterior.
    Detalhes de cada tentativa são gravados em ``payload_json``.
    """
    rows = claim_reconciliation_pending_batch(db, batch_size=batch_size)
    if not rows:
        return 0

    processed = 0
    for row in rows:
        reason = str(row.reason or "").strip().lower()
        attempt_count = int(row.attempt_count or 0)
        try:
            order = db.get(Order, row.order_id)
            if not order:
                raise RuntimeError(f"order_not_found:{row.order_id}")

            allocation = resolve_latest_allocation(db, order=order)
            pickup = resolve_latest_pickup(db, order=order)
            run_slot_release, run_credit_restore = compensation_steps_for_reason(reason)
            result = reconcile_order_compensation(
                db=db,
                order=order,
                allocation=allocation,
                pickup=pickup,
                cancel_reason="async_reconciliation_retry",
                record_pending_on_failure=False,
                run_slot_release=run_slot_release,
                run_credit_restore=run_credit_restore,
            )
            payload_patch = _retry_payload_patch(
                reason=reason,
                result=result,
                attempt_count=attempt_count,
            )

            if pending_step_succeeded(reason=reason, result=result):
                db.commit()
                mark_reconciliation_pending_done(
                    db,
                    pending_id=row.id,
                    payload_patch=payload_patch,
                )
                processed += 1
                _safe_record_worker_audit(
                    action="SYSTEM_RECON_RETRY_PROCESS",
                    result="SUCCESS",
                    correlation_id=f"recon-worker-{row.id}",
                    order_id=row.order_id,
                    details={
                        "pending_id": row.id,
                        "attempt_count": attempt_count,
                        "reason": reason,
                        "compensation_result": result.to_payload_dict(),
                    },
                )
                logger.info(
                    "reconciliation_retry_done pending_id=%s order_id=%s reason=%s",
                    row.id,
                    row.order_id,
                    reason,
                )
                continue

            step_error = _target_step_error(reason=reason, result=result) or "step_failed"
            db.rollback()
            mark_reconciliation_pending_failed(
                db,
                pending_id=row.id,
                error_message=str(step_error),
                payload_patch=payload_patch,
            )
            _safe_record_worker_audit(
                action="SYSTEM_RECON_RETRY_PROCESS",
                result="ERROR",
                correlation_id=f"recon-worker-{row.id}",
                order_id=row.order_id,
                error_message=str(step_error),
                details={
                    "pending_id": row.id,
                    "attempt_count": attempt_count + 1,
                    "reason": reason,
                    "compensation_result": result.to_payload_dict(),
                },
            )
            logger.warning(
                "reconciliation_retry_failed pending_id=%s order_id=%s reason=%s error=%s",
                row.id,
                row.order_id,
                reason,
                step_error,
            )
        except Exception as exc:
            db.rollback()
            mark_reconciliation_pending_failed(
                db,
                pending_id=row.id,
                error_message=str(exc),
                payload_patch={
                    "last_retry_reason": reason,
                    "last_retry_attempt_count": attempt_count + 1,
                    "last_retry_exception": str(exc),
                },
            )
            _safe_record_worker_audit(
                action="SYSTEM_RECON_RETRY_PROCESS",
                result="ERROR",
                correlation_id=f"recon-worker-{row.id}",
                order_id=row.order_id,
                error_message=str(exc),
                details={
                    "pending_id": row.id,
                    "attempt_count": attempt_count + 1,
                    "reason": reason,
                },
            )
            logger.warning(
                "reconciliation_retry_failed pending_id=%s order_id=%s error=%s",
                row.id,
                row.order_id,
                str(exc),
            )
    return processed
