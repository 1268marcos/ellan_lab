# 01_source/backend/billing_fiscal_service/app/services/invoice_processing_service.py
from __future__ import annotations

import logging
import os
import socket
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.invoice_model import Invoice, InvoiceStatus
from app.services.fiscal_router_service import route_issue_invoice

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _worker_id() -> str:
    configured = os.getenv("INVOICE_ISSUE_WORKER_ID")
    if configured:
        return configured
    return f"billing_fiscal:{socket.gethostname()}:{os.getpid()}"


def _max_retries() -> int:
    return int(os.getenv("INVOICE_ISSUE_MAX_RETRIES", "5"))


def _base_backoff_sec() -> int:
    return int(os.getenv("INVOICE_ISSUE_BASE_BACKOFF_SEC", "15"))


def _processing_timeout_sec() -> int:
    return int(os.getenv("INVOICE_ISSUE_PROCESSING_TIMEOUT_SEC", "180"))


def _compute_next_retry_at(retry_count: int) -> datetime:
    # backoff exponencial com teto de 30 minutos
    base = max(1, _base_backoff_sec())
    delay = min(base * (2 ** max(0, retry_count - 1)), 1800)
    return _utc_now() + timedelta(seconds=delay)


def _claim_invoice_row(
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
        .where(
            (Invoice.status == InvoiceStatus.PENDING)
            | (Invoice.status == InvoiceStatus.FAILED)
        )
        .where(
            (Invoice.next_retry_at.is_(None))
            | (Invoice.next_retry_at <= now)
        )
        .where(
            (Invoice.locked_at.is_(None))
            | (Invoice.locked_at < stale_before)
        )
        .values(
            status=InvoiceStatus.PROCESSING,
            locked_by=worker_id,
            locked_at=now,
            processing_started_at=now,
            last_attempt_at=now,
        )
    )

    result = db.execute(stmt)
    return int(result.rowcount or 0) == 1


def claim_invoice_for_processing(
    db: Session,
    *,
    invoice_id: str,
    worker_id: str | None = None,
) -> Invoice | None:
    wid = worker_id or _worker_id()

    if not _claim_invoice_row(db, invoice_id=invoice_id, worker_id=wid):
        db.rollback()
        return None

    db.commit()

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    return invoice


def finalize_invoice_success(
    db: Session,
    *,
    invoice: Invoice,
    result: dict,
) -> Invoice:
    invoice.status = InvoiceStatus.ISSUED
    invoice.invoice_number = result.get("invoice_number")
    invoice.invoice_series = result.get("invoice_series")
    invoice.access_key = result.get("access_key")
    invoice.tax_details = result.get("tax_details")
    invoice.xml_content = result.get("xml_content")
    invoice.government_response = result.get("government_response")
    invoice.payload_json = result
    invoice.error_message = None
    invoice.last_error_code = None
    invoice.issued_at = _utc_now()
    invoice.next_retry_at = None
    invoice.locked_by = None
    invoice.locked_at = None
    invoice.processing_started_at = None

    db.commit()
    db.refresh(invoice)

    logger.info(
        "invoice_processing_succeeded",
        extra={
            "invoice_id": invoice.id,
            "order_id": invoice.order_id,
            "invoice_number": invoice.invoice_number,
            "country": invoice.country,
        },
    )

    return invoice


def finalize_invoice_failure(
    db: Session,
    *,
    invoice: Invoice,
    exc: Exception,
) -> Invoice:
    next_retry_count = int(invoice.retry_count or 0) + 1
    max_retries = _max_retries()

    invoice.error_message = str(exc)
    invoice.last_error_code = "ISSUE_FAILED"
    invoice.retry_count = next_retry_count
    invoice.locked_by = None
    invoice.locked_at = None
    invoice.processing_started_at = None

    if next_retry_count >= max_retries:
        invoice.status = InvoiceStatus.DEAD_LETTER
        invoice.dead_lettered_at = _utc_now()
        invoice.next_retry_at = None
    else:
        invoice.status = InvoiceStatus.FAILED
        invoice.next_retry_at = _compute_next_retry_at(next_retry_count)

    db.commit()
    db.refresh(invoice)

    logger.exception(
        "invoice_processing_failed",
        extra={
            "invoice_id": invoice.id,
            "order_id": invoice.order_id,
            "retry_count": invoice.retry_count,
            "status": str(getattr(invoice.status, "value", invoice.status)),
            "next_retry_at": invoice.next_retry_at.isoformat() if invoice.next_retry_at else None,
        },
    )

    return invoice


def process_claimed_invoice(
    db: Session,
    *,
    invoice: Invoice,
) -> Invoice:
    try:
        result = route_issue_invoice(invoice)
        return finalize_invoice_success(db, invoice=invoice, result=result)
    except Exception as exc:
        return finalize_invoice_failure(db, invoice=invoice, exc=exc)


def claim_and_process_invoice_by_id(
    db: Session,
    *,
    invoice_id: str,
    worker_id: str | None = None,
) -> Invoice | None:
    claimed = claim_invoice_for_processing(
        db,
        invoice_id=invoice_id,
        worker_id=worker_id,
    )
    if claimed is None:
        return None

    return process_claimed_invoice(db, invoice=claimed)


def list_eligible_invoice_ids(
    db: Session,
    *,
    batch_size: int,
) -> list[str]:
    now = _utc_now()
    stale_before = now - timedelta(seconds=_processing_timeout_sec())

    stmt = (
        select(Invoice.id)
        .where(
            (Invoice.status == InvoiceStatus.PENDING)
            | (Invoice.status == InvoiceStatus.FAILED)
        )
        .where(
            (Invoice.next_retry_at.is_(None))
            | (Invoice.next_retry_at <= now)
        )
        .where(
            (Invoice.locked_at.is_(None))
            | (Invoice.locked_at < stale_before)
        )
        .order_by(Invoice.created_at.asc(), Invoice.id.asc())
        .limit(batch_size)
    )

    return list(db.execute(stmt).scalars().all())

