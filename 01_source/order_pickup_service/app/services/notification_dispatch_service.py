# 01_source/order_pickup_service/app/services/notification_dispatch_service.py
from __future__ import annotations

from datetime import datetime

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


def queue_receipt_email(
    *,
    db: Session,
    order_id: str,
    email: str,
    receipt_code: str,
) -> NotificationLog:
    normalized_email = str(email or "").strip().lower()

    # 🔑 Gerar chave de deduplicação
    dedupe_key = f"EMAIL|RECEIPT|{normalized_email}|{receipt_code}"

    # 🔒 IDEMPOTÊNCIA FORTE
    existing = (
        db.query(NotificationLog)
        .filter(
            NotificationLog.channel == "EMAIL",
            NotificationLog.template_key == "RECEIPT",
            NotificationLog.destination_value == normalized_email,
            NotificationLog.payload_json["receipt_code"].as_string() == receipt_code,
            NotificationLog.status.in_(["QUEUED", "PROCESSING", "SENT"]),
        )
        .first()
    )

    if existing:
        return existing

    log = NotificationLog(
        user_id=None,
        order_id=order_id,
        channel="EMAIL",
        template_key="RECEIPT",
        destination_masked=_mask_email(normalized_email),
        destination_value=normalized_email,
        provider_name="SMTP",
        provider_message_id=None,
        status="QUEUED",
        attempt_count=0,
        error_message=None,
        payload_json={
            "receipt_code": receipt_code,
            "order_id": order_id,
        },
        dedupe_key=dedupe_key,  # 🆕 Adicionando chave de deduplicação
        created_at=datetime.utcnow(),
        sent_at=None,
        delivered_at=None,
        failed_at=None,
    )

    db.add(log)
    db.commit()
    db.refresh(log)
    return log