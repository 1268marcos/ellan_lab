from __future__ import annotations

import logging
import os
import time
from datetime import date, datetime, timezone

from app.core.db import SessionLocal
from app.services.financial_pnl_service import recompute_monthly_pnl

logger = logging.getLogger(__name__)


def _target_month() -> date:
    lag_months = int(os.getenv("PARTNER_BILLING_PNL_LAG_MONTHS", "1"))
    now = datetime.now(timezone.utc).date()
    year = now.year
    month = now.month - lag_months
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


def process_once() -> dict:
    db = SessionLocal()
    try:
        return recompute_monthly_pnl(db, month=_target_month())
    finally:
        db.close()


def run() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    poll_sec = int(os.getenv("PARTNER_BILLING_PNL_POLL_SEC", "21600"))
    logger.info("partner_financial_pnl_worker_started poll_sec=%s", poll_sec)
    while True:
        try:
            result = process_once()
            logger.info(
                "partner_financial_pnl_worker_cycle month=%s pnl_upserted=%s depreciation_upserted=%s",
                result.get("month"),
                result.get("pnl_upserted"),
                result.get("depreciation_upserted"),
            )
        except Exception:
            logger.exception("partner_financial_pnl_worker_failed")
        time.sleep(poll_sec)


if __name__ == "__main__":
    run()
