# 01_source/backend/billing_fiscal_service/app/workers/invoice_event_worker.py
# Esse worker passa a consultar somente order.paid que ainda não têm 
# invoice, evitando varrer histórico já materializado. 
# 10/04/2026 - alteração de funções : _mark_processed() e _already_processed()
# 10/04/2026 - exclusão da função: _get_events()
# 11/04/2026 - inclusão de error_message em def _mark_processed() / endurecer mensagem de erro 
# 11/04/2026 - aplicação de uma melhor blindagem de: except OrderPickupClientError para: except Exception

from __future__ import annotations

import logging
import os
import time

from sqlalchemy import outerjoin, select

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.external_domain_event import DomainEvent

from app.integrations.order_pickup_client import OrderPickupClientError

from app.models.invoice_model import Invoice
from app.services.invoice_orchestrator import ensure_and_process_invoice

from datetime import datetime, timezone
from app.models.processed_event import ProcessedEvent


logger = logging.getLogger(__name__)

MAX_EVENT_RETRIES = int(os.getenv("INVOICE_EVENT_MAX_RETRIES", "3"))


def _utc_now():
    return datetime.now(timezone.utc)


# def _get_events(db, batch_size):
#     return (
#         db.query(DomainEvent)
#         .filter(DomainEvent.aggregate_type == "order")
#         .filter(DomainEvent.event_name == "order.paid")
#         .order_by(DomainEvent.created_at.asc())
#         .limit(batch_size)
#         .all()
#     )


# def _already_processed(db, event_key: str) -> bool:
#     return (
#         db.query(ProcessedEvent)
#         .filter(ProcessedEvent.event_key == event_key)
#         .first()
#         is not None
#     )
def _already_processed(db, event_key: str) -> bool:
    record = (
        db.query(ProcessedEvent)
        .filter(ProcessedEvent.event_key == event_key)
        .order_by(ProcessedEvent.created_at.desc())
        .first()
    )

    if record is None:
        return False

    status = str(record.status or "").upper()

    # Só bloqueia se já concluiu com sucesso
    if status == "PROCESSED":
        return True

    # DEAD também pode bloquear definitivamente
    if status == "DEAD":
        return True

    # FAILED deve poder tentar de novo
    return False





# def _mark_processed(db, event, status: str, error: str | None = None):
#     record = ProcessedEvent(
#         event_key=event.event_key,
#         order_id=str(event.aggregate_id),
#         status=status,
#         error_message=error,
#         created_at=_utc_now(),
#     )
#     db.add(record)
#     db.commit()
def _mark_processed(db, event, status: str, error: str | None = None):
    error_message = str(error) if error else None

    if error_message and len(error_message) > 500:
        error_message = error_message[:500]

    record = (
        db.query(ProcessedEvent)
        .filter(ProcessedEvent.event_key == event.event_key)
        .first()
    )

    if record is None:
        record = ProcessedEvent(
            event_key=event.event_key,
            order_id=str(event.aggregate_id),
            status=status,
            error_message=error_message,
            created_at=_utc_now(),
        )
        db.add(record)
    else:
        record.status = status
        record.error_message = error_message

    db.commit()




def _get_order_paid_events_without_invoice(db, batch_size: int):
    join_stmt = outerjoin(
        DomainEvent,
        Invoice,
        DomainEvent.aggregate_id == Invoice.order_id,
    )

    stmt = (
        select(DomainEvent)
        .select_from(join_stmt)
        .where(DomainEvent.aggregate_type == "order")
        .where(DomainEvent.event_name == "order.paid")
        .where(Invoice.id.is_(None))
        .order_by(DomainEvent.created_at.asc())
        .limit(batch_size)
    )

    return list(db.execute(stmt).scalars().all())


def process_events_once(batch_size: int):
    db = SessionLocal()

    processed = 0
    skipped = 0
    failed = 0

    try:
        events = _get_order_paid_events_without_invoice(db, batch_size)

        for event in events:
            order_id = str(event.aggregate_id).strip()

            # 🔒 BLOQUEIO ANTES DE PROCESSAR
            if _already_processed(db, event.event_key):
                skipped += 1
                continue

            try:
                ensure_and_process_invoice(db, order_id)

                _mark_processed(db, event, "PROCESSED")
                processed += 1


            except Exception as exc:
                msg = str(exc).lower()

                # 💀 DEAD definitivo
                if "404" in msg or "order not found" in msg:
                    logger.warning(
                        "invoice_event_order_not_found_dead order_id=%s event_key=%s",
                        order_id,
                        event.event_key,
                    )

                    _mark_processed(db, event, "DEAD", "order_not_found")
                    skipped += 1
                    continue

                # ⚠️ erro transitório
                _mark_processed(db, event, "FAILED", str(exc))
                failed += 1

                logger.exception(
                    "invoice_event_worker_error order_id=%s event_key=%s",
                    order_id,
                    event.event_key,
                )   

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
            # logger.info("invoice_event_worker_cycle", extra=result)
            logger.info(
                "invoice_event_worker_cycle processed=%s skipped=%s failed=%s scanned=%s",
                result["processed"],
                result["skipped"],
                result["failed"],
                result["scanned"],
            )

        except Exception:
            logger.exception("invoice_event_worker_cycle_failed")

        time.sleep(poll)


if __name__ == "__main__":
    run()
