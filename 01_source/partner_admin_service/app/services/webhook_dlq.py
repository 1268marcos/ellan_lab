from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

DEAD_LETTER_FAILURE_THRESHOLD = 3
STATUS_DELIVERED = "DELIVERED"
STATUS_FAILED = "FAILED"
STATUS_DEAD_LETTER = "DEAD_LETTER"
STATUS_SKIPPED = "SKIPPED"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def apply_delivery_status(db: Session, *, webhook_id: str, success: bool, response_snippet: str | None) -> str:
    if success:
        return STATUS_DELIVERED
    if response_snippet == "event_not_subscribed":
        return STATUS_SKIPPED
    from app.models.partner_capability_webhook import PartnerCapabilityWebhookDelivery

    fail_count = (
        db.query(PartnerCapabilityWebhookDelivery)
        .filter(
            PartnerCapabilityWebhookDelivery.webhook_id == webhook_id,
            PartnerCapabilityWebhookDelivery.status == STATUS_FAILED,
        )
        .count()
    )
    if fail_count + 1 >= DEAD_LETTER_FAILURE_THRESHOLD:
        return STATUS_DEAD_LETTER
    return STATUS_FAILED


def dead_lettered_at_for_status(status: str) -> datetime | None:
    return _utcnow() if status == STATUS_DEAD_LETTER else None
