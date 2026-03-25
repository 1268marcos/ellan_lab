# 01_source/order_pickup_service/app/workers/notification_delivery_worker.py
from __future__ import annotations

import time
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.db import SessionLocal, init_db
from app.models.notification_log import NotificationLog
from app.services.email_notification_service import send_receipt_email

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


def run_notification_delivery_once(db: Session) -> None:
    pending = (
        db.query(NotificationLog)
        .filter(NotificationLog.status.in_(["QUEUED", "FAILED"]))
        .order_by(NotificationLog.created_at.asc(), NotificationLog.id.asc())
        .limit(20)
        .all()
    )

    for item in pending:
        if item.channel != "EMAIL" or item.template_key != "RECEIPT":
            continue

        if (item.attempt_count or 0) >= MAX_ATTEMPTS:
            item.status = "DEAD"
            item.failed_at = item.failed_at or datetime.utcnow()
            db.commit()
            continue

        try:
            # 🔒 MARCA COMO PROCESSANDO (lock lógico)
            item.status = "PROCESSING"
            db.commit()

            payload = item.payload_json or {}
            receipt_code = payload.get("receipt_code")
            order_id = payload.get("order_id") or item.order_id
            to_email = item.destination_value

            if not to_email:
                raise RuntimeError("destination_value ausente em notification_logs")

            if not receipt_code:
                raise RuntimeError("receipt_code ausente em payload_json")

            # incrementa UMA vez por tentativa real
            item.attempt_count = (item.attempt_count or 0) + 1

            send_receipt_email(
                to_email=to_email,
                receipt_code=receipt_code,
                order_id=order_id,
            )

            item.status = "SENT"
            item.error_message = None
            item.sent_at = datetime.utcnow()
            item.failed_at = None
            db.commit()

        except Exception as exc:
            item.status = "FAILED" if item.attempt_count < MAX_ATTEMPTS else "DEAD"
            item.error_message = str(exc)
            item.failed_at = datetime.utcnow()
            db.commit()


def main() -> None:
    # worker autossuficiente:
    # cria tabelas ausentes, roda migration se habilitada
    # e valida schema antes de entrar no loop.
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