# 01_source/backend/order_lifecycle_service/app/workers/prepayment_timeout_worker.py
import logging
import time
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.logging import configure_logging
from app.models.lifecycle import DeadlineStatus, DeadlineType, LifecycleDeadline
from app.services.deadline_engine import execute_prepayment_timeout
from app.services.event_publisher import publish_pending_events

configure_logging()
logger = logging.getLogger(__name__)


def utc_now():
    return datetime.now(timezone.utc)


def claim_due_deadline_ids(db: Session, batch_size: int = 100) -> list[UUID]:
    stmt = (
        select(LifecycleDeadline)
        .where(LifecycleDeadline.deadline_type == DeadlineType.PREPAYMENT_TIMEOUT)
        .where(LifecycleDeadline.status == DeadlineStatus.PENDING)
        .where(LifecycleDeadline.due_at <= utc_now())
        .order_by(LifecycleDeadline.due_at.asc())
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )

    rows = db.execute(stmt).scalars().all()

    now = utc_now()
    ids: list[UUID] = []

    for row in rows:
        row.status = DeadlineStatus.EXECUTING
        row.locked_at = now
        row.updated_at = now
        ids.append(row.id)

    return ids


def run_once() -> None:
    with SessionLocal() as db:
        deadline_ids = claim_due_deadline_ids(db)
        db.commit()

    processed = 0

    for deadline_id in deadline_ids:
        try:
            with SessionLocal() as tx:
                current = tx.get(LifecycleDeadline, deadline_id)
                if current is None:
                    continue

                if current.status != DeadlineStatus.EXECUTING:
                    continue

                execute_prepayment_timeout(tx, current)
                publish_pending_events(tx)
                tx.commit()
                processed += 1

        except Exception:
            logger.exception(
                "deadline_execution_failed",
                extra={"deadline_id": str(deadline_id)},
            )
            with SessionLocal() as err_tx:
                current = err_tx.get(LifecycleDeadline, deadline_id)
                if current is not None and current.status == DeadlineStatus.EXECUTING:
                    current.status = DeadlineStatus.FAILED
                    current.failure_count += 1
                    current.updated_at = utc_now()
                    err_tx.commit()

    if processed:
        logger.info("worker_cycle_processed", extra={"processed": processed})


def main():
    logger.info(
        "prepayment_timeout_worker_started",
        extra={
            "poll_interval_seconds": settings.worker_poll_interval_seconds,
            "prepayment_timeout_seconds": settings.prepayment_timeout_seconds,
        },
    )
    while True:
        run_once()
        time.sleep(settings.worker_poll_interval_seconds)


if __name__ == "__main__":
    main()