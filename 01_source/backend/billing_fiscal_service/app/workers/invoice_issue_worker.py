# 01_source/backend/billing_fiscal_service/app/workers/invoice_issue_worker.py
# issue worker: só pega invoices elegíveis; tenta claim atômico, processa só se o claim for dele;
# respeita next_retry_at; não conflita com outro worker igual
# 11/04/2026 - aplicar padrão de logs.

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
                    logger.info(
                        "invoice_issue_worker_skipped invoice_id=%s reason=claim_not_acquired_or_not_eligible",
                        invoice_id,
                    )
                    continue

                processed += 1
                logger.info(
                    "invoice_issue_worker_processed invoice_id=%s",
                    invoice_id,
                )

            except Exception as exc:
                failed += 1
                logger.exception(
                    "invoice_issue_worker_error invoice_id=%s error=%s",
                    invoice_id,
                    str(exc),
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

    logger.info(
        "invoice_issue_worker_started poll_sec=%s batch_size=%s",
        poll,
        batch,
    )

    while True:
        try:
            result = process_batch_once(batch)
            logger.info(
                "invoice_issue_worker_cycle processed=%s skipped=%s failed=%s scanned=%s",
                result["processed"],
                result["skipped"],
                result["failed"],
                result["scanned"],
            )
        except Exception as exc:
            logger.exception(
                "invoice_issue_worker_cycle_failed error=%s",
                str(exc),
            )

        time.sleep(poll)


if __name__ == "__main__":
    run()