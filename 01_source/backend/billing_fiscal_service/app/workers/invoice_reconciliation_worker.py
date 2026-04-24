from __future__ import annotations

import logging
import os
import time

from app.core.db import SessionLocal
from app.services.fiscal_reconciliation_service import scan_and_persist_reconciliation_gaps

logger = logging.getLogger(__name__)


def run():
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    poll = int(os.getenv("INVOICE_RECONCILIATION_POLL_SEC", "60"))
    lookback_days = int(os.getenv("INVOICE_RECONCILIATION_LOOKBACK_DAYS", "7"))
    limit = int(os.getenv("INVOICE_RECONCILIATION_LIMIT_PER_TYPE", "500"))
    logger.info(
        "invoice_reconciliation_worker_started poll_sec=%s lookback_days=%s limit_per_type=%s",
        poll,
        lookback_days,
        limit,
    )

    while True:
        db = SessionLocal()
        try:
            result = scan_and_persist_reconciliation_gaps(
                db,
                lookback_days=lookback_days,
                limit_per_type=limit,
            )
            logger.info(
                "invoice_reconciliation_worker_cycle paid_without_invoice=%s "
                "issued_without_paid=%s open_total=%s created=%s updated=%s resolved=%s",
                result["paid_without_invoice"],
                result["issued_without_paid"],
                result["open_total"],
                result["created"],
                result["updated"],
                result["resolved"],
            )
        except Exception:
            logger.exception("invoice_reconciliation_worker_cycle_failed")
        finally:
            db.close()
        time.sleep(poll)


if __name__ == "__main__":
    run()
