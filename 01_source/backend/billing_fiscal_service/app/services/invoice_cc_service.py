# I-2 — Processamento stub de CC-e / carta de correção (estado CORRECTION_REQUESTED).

from __future__ import annotations

import logging
import os
import socket
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.invoice_model import Invoice, InvoiceStatus
from app.services.fiscal_router_service import route_cc_e_stub
from app.services.invoice_processing_service import _processing_timeout_sec

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _worker_id() -> str:
    configured = os.getenv("INVOICE_ISSUE_WORKER_ID")
    if configured:
        return f"{configured}:cce"
    return f"billing_fiscal_cce:{socket.gethostname()}:{os.getpid()}"


def _default_correction_text(invoice: Invoice) -> str:
    pj = invoice.payload_json or {}
    if isinstance(pj, dict):
        manual = pj.get("cce_manual_request") or {}
        if isinstance(manual, dict):
            t = manual.get("correction_text")
            if t and str(t).strip():
                return str(t).strip()[:1000]
        cr = pj.get("cancel_request") or {}
        if isinstance(cr, dict):
            r = cr.get("reason")
            if r and str(r).strip():
                return str(r).strip()[:1000]
    return "Ajuste operacional (stub CC-e)."


def _merge_payload(invoice: Invoice, patch: dict) -> None:
    base = dict(invoice.payload_json or {})
    base.update(patch)
    invoice.payload_json = base


def list_eligible_cc_invoice_ids(db: Session, *, batch_size: int) -> list[str]:
    now = _utc_now()
    stale_before = now - timedelta(seconds=_processing_timeout_sec())
    stmt = (
        select(Invoice.id)
        .where(Invoice.status == InvoiceStatus.CORRECTION_REQUESTED)
        .where((Invoice.next_retry_at.is_(None)) | (Invoice.next_retry_at <= now))
        .where((Invoice.locked_at.is_(None)) | (Invoice.locked_at < stale_before))
        .order_by(Invoice.updated_at.asc(), Invoice.id.asc())
        .limit(batch_size)
    )
    return list(db.execute(stmt).scalars().all())


def _claim_cc_row(db: Session, *, invoice_id: str, worker_id: str) -> bool:
    now = _utc_now()
    stale_before = now - timedelta(seconds=_processing_timeout_sec())
    stmt = (
        update(Invoice)
        .where(Invoice.id == invoice_id)
        .where(Invoice.status == InvoiceStatus.CORRECTION_REQUESTED)
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


def claim_invoice_for_cc(db: Session, *, invoice_id: str, worker_id: str | None = None) -> Invoice | None:
    wid = worker_id or _worker_id()
    if not _claim_cc_row(db, invoice_id=invoice_id, worker_id=wid):
        db.rollback()
        return None
    db.commit()
    return db.query(Invoice).filter(Invoice.id == invoice_id).first()


def process_claimed_cc_stub(db: Session, *, invoice: Invoice) -> Invoice:
    text = _default_correction_text(invoice)
    try:
        evt = route_cc_e_stub(invoice, text)
    except Exception as exc:
        invoice.error_message = str(exc)
        invoice.last_error_code = "CCE_STUB_FAILED"
        invoice.locked_by = None
        invoice.locked_at = None
        invoice.processing_started_at = None
        invoice.next_retry_at = _utc_now() + timedelta(seconds=90)
        db.commit()
        raise
    gr = dict(invoice.government_response or {})
    evs = list(gr.get("cce_events") or [])
    evs.append(evt)
    gr["cce_events"] = evs
    gr.pop("cancel_stub", None)
    invoice.government_response = gr
    _merge_payload(
        invoice,
        {
            "cce_stub_applied": True,
            "cce_applied_at": _utc_now().isoformat(),
        },
    )
    invoice.status = InvoiceStatus.ISSUED
    invoice.error_message = None
    invoice.last_error_code = None
    invoice.next_retry_at = None
    invoice.locked_by = None
    invoice.locked_at = None
    invoice.processing_started_at = None
    db.commit()
    db.refresh(invoice)
    logger.info(
        "invoice_cce_stub_applied",
        extra={"invoice_id": invoice.id, "order_id": invoice.order_id},
    )
    try:
        from app.services.invoice_email_service import send_danfe_email_after_cce

        send_danfe_email_after_cce(invoice.id)
    except Exception:
        logger.exception("invoice_cce_email_hook_failed", extra={"invoice_id": invoice.id})
    return invoice


def claim_and_process_cc_stub_by_id(
    db: Session,
    *,
    invoice_id: str,
    worker_id: str | None = None,
) -> Invoice | None:
    claimed = claim_invoice_for_cc(db, invoice_id=invoice_id, worker_id=worker_id)
    if claimed is None:
        return None
    return process_claimed_cc_stub(db, invoice=claimed)
