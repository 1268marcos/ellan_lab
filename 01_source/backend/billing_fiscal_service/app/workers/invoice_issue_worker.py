# 01_source/backend/billing_fiscal_service/app/workers/invoice_issue_worker.py
# issue worker: só pega invoices elegíveis; tenta claim atômico, processa só se o claim for dele;
# respeita next_retry_at; não conflita com outro worker igual 
from __future__ import annotations

import logging
import os
import time

from app.core.db import SessionLocal
from app.services.invoice_processing_service import (
    claim_and_process_invoice_by_id,
    list_eligible_invoice_ids,
)

logger = logging.getLogger(__name__)


def process_batch_once(batch_size: int):
    db = SessionLocal()

    processed = 0
    skipped = 0
    failed = 0

    try:
        invoice_ids = list_eligible_invoice_ids(db, batch_size=batch_size)

        for invoice_id in invoice_ids:
            try:
                result = claim_and_process_invoice_by_id(db, invoice_id=invoice_id)

                if result is None:
                    skipped += 1
                    continue

                processed += 1

            except Exception:
                failed += 1
                logger.exception(
                    "invoice_issue_worker_error",
                    extra={"invoice_id": invoice_id},
                )

        return {
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "scanned": len(invoice_ids),
        }

    finally:
        db.close()


def run():
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    poll = int(os.getenv("INVOICE_ISSUE_POLL_SEC", "5"))
    batch = int(os.getenv("INVOICE_ISSUE_BATCH_SIZE", "50"))

    logger.info("invoice_issue_worker_started")

    while True:
        try:
            result = process_batch_once(batch)
            logger.info("invoice_issue_worker_cycle", extra=result)
        except Exception:
            logger.exception("invoice_issue_worker_cycle_failed")

        time.sleep(poll)


if __name__ == "__main__":
    run()