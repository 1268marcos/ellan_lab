# 01_source/order_pickup_service/app/workers/domain_event_outbox_worker.py
# 10/04/2026 - revisão de payload / json


from __future__ import annotations

import logging
import os
import time
import json

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.domain_event_outbox import DomainEventOutbox
from app.services.lifecycle_domain_event_client import (
    LifecycleDomainEventClientError,
    publish_domain_event,
)

logger = logging.getLogger("domain_event_outbox_worker")

POLL_SEC = int(os.getenv("DOMAIN_EVENT_OUTBOX_POLL_SEC", "5"))
BATCH_SIZE = int(os.getenv("DOMAIN_EVENT_OUTBOX_BATCH_SIZE", "50"))


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _claim_batch(db: Session) -> list[dict]:
    rows = (
        db.query(DomainEventOutbox)
        .filter(DomainEventOutbox.status.in_(["PENDING", "FAILED"]))
        .order_by(DomainEventOutbox.created_at.asc())
        .limit(BATCH_SIZE)
        .all()
    )

    claimed: list[dict] = []
    now = _utc_now_naive()

    for row in rows:
        row.status = "PROCESSING"
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
            }
        )

    if rows:
        db.commit()

    return claimed


def _mark_published(db: Session, row_id: str) -> None:
    row = db.query(DomainEventOutbox).filter(DomainEventOutbox.id == row_id).first()
    if not row:
        return

    now = _utc_now_naive()
    row.status = "PUBLISHED"
    row.published_at = now
    row.last_error = None
    row.updated_at = now
    db.commit()


def _mark_failed(db: Session, row_id: str, error_message: str) -> None:
    row = db.query(DomainEventOutbox).filter(DomainEventOutbox.id == row_id).first()
    if not row:
        return

    row.status = "FAILED"
    row.last_error = (error_message or "")[:4000]
    row.updated_at = _utc_now_naive()
    db.commit()

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

    payload = {
        "event_key": row["event_key"],
        "aggregate_type": row["aggregate_type"],
        "aggregate_id": row["aggregate_id"],
        "event_name": row["event_name"],
        "event_version": row["event_version"],
        "payload": parsed_payload,
        "occurred_at": row["occurred_at"],
    }

    publish_domain_event(payload)



    

def run() -> None:
    logger.info("domain_event_outbox_worker_started")

    while True:
        db = SessionLocal()
        try:
            rows = _claim_batch(db)
        finally:
            db.close()

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

                logger.info(
                    "domain_event_outbox_published",
                    extra={
                        "event_key": row["event_key"],
                        "event_name": row["event_name"],
                        "aggregate_id": row["aggregate_id"],
                    },
                )

            except LifecycleDomainEventClientError as exc:
                db3 = SessionLocal()
                try:
                    _mark_failed(db3, row["id"], str(exc))
                finally:
                    db3.close()

                # logger.error(
                logger.exception(
                    "domain_event_outbox_publish_failed",
                    extra={
                        "event_key": row["event_key"],
                        "event_name": row["event_name"],
                        "aggregate_id": row["aggregate_id"],
                        "error": str(exc),
                    },
                )

            except Exception as exc:
                db4 = SessionLocal()
                try:
                    _mark_failed(db4, row["id"], str(exc))
                finally:
                    db4.close()

                logger.exception(
                    "domain_event_outbox_unexpected_error",
                    extra={
                        "event_key": row["event_key"],
                        "event_name": row["event_name"],
                        "aggregate_id": row["aggregate_id"],
                    },
                )

        time.sleep(POLL_SEC)


if __name__ == "__main__":
    run()