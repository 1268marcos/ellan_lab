# 01_source/backend/billing_fiscal_service/app/workers/invoice_issue_worker.py
from __future__ import annotations

import logging
import os
import time

from sqlalchemy.orm import Session

from app.core.db import SessionLocal, init_db
from app.models.invoice_model import Invoice, InvoiceStatus
from app.services.invoice_issue_service import issue_invoice

logger = logging.getLogger("invoice_issue_worker")

POLL_SEC = int(os.getenv("INVOICE_ISSUE_POLL_SEC", "5"))
BATCH_SIZE = int(os.getenv("INVOICE_ISSUE_BATCH_SIZE", "50"))


def _claim_batch(db: Session) -> list[str]:
    rows = (
        db.query(Invoice)
        .filter(Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.FAILED]))
        .order_by(Invoice.created_at.asc())
        .limit(BATCH_SIZE)
        .all()
    )

    return [row.id for row in rows]


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
                "previous_status": previous_status,
                "final_status": final_status,
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
            time.sleep(POLL_SEC)
            continue

        for invoice_id in batch:
            try:
                _process_one(invoice_id)
            except Exception:
                logger.exception(
                    "invoice_issue_worker_unexpected_error",
                    extra={"invoice_id": invoice_id},
                )

        time.sleep(POLL_SEC)


if __name__ == "__main__":
    run()

