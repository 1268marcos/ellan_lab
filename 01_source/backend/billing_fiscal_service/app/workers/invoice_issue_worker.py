# 01_source/backend/billing_fiscal_service/app/workers/invoice_issue_worker.py
from __future__ import annotations

import logging
import time
from datetime import timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal, init_db
from app.models.invoice_model import Invoice, InvoiceStatus
from app.services.invoice_issue_service import issue_invoice

logger = logging.getLogger("invoice_issue_worker")


def _claim_batch(db: Session) -> list[str]:
    now = Invoice.created_at.type.python_type  # no-op to keep import sanity
    del now

    from datetime import datetime, timezone

    utc_now = datetime.now(timezone.utc)
    stale_before = utc_now - timedelta(seconds=settings.invoice_issue_processing_timeout_sec)

    rows = (
        db.query(Invoice)
        .filter(
            or_(
                ((Invoice.status == InvoiceStatus.PENDING) & (Invoice.next_retry_at.is_(None))),
                ((Invoice.status == InvoiceStatus.FAILED) & (Invoice.next_retry_at <= utc_now)),
                ((Invoice.status == InvoiceStatus.PROCESSING) & (Invoice.processing_started_at <= stale_before)),
            )
        )
        .with_for_update(skip_locked=True)
        .order_by(Invoice.created_at.asc())
        .limit(settings.invoice_issue_batch_size)
        .all()
    )

    claimed_ids: list[str] = []

    for row in rows:
        row.status = InvoiceStatus.PROCESSING
        row.processing_started_at = utc_now
        row.locked_at = utc_now
        row.locked_by = settings.invoice_issue_worker_id
        row.last_attempt_at = utc_now
        row.updated_at = utc_now
        claimed_ids.append(row.id)

    if claimed_ids:
        db.commit()

    return claimed_ids


def _process_one(invoice_id: str) -> None:
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            return

        previous_status = str(getattr(invoice.status, "value", invoice.status))
        issued = issue_invoice(db, invoice)
        final_status = str(getattr(issued.status, "value", issued.status))

        logger.info(
            "invoice_issue_worker_processed",
            extra={
                "invoice_id": issued.id,
                "order_id": issued.order_id,
                "country": issued.country,
                "region": issued.region,
                "previous_status": previous_status,
                "final_status": final_status,
                "retry_count": issued.retry_count,
                "next_retry_at": issued.next_retry_at.isoformat() if issued.next_retry_at else None,
                "invoice_number": issued.invoice_number,
                "invoice_series": issued.invoice_series,
                "access_key": issued.access_key,
            },
        )
    finally:
        db.close()


def run() -> None:
    init_db()
    logger.info("invoice_issue_worker_started")

    while True:
        db = SessionLocal()
        try:
            batch = _claim_batch(db)
        finally:
            db.close()

        if not batch:
            time.sleep(settings.invoice_issue_poll_sec)
            continue

        for invoice_id in batch:
            try:
                _process_one(invoice_id)
            except Exception:
                logger.exception(
                    "invoice_issue_worker_unexpected_error",
                    extra={"invoice_id": invoice_id},
                )

        time.sleep(settings.invoice_issue_poll_sec)


if __name__ == "__main__":
    run()