# 01_source/order_pickup_service/app/workers/domain_event_outbox_worker.py
# 10/04/2026 - revisão de payload / json
# 11/04/2026 - inclusão import DomainEventEnvelope e OrderPaidPayload
# 11/04/2026 - inclusão helper de backoff def _next_retry_at_for() / substituição def _claim_batch() /
#              substituição def _mark_published() / substituição def _mark_failed()

from __future__ import annotations

import logging
import os
import time
import json

from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.domain_event_outbox import DomainEventOutbox
from app.services.lifecycle_domain_event_client import (
    LifecycleDomainEventClientError,
    publish_domain_event,
)


from app.schemas.domain_events import DomainEventEnvelope, OrderPaidPayload


logger = logging.getLogger("domain_event_outbox_worker")

POLL_SEC = int(os.getenv("DOMAIN_EVENT_OUTBOX_POLL_SEC", "5"))
BATCH_SIZE = int(os.getenv("DOMAIN_EVENT_OUTBOX_BATCH_SIZE", "50"))


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)



def _next_retry_at_for(retry_count: int) -> datetime:
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if retry_count <= 1:
        return now + timedelta(seconds=15)
    if retry_count == 2:
        return now + timedelta(seconds=60)
    if retry_count == 3:
        return now + timedelta(minutes=5)

    return now + timedelta(minutes=15)



# def _claim_batch(db: Session) -> list[dict]:
#         db.query(DomainEventOutbox)
#     rows = (
#         .filter(DomainEventOutbox.status.in_(["PENDING", "FAILED"]))
#         .order_by(DomainEventOutbox.created_at.asc())
#         .limit(BATCH_SIZE)
#         .all()
#     )
# 
#     claimed: list[dict] = []
#     now = _utc_now_naive()
# 
#     for row in rows:
#         row.status = "PROCESSING"
#         row.updated_at = now
# 
#         claimed.append(
#             {
#                 "id": row.id,
#                 "event_key": row.event_key,
#                 "aggregate_type": row.aggregate_type,
#                 "aggregate_id": row.aggregate_id,
#                 "event_name": row.event_name,
#                 "event_version": int(row.event_version),
#                 "payload_json": row.payload_json,
#                 "occurred_at": row.occurred_at.isoformat(),
#             }
#         )
# 
#     if rows:
#         db.commit()
# 
#     return claimed
def _claim_batch(db: Session) -> list[dict]:
    now = _utc_now_naive()
    stale_processing_before = now - timedelta(minutes=5)

    rows = (
        db.query(DomainEventOutbox)
        .filter(
            (
                DomainEventOutbox.status == "PENDING"
            )
            |
            (
                (DomainEventOutbox.status == "FAILED")
                & (
                    (DomainEventOutbox.next_retry_at.is_(None))
                    | (DomainEventOutbox.next_retry_at <= now)
                )
            )
            |
            (
                (DomainEventOutbox.status == "PROCESSING")
                & (DomainEventOutbox.processing_started_at <= stale_processing_before)
            )
        )
        .order_by(DomainEventOutbox.created_at.asc())
        .limit(BATCH_SIZE)
        .all()
    )

    claimed: list[dict] = []

    for row in rows:
        row.status = "PROCESSING"
        row.processing_started_at = now
        row.updated_at = now

        claimed.append(
            {
                "id": row.id,
                "event_key": row.event_key,
                "aggregate_type": row.aggregate_type,
                "aggregate_id": row.aggregate_id,
                "event_name": row.event_name,
                "event_version": int(row.event_version),
                "payload_json": row.payload_json,
                "occurred_at": row.occurred_at.isoformat(),
                "retry_count": int(getattr(row, "retry_count", 0) or 0),
            }
        )

    if rows:
        db.commit()

    return claimed




# def _mark_published(db: Session, row_id: str) -> None:
#     row = db.query(DomainEventOutbox).filter(DomainEventOutbox.id == row_id).first()
#     if not row:
#         return
# 
#     now = _utc_now_naive()
#     row.status = "PUBLISHED"
#     row.published_at = now
#     row.last_error = None
#     row.updated_at = now
#     db.commit()
def _mark_published(db: Session, row_id: str) -> None:
    row = db.query(DomainEventOutbox).filter(DomainEventOutbox.id == row_id).first()
    if not row:
        return

    now = _utc_now_naive()
    row.status = "PUBLISHED"
    row.published_at = now
    row.last_error = None
    row.processing_started_at = None
    row.next_retry_at = None
    row.updated_at = now
    db.commit()


# def _mark_failed(db: Session, row_id: str, error_message: str) -> None:
#     row = db.query(DomainEventOutbox).filter(DomainEventOutbox.id == row_id).first()
#     if not row:
#         return
# 
#     row.status = "FAILED"
#     row.last_error = (error_message or "")[:4000]
#     row.updated_at = _utc_now_naive()
#     db.commit()
def _mark_failed(db: Session, row_id: str, error_message: str) -> None:
    row = db.query(DomainEventOutbox).filter(DomainEventOutbox.id == row_id).first()
    if not row:
        return

    retry_count = int(getattr(row, "retry_count", 0) or 0) + 1
    row.retry_count = retry_count
    row.status = "FAILED"
    row.last_error = (error_message or "")[:4000]
    row.next_retry_at = _next_retry_at_for(retry_count)
    row.processing_started_at = None
    row.updated_at = _utc_now_naive()
    db.commit()



# def _process_one(row: dict) -> None:
#     raw_payload = row["payload_json"]
# 
#     if isinstance(raw_payload, str):
#         parsed_payload = json.loads(raw_payload)
#     elif isinstance(raw_payload, dict):
#         parsed_payload = raw_payload
#     else:
#         raise ValueError(
#             f"payload_json inválido para domain event outbox: type={type(raw_payload).__name__}"
#         )
# 
#     payload = {
#         "event_key": row["event_key"],
#         "aggregate_type": row["aggregate_type"],
#         "aggregate_id": row["aggregate_id"],
#         "event_name": row["event_name"],
#         "event_version": row["event_version"],
#         "payload": parsed_payload,
#         "occurred_at": row["occurred_at"],
#     }
# 
#     publish_domain_event(payload)
def _process_one(row: dict) -> None:
    raw_payload = row["payload_json"]

    if isinstance(raw_payload, str):
        parsed_payload = json.loads(raw_payload)
    elif isinstance(raw_payload, dict):
        parsed_payload = raw_payload
    else:
        raise ValueError(
            f"payload_json inválido para domain event outbox: type={type(raw_payload).__name__}"
        )

    # valida payload tipado para order.paid
    if row["event_name"] == "order.paid":
        parsed_payload = OrderPaidPayload.model_validate(parsed_payload).model_dump()

    envelope = DomainEventEnvelope(
        event_key=row["event_key"],
        aggregate_type=row["aggregate_type"],
        aggregate_id=row["aggregate_id"],
        event_name=row["event_name"],
        event_version=row["event_version"],
        payload=parsed_payload,
        occurred_at=row["occurred_at"],
    )

    publish_domain_event(envelope.model_dump())


    

def run() -> None:
    logger.info("domain_event_outbox_worker_started")

    while True:
        db = SessionLocal()
        try:
            rows = _claim_batch(db)
        finally:
            db.close()

        # Log do resumo do ciclo - movido para depois que rows é definida
        logger.info(
            "domain_event_outbox_worker_cycle processed=%s batch_size=%s",
            len(rows),
            BATCH_SIZE,
        )


        if not rows:
            time.sleep(POLL_SEC)
            continue

        for row in rows:
            try:
                _process_one(row)

                db2 = SessionLocal()
                try:
                    _mark_published(db2, row["id"])
                finally:
                    db2.close()

                # logger.info(
                #     "domain_event_outbox_published",
                #     extra={
                #         "event_key": row["event_key"],
                #         "event_name": row["event_name"],
                #         "aggregate_id": row["aggregate_id"],
                #     },
                # )
                logger.info(
                    "domain_event_outbox_published event_key=%s event_name=%s aggregate_id=%s",
                    row["event_key"],
                    row["event_name"],
                    row["aggregate_id"],
                )

            except LifecycleDomainEventClientError as exc:
                db3 = SessionLocal()
                try:
                    _mark_failed(db3, row["id"], str(exc))
                finally:
                    db3.close()

                # logger.error(
                # logger.exception(
                #     "domain_event_outbox_publish_failed",
                #     extra={
                #         "event_key": row["event_key"],
                #         "event_name": row["event_name"],
                #         "aggregate_id": row["aggregate_id"],
                #         "error": str(exc),
                #     },
                # )
                logger.exception(
                    "domain_event_outbox_publish_failed event_key=%s event_name=%s aggregate_id=%s error=%s",
                    row["event_key"],
                    row["event_name"],
                    row["aggregate_id"],
                    str(exc),
                )


            except Exception as exc:
                db4 = SessionLocal()
                try:
                    _mark_failed(db4, row["id"], str(exc))
                finally:
                    db4.close()

                # logger.exception(
                #     "domain_event_outbox_unexpected_error",
                #     extra={
                #         "event_key": row["event_key"],
                #         "event_name": row["event_name"],
                #         "aggregate_id": row["aggregate_id"],
                #     },
                # )
                logger.exception(
                    "domain_event_outbox_unexpected_error event_key=%s event_name=%s aggregate_id=%s",
                    row["event_key"],
                    row["event_name"],
                    row["aggregate_id"],
                    exc_info=True,
                )


        time.sleep(POLL_SEC)


if __name__ == "__main__":
    run()