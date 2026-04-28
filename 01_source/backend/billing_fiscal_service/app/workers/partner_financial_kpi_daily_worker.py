from __future__ import annotations

import logging
import os
import time
from datetime import date, datetime, timedelta, timezone

from app.core.db import SessionLocal
from app.services.financial_pnl_service import recompute_daily_kpis, recompute_daily_revenue_recognition

logger = logging.getLogger(__name__)


def _target_date() -> date:
    lag_days = int(os.getenv("PARTNER_BILLING_KPI_DAILY_LAG_DAYS", "1"))
    return (datetime.now(timezone.utc) - timedelta(days=lag_days)).date()


def process_once() -> dict:
    db = SessionLocal()
    try:
        target = _target_date()
        revrec = recompute_daily_revenue_recognition(db, snapshot_date=target)
        kpi = recompute_daily_kpis(db, snapshot_date=target)
        return {"snapshot_date": target.isoformat(), **revrec, **kpi}
    finally:
        db.close()


def run() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    poll_sec = int(os.getenv("PARTNER_BILLING_KPI_DAILY_POLL_SEC", "3600"))
    logger.info("partner_financial_kpi_daily_worker_started poll_sec=%s", poll_sec)
    while True:
        try:
            out = process_once()
            logger.info(
                "partner_financial_kpi_daily_worker_cycle date=%s revrec_upserted=%s kpi_upserted=%s",
                out.get("snapshot_date"),
                out.get("revenue_recognition_upserted"),
                out.get("kpi_daily_upserted"),
            )
        except Exception:
            logger.exception("partner_financial_kpi_daily_worker_failed")
        time.sleep(poll_sec)


if __name__ == "__main__":
    run()
