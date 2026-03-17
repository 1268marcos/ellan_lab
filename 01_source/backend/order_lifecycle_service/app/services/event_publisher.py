# 01_source/backend/order_lifecycle_service/app/services/event_publisher.py
import logging

from sqlalchemy.orm import Session

from app.models.lifecycle import DomainEvent, EventStatus

logger = logging.getLogger(__name__)


def publish_pending_events(db: Session) -> int:
    events = (
        db.query(DomainEvent)
        .filter(DomainEvent.status == EventStatus.PENDING)
        .order_by(DomainEvent.created_at.asc())
        .limit(100)
        .all()
    )

    count = 0
    for event in events:
        logger.info(
            "domain_event_recorded",
            extra={
                "event_name": event.event_name,
                "aggregate_id": event.aggregate_id,
                "event_key": event.event_key,
            },
        )
        event.status = EventStatus.PUBLISHED
        event.published_at = event.occurred_at
        count += 1

    return count