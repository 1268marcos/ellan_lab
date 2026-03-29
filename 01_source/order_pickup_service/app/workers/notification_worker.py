# 01_source/order_pickup_service/app/workers/notification_worker.py
from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.notification_log import NotificationLog
from app.services.email_notification_service import send_receipt_email


def run_worker():
    while True:
        db: Session = SessionLocal()

        try:
            pending = (
                db.query(NotificationLog)
                .filter(NotificationLog.status == "QUEUED")
                .order_by(NotificationLog.created_at.asc())
                .limit(10)
                .all()
            )

            for item in pending:
                try:
                    send_receipt_email(
                        to_email=item.destination_masked,  # ajustar depois
                        receipt_code="TODO",
                        order_id=item.order_id,
                    )

                    item.status = "SENT"
                    item.sent_at = datetime.now(timezone.utc)

                except Exception as e:
                    item.status = "FAILED"
                    item.error_message = str(e)

                db.commit()

        finally:
            db.close()

        time.sleep(3)
