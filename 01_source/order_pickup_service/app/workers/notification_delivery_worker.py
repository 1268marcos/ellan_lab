# 01_source/order_pickup_service/app/workers/notification_delivery_worker.py
from __future__ import annotations

import time
from datetime import datetime, timedelta

from sqlalchemy import and_, or_, update
from sqlalchemy.orm import Session

from app.core.db import SessionLocal, init_db
from app.models.notification_log import NotificationLog
from app.services.email_notification_service import (
    send_receipt_email,
    send_pickup_email,
)

# IMPORTAR TODOS OS MODELS
from app.models import user  # noqa
from app.models import order  # noqa
from app.models import allocation  # noqa
from app.models import pickup  # noqa
from app.models import pickup_token  # noqa
from app.models import auth_session  # noqa
from app.models import notification_log  # noqa
from app.models import fiscal_document  # noqa


MAX_ATTEMPTS = 5
POLL_SEC = 5
BATCH_SIZE = 20
PROCESSING_STALE_TIMEOUT_SEC = 180
SUPPORTED_TEMPLATE_KEYS = {"RECEIPT", "PICKUP"}


def _utcnow() -> datetime:
    return datetime.utcnow()


def _compute_next_attempt_at(attempt_count: int) -> datetime:
    delays = {
        1: 30,
        2: 60,
        3: 120,
        4: 300,
    }
    delay_sec = delays.get(attempt_count, 600)
    return _utcnow() + timedelta(seconds=delay_sec)


def _recover_stale_processing_items(db: Session) -> None:
    now = _utcnow()
    stale_before = now - timedelta(seconds=PROCESSING_STALE_TIMEOUT_SEC)

    stale_items = (
        db.query(NotificationLog)
        .filter(
            NotificationLog.channel == "EMAIL",
            NotificationLog.template_key.in_(SUPPORTED_TEMPLATE_KEYS),
            NotificationLog.status == "PROCESSING",
            NotificationLog.processing_started_at.is_not(None),
            NotificationLog.processing_started_at <= stale_before,
        )
        .order_by(NotificationLog.processing_started_at.asc(), NotificationLog.id.asc())
        .limit(BATCH_SIZE)
        .all()
    )

    for item in stale_items:
        if (item.attempt_count or 0) >= MAX_ATTEMPTS:
            item.status = "DEAD"
            item.error_message = "PROCESSING_STALE_TIMEOUT_MAX_ATTEMPTS"
            item.failed_at = now
            item.processing_started_at = None
            item.next_attempt_at = None
            db.commit()
            continue

        item.status = "FAILED"
        item.error_message = "PROCESSING_STALE_TIMEOUT"
        item.failed_at = now
        item.processing_started_at = None
        item.next_attempt_at = now
        db.commit()


def _find_candidate_ids(db: Session) -> list[int]:
    now = _utcnow()

    rows = (
        db.query(NotificationLog.id)
        .filter(
            NotificationLog.channel == "EMAIL",
            NotificationLog.template_key.in_(SUPPORTED_TEMPLATE_KEYS),
            or_(
                NotificationLog.status == "QUEUED",
                and_(
                    NotificationLog.status == "FAILED",
                    NotificationLog.next_attempt_at.is_not(None),
                    NotificationLog.next_attempt_at <= now,
                ),
            ),
        )
        .order_by(NotificationLog.created_at.asc(), NotificationLog.id.asc())
        .limit(BATCH_SIZE)
        .all()
    )

    return [row[0] for row in rows]


def _claim_item(db: Session, notification_id: int) -> NotificationLog | None:
    now = _utcnow()

    result = db.execute(
        update(NotificationLog)
        .where(
            NotificationLog.id == notification_id,
            NotificationLog.status.in_(["QUEUED", "FAILED"]),
        )
        .values(
            status="PROCESSING",
            processing_started_at=now,
            error_message=None,
        )
    )

    if (result.rowcount or 0) != 1:
        db.rollback()
        return None

    db.commit()
    return db.get(NotificationLog, notification_id)


def _mark_dead(db: Session, item: NotificationLog, message: str | None = None) -> None:
    item.status = "DEAD"
    item.error_message = message
    item.failed_at = item.failed_at or _utcnow()
    item.processing_started_at = None
    item.next_attempt_at = None
    db.commit()


def _mark_failed(db: Session, item: NotificationLog, exc: Exception) -> None:
    item.status = "FAILED" if (item.attempt_count or 0) < MAX_ATTEMPTS else "DEAD"
    item.error_message = str(exc)
    item.failed_at = _utcnow()
    item.processing_started_at = None

    if item.status == "FAILED":
        item.next_attempt_at = _compute_next_attempt_at(item.attempt_count or 0)
    else:
        item.next_attempt_at = None

    db.commit()


def _mark_sent(db: Session, item: NotificationLog) -> None:
    item.status = "SENT"
    item.error_message = None
    item.sent_at = _utcnow()
    item.failed_at = None
    item.processing_started_at = None
    item.next_attempt_at = None
    db.commit()


def _process_email_notification(db: Session, item: NotificationLog) -> None:
    payload = item.payload_json or {}
    template = item.template_key
    to_email = item.destination_value

    if not to_email:
        raise RuntimeError("destination_value ausente")

    if template == "RECEIPT":
        receipt_code = payload.get("receipt_code")
        order_id = payload.get("order_id") or item.order_id

        if not receipt_code:
            raise RuntimeError("receipt_code ausente")

        send_receipt_email(
            to_email=to_email,
            receipt_code=receipt_code,
            order_id=order_id,
        )
        return

    if template == "PICKUP":
        order_id = payload.get("order_id") or item.order_id
        qr_value = payload.get("qr_value")
        manual_code = payload.get("manual_code")
        expires_at = payload.get("expires_at")
        region = payload.get("region")
        locker_id = payload.get("locker_id")
        slot = payload.get("slot")

        if not qr_value:
            raise RuntimeError("qr_value ausente")

        if not manual_code:
            raise RuntimeError("manual_code ausente")

        send_pickup_email(
            to_email=to_email,
            order_id=order_id,
            qr_value=qr_value,
            manual_code=manual_code,
            expires_at=expires_at,
            region=region,
            locker_id=locker_id,
            slot=slot,
        )
        return

    raise RuntimeError(f"template_key não suportado: {template}")


def run_notification_delivery_once(db: Session) -> None:
    _recover_stale_processing_items(db)

    candidate_ids = _find_candidate_ids(db)

    for notification_id in candidate_ids:
        item = _claim_item(db, notification_id)
        if item is None:
            continue

        if (item.attempt_count or 0) >= MAX_ATTEMPTS:
            _mark_dead(db, item, "MAX_ATTEMPTS_EXCEEDED")
            continue

        try:
            item.attempt_count = (item.attempt_count or 0) + 1
            item.last_attempt_at = _utcnow()
            db.commit()

            _process_email_notification(db, item)

            _mark_sent(db, item)

        except Exception as exc:
            _mark_failed(db, item, exc)


def main() -> None:
    init_db()

    while True:
        db = SessionLocal()
        try:
            run_notification_delivery_once(db)
        finally:
            db.close()

        time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()