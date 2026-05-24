from __future__ import annotations

import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services import finance_jobs_service as jobs_svc

logger = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


def _run_job_safe(job_code: str) -> None:
    db = SessionLocal()
    try:
        result = jobs_svc.run_job(db, job_code)
        logger.info("scheduled_job %s status=%s", job_code, result.get("status"))
    except Exception:
        logger.exception("scheduled_job_failed job=%s", job_code)
    finally:
        db.close()


def start_finance_scheduler() -> None:
    global _scheduler
    settings = get_settings()
    if not settings.enable_finance_scheduler:
        return
    if _scheduler is not None:
        return

    tz = ZoneInfo(settings.finance_scheduler_timezone)
    _scheduler = BackgroundScheduler(timezone=tz)
    _scheduler.add_job(lambda: _run_job_safe("DUNNING_SCAN"), "cron", hour=settings.finance_dunning_cron_hour, minute=0)
    _scheduler.add_job(
        lambda: _run_job_safe("SETTLEMENT_RECONCILE"),
        "cron",
        hour=settings.finance_reconcile_cron_hour,
        minute=15,
    )
    _scheduler.add_job(
        lambda: _run_job_safe("REVENUE_RECOGNITION"),
        "cron",
        hour=settings.finance_revrec_cron_hour,
        minute=30,
    )
    _scheduler.add_job(
        lambda: _run_job_safe("FISCAL_GAP_SYNC"),
        "cron",
        hour=settings.finance_fiscal_gap_cron_hour,
        minute=45,
    )
    _scheduler.add_job(
        lambda: _run_job_safe("READINESS_RECOMPUTE"),
        "cron",
        hour=6,
        minute=0,
    )
    _scheduler.add_job(
        lambda: _run_job_safe("ECOSYSTEM_INTELLIGENCE_SCAN"),
        "cron",
        hour=6,
        minute=30,
    )
    _scheduler.start()
    logger.info("finance_scheduler_started tz=%s", settings.finance_scheduler_timezone)


def stop_finance_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("finance_scheduler_stopped")
