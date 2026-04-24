from __future__ import annotations

import os
import socket
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.invoice_model import Invoice
from app.services.fiscal_router_service import route_issue_invoice_reconnect


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _worker_id() -> str:
    configured = os.getenv("INVOICE_RESYNC_WORKER_ID")
    if configured:
        return configured
    return f"billing_fiscal:resync:{socket.gethostname()}:{os.getpid()}"


def _processing_timeout_sec() -> int:
    return int(os.getenv("INVOICE_RESYNC_PROCESSING_TIMEOUT_SEC", "180"))


def _is_sync_pending(government_response: dict | None) -> bool:
    if not isinstance(government_response, dict):
        return False
    return bool(government_response.get("sync_pending") is True)


def list_eligible_resync_invoice_ids(
    db: Session,
    *,
    batch_size: int,
) -> list[str]:
    now = _utc_now()
    stale_before = now - timedelta(seconds=_processing_timeout_sec())

    stmt = (
        select(Invoice.id)
        .where(Invoice.issued_at.is_not(None))
        .where((Invoice.next_retry_at.is_(None)) | (Invoice.next_retry_at <= now))
        .where((Invoice.locked_at.is_(None)) | (Invoice.locked_at < stale_before))
        .order_by(Invoice.issued_at.asc(), Invoice.id.asc())
        .limit(batch_size)
    )
    candidate_ids = list(db.execute(stmt).scalars().all())

    if not candidate_ids:
        return []

    rows = db.query(Invoice.id, Invoice.government_response).filter(Invoice.id.in_(candidate_ids)).all()
    return [invoice_id for invoice_id, gov in rows if _is_sync_pending(gov)]


def _claim_resync_invoice_row(
    db: Session,
    *,
    invoice_id: str,
    worker_id: str,
) -> bool:
    now = _utc_now()
    stale_before = now - timedelta(seconds=_processing_timeout_sec())

    stmt = (
        update(Invoice)
        .where(Invoice.id == invoice_id)
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


def claim_and_process_resync_invoice_by_id(
    db: Session,
    *,
    invoice_id: str,
    worker_id: str | None = None,
) -> Invoice | None:
    wid = worker_id or _worker_id()
    if not _claim_resync_invoice_row(db, invoice_id=invoice_id, worker_id=wid):
        db.rollback()
        return None

    db.commit()
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if invoice is None:
        return None

    gov_before = dict(invoice.government_response or {})
    if not _is_sync_pending(gov_before):
        invoice.locked_by = None
        invoice.locked_at = None
        invoice.processing_started_at = None
        db.commit()
        return None

    try:
        fiscal_result = route_issue_invoice_reconnect(invoice)
        gov_after = dict(fiscal_result.get("government_response") or {})
        gov_after["sync_pending"] = False
        gov_after["sync_state"] = "SYNCED"
        gov_after["sync_synced_at"] = _utc_now().isoformat()
        if gov_before.get("sync_id"):
            gov_after["sync_id"] = gov_before.get("sync_id")

        invoice.invoice_number = fiscal_result.get("invoice_number") or invoice.invoice_number
        invoice.invoice_series = fiscal_result.get("invoice_series") or invoice.invoice_series
        invoice.access_key = fiscal_result.get("access_key") or invoice.access_key
        invoice.xml_content = fiscal_result.get("xml_content") or invoice.xml_content
        invoice.tax_details = fiscal_result.get("tax_details") or invoice.tax_details
        invoice.government_response = gov_after
        invoice.payload_json = fiscal_result
        invoice.error_message = None
        invoice.last_error_code = None
        invoice.next_retry_at = None
    except Exception as exc:
        gov_fail = dict(gov_before)
        gov_fail["sync_pending"] = True
        gov_fail["sync_state"] = "FAILED_RETRY"
        gov_fail["sync_last_error"] = str(exc)
        gov_fail["sync_last_attempt_at"] = _utc_now().isoformat()
        invoice.government_response = gov_fail
        invoice.last_error_code = "RESYNC_FAILED"
        invoice.error_message = str(exc)[:1000]
        invoice.next_retry_at = _utc_now() + timedelta(seconds=30)
    finally:
        invoice.locked_by = None
        invoice.locked_at = None
        invoice.processing_started_at = None
        invoice.updated_at = _utc_now()
        db.commit()
        db.refresh(invoice)

    return invoice
