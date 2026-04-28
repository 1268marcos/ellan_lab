from __future__ import annotations

import logging
import os
import time

from app.core.db import SessionLocal
from app.services.partner_billing_cycle_service import (
    compute_cycle_once,
    list_eligible_billing_cycle_ids,
)

logger = logging.getLogger(__name__)


def process_batch_once(batch_size: int) -> dict:
    db = SessionLocal()
    processed = 0
    skipped = 0
    failed = 0
    try:
        cycle_ids = list_eligible_billing_cycle_ids(db, batch_size=batch_size)
        for cycle_id in cycle_ids:
            try:
                result = compute_cycle_once(db, cycle_id)
                if result is None:
                    skipped += 1
                    continue
                processed += 1
            except Exception as exc:
                failed += 1
                logger.exception(
                    "partner_billing_cycle_worker_error cycle_id=%s error=%s",
                    cycle_id,
                    str(exc),
                )
        return {
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "scanned": len(cycle_ids),
        }
    finally:
        db.close()


def run() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    poll = int(os.getenv("PARTNER_BILLING_CYCLE_POLL_SEC", "30"))
    batch = int(os.getenv("PARTNER_BILLING_CYCLE_BATCH_SIZE", "100"))
    logger.info(
        "partner_billing_cycle_worker_started poll_sec=%s batch_size=%s",
        poll,
        batch,
    )
    while True:
        try:
            result = process_batch_once(batch)
            logger.info(
                "partner_billing_cycle_worker_cycle processed=%s skipped=%s failed=%s scanned=%s",
                result["processed"],
                result["skipped"],
                result["failed"],
                result["scanned"],
            )
        except Exception as exc:
            logger.exception("partner_billing_cycle_worker_cycle_failed error=%s", str(exc))
        time.sleep(poll)


if __name__ == "__main__":
    run()
