from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timedelta, timezone

from app.core.db import SessionLocal
from app.services.partner_billing_utilization_service import recompute_daily_utilization_snapshot

logger = logging.getLogger(__name__)


def _target_date() -> datetime.date:
    lag_days = int(os.getenv("PARTNER_BILLING_UTILIZATION_LAG_DAYS", "1"))
    return (datetime.now(timezone.utc) - timedelta(days=lag_days)).date()


def process_once() -> dict:
    db = SessionLocal()
    try:
        return recompute_daily_utilization_snapshot(db, snapshot_date=_target_date())
    finally:
        db.close()


def run() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    poll_sec = int(os.getenv("PARTNER_BILLING_UTILIZATION_POLL_SEC", "3600"))
    logger.info("partner_billing_utilization_worker_started poll_sec=%s", poll_sec)
    while True:
        try:
            result = process_once()
            logger.info(
                "partner_billing_utilization_worker_cycle snapshot_date=%s processed=%s",
                result.get("snapshot_date"),
                result.get("processed"),
            )
        except Exception:
            logger.exception("partner_billing_utilization_worker_failed")
        time.sleep(poll_sec)


if __name__ == "__main__":
    run()

