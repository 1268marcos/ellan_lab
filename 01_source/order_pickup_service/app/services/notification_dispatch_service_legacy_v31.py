# 01_source/order_pickup_service/app/services/notification_dispatch_service.py
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.notification_log import NotificationLog


def _mask_email(email: str) -> str:
    value = (email or "").strip().lower()
    if "@" not in value:
        return value

    name, domain = value.split("@", 1)
    if len(name) <= 2:
        masked_name = name[0] + "***" if name else "***"
    else:
        masked_name = name[:2] + "***"

    return f"{masked_name}@{domain}"


def _queue_email_notification(
    *,
    db: Session,
    order_id: str,
    email: str,
    template_key: str,
    dedupe_key: str,
    payload_json: dict,
) -> NotificationLog:
    normalized_email = str(email or "").strip().lower()

    existing = (
        db.query(NotificationLog)
        .filter(NotificationLog.dedupe_key == dedupe_key)
        .first()
    )
    if existing:
        return existing

    now = datetime.now(timezone.utc)

    log = NotificationLog(
        user_id=None,
        order_id=order_id,
        channel="EMAIL",
        template_key=template_key,
        destination_masked=_mask_email(normalized_email),
        destination_value=normalized_email,
        dedupe_key=dedupe_key,
        provider_name="SMTP",
        provider_message_id=None,
        status="QUEUED",
        attempt_count=0,
        error_message=None,
        payload_json=payload_json,
        processing_started_at=None,
        last_attempt_at=None,
        next_attempt_at=now,
        created_at=now,
        sent_at=None,
        delivered_at=None,
        failed_at=None,
    )

    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def queue_receipt_email(
    *,
    db: Session,
    order_id: str,
    email: str,
    receipt_code: str,
) -> NotificationLog:
    normalized_email = str(email or "").strip().lower()
    normalized_receipt_code = str(receipt_code or "").strip().upper()
    dedupe_key = f"EMAIL|RECEIPT|{normalized_email}|{normalized_receipt_code}"

    return _queue_email_notification(
        db=db,
        order_id=order_id,
        email=normalized_email,
        template_key="RECEIPT",
        dedupe_key=dedupe_key,
        payload_json={
            "receipt_code": normalized_receipt_code,
            "order_id": order_id,
        },
    )


def queue_pickup_email(
    *,
    db: Session,
    order_id: str,
    email: str,
    qr_value: str,
    manual_code: str,
    expires_at: str | None,
    region: str | None,
    locker_id: str | None,
    slot: str | None,
) -> NotificationLog:
    normalized_email = str(email or "").strip().lower()
    normalized_manual_code = str(manual_code or "").strip()
    dedupe_key = f"EMAIL|PICKUP|{normalized_email}|{order_id}"

    return _queue_email_notification(
        db=db,
        order_id=order_id,
        email=normalized_email,
        template_key="PICKUP",
        dedupe_key=dedupe_key,
        payload_json={
            "order_id": order_id,
            "qr_value": qr_value,
            "manual_code": normalized_manual_code,
            "expires_at": expires_at,
            "region": region,
            "locker_id": locker_id,
            "slot": slot,
        },
    )