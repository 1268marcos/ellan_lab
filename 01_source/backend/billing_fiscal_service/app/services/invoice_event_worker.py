# 01_source/backend/biling_fiscal_service/app/services/invoice_event_worker.py
from __future__ import annotations

import logging
import os
import socket
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.external_domain_event import DomainEvent
from app.models.invoice_model import Invoice, InvoiceStatus
from app.services.invoice_orchestrator import ensure_and_process_invoice

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _worker_id() -> str:
    host = socket.gethostname()
    pid = os.getpid()
    return f"billing_invoice_worker:{host}:{pid}"


def _iter_candidate_order_paid_events(db: Session, limit: int) -> list[DomainEvent]:
    stmt = (
        select(DomainEvent)
        .where(DomainEvent.aggregate_type == "order")
        .where(DomainEvent.event_name == "order.paid")
        .order_by(DomainEvent.created_at.asc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def _should_process_invoice(invoice: Invoice | None) -> bool:
    if invoice is None:
        return True

    if invoice.status in (InvoiceStatus.PENDING, InvoiceStatus.FAILED):
        return True

    return False


def _get_invoice_by_order(db: Session, order_id: str) -> Invoice | None:
    return (
        db.query(Invoice)
        .filter(Invoice.order_id == str(order_id).strip())
        .first()
    )


def process_pending_order_paid_events_once(
    *,
    batch_size: int = 100,
) -> dict:
    processed = 0
    skipped = 0
    failed = 0

    db = SessionLocal()
    try:
        events = _iter_candidate_order_paid_events(db, batch_size)

        for event in events:
            order_id = str(event.aggregate_id).strip()

            try:
                invoice = _get_invoice_by_order(db, order_id)

                if not _should_process_invoice(invoice):
                    skipped += 1
                    continue

                invoice = ensure_and_process_invoice(db, order_id)

                if invoice.status == InvoiceStatus.ISSUED:
                    processed += 1
                else:
                    failed += 1

            except Exception:
                failed += 1
                logger.exception(
                    "invoice_event_worker_failed",
                    extra={
                        "order_id": order_id,
                        "event_key": event.event_key,
                        "event_name": event.event_name,
                    },
                )
                db.rollback()

        return {
            "ok": True,
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "scanned": len(events),
        }
    finally:
        db.close()


def run_invoice_event_worker_forever(
    *,
    poll_interval_sec: int = 10,
    batch_size: int = 100,
) -> None:
    wid = _worker_id()

    logger.info(
        "invoice_event_worker_started",
        extra={
            "worker_id": wid,
            "poll_interval_sec": poll_interval_sec,
            "batch_size": batch_size,
        },
    )

    while True:
        started_at = _utc_now()

        try:
            result = process_pending_order_paid_events_once(batch_size=batch_size)
            logger.info(
                "invoice_event_worker_cycle",
                extra={
                    "worker_id": wid,
                    **result,
                },
            )
        except Exception:
            logger.exception(
                "invoice_event_worker_cycle_failed",
                extra={"worker_id": wid},
            )

        elapsed = (_utc_now() - started_at).total_seconds()
        sleep_for = max(1, int(poll_interval_sec - elapsed))
        time.sleep(sleep_for)

