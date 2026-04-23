# I-2 — Solicitação e processamento de cancelamento (void SEFAZ stub + estados CC/complemento).

from __future__ import annotations

import logging
import os
import socket
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.datetime_utils import to_iso_utc
from app.models.invoice_model import Invoice, InvoiceStatus
from app.services.cancellation_policy_service import (
    CancelPolicyAction,
    resolve_cancel_policy,
)
from app.services.fiscal_router_service import route_cancel_invoice
from app.services.invoice_processing_service import _compute_next_retry_at, _max_retries, _processing_timeout_sec

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _worker_id() -> str:
    configured = os.getenv("INVOICE_ISSUE_WORKER_ID")
    if configured:
        return f"{configured}:cancel"
    return f"billing_fiscal_cancel:{socket.gethostname()}:{os.getpid()}"


def _merge_payload(invoice: Invoice, patch: dict) -> None:
    base = dict(invoice.payload_json or {})
    base.update(patch)
    invoice.payload_json = base


def request_invoice_cancel(
    db: Session,
    *,
    invoice_id: str,
    reason: str | None = None,
    source: str = "api",
) -> Invoice:
    inv = db.query(Invoice).filter(Invoice.id == str(invoice_id).strip()).first()
    if not inv:
        raise ValueError(f"Invoice não encontrada: {invoice_id}")
    if inv.status != InvoiceStatus.ISSUED:
        raise ValueError(
            f"Cancelamento só é permitido para invoice ISSUED; status atual={inv.status.value}"
        )
    if not inv.issued_at:
        raise ValueError("Invoice sem issued_at; não é possível aplicar política de cancelamento.")

    policy = resolve_cancel_policy(
        issued_at=inv.issued_at,
        now=_utc_now(),
        country=str(inv.country or "BR"),
        fiscal_doc_subtype=inv.fiscal_doc_subtype,
    )

    _merge_payload(
        inv,
        {
            "cancel_request": {
                "reason": reason,
                "source": source,
                "requested_at": to_iso_utc(_utc_now()),
                "policy_action": policy.action.value,
                "policy_detail": policy.detail,
            }
        },
    )

    if policy.action == CancelPolicyAction.VOID_NFCE:
        inv.status = InvoiceStatus.CANCELLING
        inv.next_retry_at = None
        inv.error_message = None
        inv.last_error_code = None
    elif policy.action == CancelPolicyAction.CORRECTION_LETTER_REQUIRED:
        inv.status = InvoiceStatus.CORRECTION_REQUESTED
        gr = dict(inv.government_response or {})
        gr["cancel_stub"] = {
            "kind": "cce_required",
            "message": "Pendente integração SEFAZ (CC-e). Estado CORRECTION_REQUESTED.",
            "policy": policy.detail,
        }
        inv.government_response = gr
    elif policy.action == CancelPolicyAction.COMPLEMENTARY_INVOICE_REQUIRED:
        inv.status = InvoiceStatus.COMPLEMENTARY_ISSUED
        gr = dict(inv.government_response or {})
        gr["cancel_stub"] = {
            "kind": "complementary_required",
            "message": "Pendente NF complementar / análise. Estado COMPLEMENTARY_ISSUED.",
            "policy": policy.detail,
        }
        inv.government_response = gr
    else:
        inv.status = InvoiceStatus.CORRECTION_REQUESTED
        gr = dict(inv.government_response or {})
        gr["cancel_stub"] = {
            "kind": "manual_review",
            "policy": policy.detail,
        }
        inv.government_response = gr

    db.commit()
    db.refresh(inv)
    logger.info(
        "invoice_cancel_requested",
        extra={
            "invoice_id": inv.id,
            "order_id": inv.order_id,
            "policy": policy.action.value,
            "new_status": inv.status.value,
        },
    )
    return inv


def list_eligible_cancel_invoice_ids(db: Session, *, batch_size: int) -> list[str]:
    now = _utc_now()
    stale_before = now - timedelta(seconds=_processing_timeout_sec())

    stmt = (
        select(Invoice.id)
        .where(Invoice.status == InvoiceStatus.CANCELLING)
        .where((Invoice.next_retry_at.is_(None)) | (Invoice.next_retry_at <= now))
        .where((Invoice.locked_at.is_(None)) | (Invoice.locked_at < stale_before))
        .order_by(Invoice.issued_at.asc(), Invoice.id.asc())
        .limit(batch_size)
    )
    return list(db.execute(stmt).scalars().all())


def _claim_cancel_row(db: Session, *, invoice_id: str, worker_id: str) -> bool:
    now = _utc_now()
    stale_before = now - timedelta(seconds=_processing_timeout_sec())
    stmt = (
        update(Invoice)
        .where(Invoice.id == invoice_id)
        .where(Invoice.status == InvoiceStatus.CANCELLING)
        .where((Invoice.next_retry_at.is_(None)) | (Invoice.next_retry_at <= now))
        .where((Invoice.locked_at.is_(None)) | (Invoice.locked_at < stale_before))
        .values(
            locked_by=worker_id,
            locked_at=now,
            processing_started_at=now,
            last_attempt_at=now,
        )
    )
    result = db.execute(stmt)
    return int(result.rowcount or 0) == 1


def claim_invoice_for_cancel(db: Session, *, invoice_id: str, worker_id: str | None = None) -> Invoice | None:
    wid = worker_id or _worker_id()
    if not _claim_cancel_row(db, invoice_id=invoice_id, worker_id=wid):
        db.rollback()
        return None
    db.commit()
    return db.query(Invoice).filter(Invoice.id == invoice_id).first()


def finalize_cancel_success(db: Session, *, invoice: Invoice, result: dict) -> Invoice:
    invoice.status = InvoiceStatus.CANCELLED
    gr = dict(invoice.government_response or {})
    gr["cancel"] = result
    invoice.government_response = gr
    invoice.error_message = None
    invoice.last_error_code = None
    invoice.next_retry_at = None
    invoice.locked_by = None
    invoice.locked_at = None
    invoice.processing_started_at = None
    db.commit()
    db.refresh(invoice)
    logger.info("invoice_cancelled", extra={"invoice_id": invoice.id, "order_id": invoice.order_id})
    try:
        from app.services.invoice_email_service import send_danfe_email_after_cancel

        send_danfe_email_after_cancel(invoice.id)
    except Exception:
        logger.exception("invoice_cancel_email_hook_failed", extra={"invoice_id": invoice.id})
    return invoice


def finalize_cancel_failure(db: Session, *, invoice: Invoice, exc: Exception) -> Invoice:
    next_retry_count = int(invoice.retry_count or 0) + 1
    max_retries = _max_retries()
    invoice.error_message = str(exc)
    invoice.last_error_code = "CANCEL_FAILED"
    invoice.retry_count = next_retry_count
    invoice.locked_by = None
    invoice.locked_at = None
    invoice.processing_started_at = None
    if next_retry_count >= max_retries:
        invoice.status = InvoiceStatus.DEAD_LETTER
        invoice.dead_lettered_at = _utc_now()
        invoice.next_retry_at = None
    else:
        invoice.status = InvoiceStatus.CANCELLING
        invoice.next_retry_at = _compute_next_retry_at(next_retry_count)
    db.commit()
    db.refresh(invoice)
    logger.exception(
        "invoice_cancel_failed",
        extra={"invoice_id": invoice.id, "order_id": invoice.order_id, "retry_count": invoice.retry_count},
    )
    return invoice


def process_claimed_cancel(db: Session, *, invoice: Invoice) -> Invoice:
    try:
        result = route_cancel_invoice(invoice)
        return finalize_cancel_success(db, invoice=invoice, result=result)
    except Exception as exc:
        return finalize_cancel_failure(db, invoice=invoice, exc=exc)


def claim_and_process_cancel_by_id(
    db: Session,
    *,
    invoice_id: str,
    worker_id: str | None = None,
) -> Invoice | None:
    claimed = claim_invoice_for_cancel(db, invoice_id=invoice_id, worker_id=worker_id)
    if claimed is None:
        return None
    return process_claimed_cancel(db, invoice=claimed)


def request_cancel_for_order_if_issued(
    db: Session,
    *,
    order_id: str,
    reason: str | None = None,
    source: str = "domain_event",
) -> Invoice | None:
    inv = db.query(Invoice).filter(Invoice.order_id == str(order_id).strip()).first()
    if not inv or inv.status != InvoiceStatus.ISSUED:
        return None
    return request_invoice_cancel(db, invoice_id=inv.id, reason=reason, source=source)
