# 01_source/backend/billing_fiscal_service/app/workers/invoice_event_worker.py
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.external_domain_event import DomainEvent
from app.models.invoice_model import Invoice
from app.services.invoice_orchestrator import ensure_and_process_invoice

logger = logging.getLogger(__name__)


def _utc_now():
    return datetime.now(timezone.utc)


def _get_order_paid_events(db: Session, limit: int):
    stmt = (
        select(DomainEvent)
        .where(DomainEvent.aggregate_type == "order")
        .where(DomainEvent.event_name == "order.paid")
        .order_by(DomainEvent.created_at.asc())
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


def _invoice_exists(db: Session, order_id: str) -> bool:
    return (
        db.query(Invoice)
        .filter(Invoice.order_id == order_id)
        .first()
        is not None
    )


def process_events_once(batch_size: int):
    db = SessionLocal()

    processed = 0
    skipped = 0
    failed = 0

    try:
        events = _get_order_paid_events(db, batch_size)

        for event in events:
            order_id = str(event.aggregate_id)

            try:
                if _invoice_exists(db, order_id):
                    skipped += 1
                    continue

                ensure_and_process_invoice(db, order_id)
                processed += 1

            except Exception:
                failed += 1
                logger.exception(
                    "invoice_event_worker_error",
                    extra={
                        "order_id": order_id,
                        "event_key": event.event_key,
                    },
                )
                db.rollback()

        return {
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "scanned": len(events),
        }

    finally:
        db.close()


def run():
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    poll = int(os.getenv("INVOICE_EVENT_WORKER_POLL_SEC", "10"))
    batch = int(os.getenv("INVOICE_EVENT_WORKER_BATCH_SIZE", "100"))

    logger.info("invoice_event_worker_started")

    while True:
        try:
            result = process_events_once(batch)
            logger.info("invoice_event_worker_cycle", extra=result)
        except Exception:
            logger.exception("invoice_event_worker_cycle_failed")

        time.sleep(poll)


if __name__ == "__main__":
    run()
