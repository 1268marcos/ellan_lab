# 01_source/backend/billing_fiscal_service/app/workers/invoice_issue_worker.py
# issue worker: só pega invoices elegíveis; tenta claim atômico, processa só se o claim for dele;
# respeita next_retry_at; não conflita com outro worker igual
# 11/04/2026 - aplicar padrão de logs.

from __future__ import annotations

import logging
import os
import time

from app.core.db import SessionLocal
from app.services.invoice_cancel_service import (
    claim_and_process_cancel_by_id,
    list_eligible_cancel_invoice_ids,
)
from app.services.invoice_cc_service import (
    claim_and_process_cc_stub_by_id,
    list_eligible_cc_invoice_ids,
)
from app.services.invoice_email_queue_service import (
    claim_and_process_email_outbox_by_id,
    list_eligible_email_outbox_ids,
)
from app.services.invoice_processing_service import (
    claim_and_process_invoice_by_id,
    list_eligible_invoice_ids,
)
from app.services.invoice_resync_service import (
    claim_and_process_resync_invoice_by_id,
    list_eligible_resync_invoice_ids,
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

        cancel_processed = 0
        cancel_skipped = 0
        cancel_failed = 0
        cancel_ids = list_eligible_cancel_invoice_ids(db, batch_size=batch_size)
        for invoice_id in cancel_ids:
            try:
                cres = claim_and_process_cancel_by_id(db, invoice_id=invoice_id)
                if cres is None:
                    cancel_skipped += 1
                    logger.info(
                        "invoice_cancel_worker_skipped invoice_id=%s reason=claim_not_acquired_or_not_eligible",
                        invoice_id,
                    )
                else:
                    cancel_processed += 1
                    logger.info("invoice_cancel_worker_processed invoice_id=%s", invoice_id)
            except Exception as exc:
                cancel_failed += 1
                logger.exception(
                    "invoice_cancel_worker_error invoice_id=%s error=%s",
                    invoice_id,
                    str(exc),
                )

        cc_processed = 0
        cc_skipped = 0
        cc_failed = 0
        cc_ids = list_eligible_cc_invoice_ids(db, batch_size=batch_size)
        for invoice_id in cc_ids:
            try:
                ccres = claim_and_process_cc_stub_by_id(db, invoice_id=invoice_id)
                if ccres is None:
                    cc_skipped += 1
                    logger.info(
                        "invoice_cce_worker_skipped invoice_id=%s reason=claim_not_acquired_or_not_eligible",
                        invoice_id,
                    )
                else:
                    cc_processed += 1
                    logger.info("invoice_cce_worker_processed invoice_id=%s", invoice_id)
            except Exception as exc:
                cc_failed += 1
                logger.exception(
                    "invoice_cce_worker_error invoice_id=%s error=%s",
                    invoice_id,
                    str(exc),
                )

        email_processed = 0
        email_skipped = 0
        email_failed = 0
        email_ids = list_eligible_email_outbox_ids(db, batch_size=batch_size)
        for outbox_id in email_ids:
            try:
                eres = claim_and_process_email_outbox_by_id(db, outbox_id=outbox_id)
                if eres is None:
                    email_skipped += 1
                    logger.info(
                        "invoice_email_worker_skipped outbox_id=%s reason=claim_not_acquired_or_not_eligible",
                        outbox_id,
                    )
                else:
                    email_processed += 1
                    logger.info("invoice_email_worker_processed outbox_id=%s", outbox_id)
            except Exception as exc:
                email_failed += 1
                logger.exception(
                    "invoice_email_worker_error outbox_id=%s error=%s",
                    outbox_id,
                    str(exc),
                )

        resync_processed = 0
        resync_skipped = 0
        resync_failed = 0
        resync_ids = list_eligible_resync_invoice_ids(db, batch_size=batch_size)
        for invoice_id in resync_ids:
            try:
                rres = claim_and_process_resync_invoice_by_id(db, invoice_id=invoice_id)
                if rres is None:
                    resync_skipped += 1
                    logger.info(
                        "invoice_resync_worker_skipped invoice_id=%s reason=claim_not_acquired_or_not_eligible",
                        invoice_id,
                    )
                else:
                    resync_processed += 1
                    logger.info("invoice_resync_worker_processed invoice_id=%s", invoice_id)
            except Exception as exc:
                resync_failed += 1
                logger.exception(
                    "invoice_resync_worker_error invoice_id=%s error=%s",
                    invoice_id,
                    str(exc),
                )

        return {
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "scanned": len(invoice_ids),
            "cancel_processed": cancel_processed,
            "cancel_skipped": cancel_skipped,
            "cancel_failed": cancel_failed,
            "cancel_scanned": len(cancel_ids),
            "cc_processed": cc_processed,
            "cc_skipped": cc_skipped,
            "cc_failed": cc_failed,
            "cc_scanned": len(cc_ids),
            "email_processed": email_processed,
            "email_skipped": email_skipped,
            "email_failed": email_failed,
            "email_scanned": len(email_ids),
            "resync_processed": resync_processed,
            "resync_skipped": resync_skipped,
            "resync_failed": resync_failed,
            "resync_scanned": len(resync_ids),
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
                "invoice_issue_worker_cycle processed=%s skipped=%s failed=%s scanned=%s "
                "email_processed=%s email_skipped=%s email_failed=%s email_scanned=%s "
                "resync_processed=%s resync_skipped=%s resync_failed=%s resync_scanned=%s",
                result["processed"],
                result["skipped"],
                result["failed"],
                result["scanned"],
                result["email_processed"],
                result["email_skipped"],
                result["email_failed"],
                result["email_scanned"],
                result["resync_processed"],
                result["resync_skipped"],
                result["resync_failed"],
                result["resync_scanned"],
            )
        except Exception as exc:
            logger.exception(
                "invoice_issue_worker_cycle_failed error=%s",
                str(exc),
            )

        time.sleep(poll)


if __name__ == "__main__":
    run()