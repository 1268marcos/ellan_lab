# 01_source/backend/order_lifecycle_service/app/services/domain_event_service.py
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.lifecycle import DomainEvent, EventStatus
from app.schemas.domain_events import DomainEventPublishIn


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def publish_domain_event(db: Session, payload: DomainEventPublishIn) -> tuple[DomainEvent, bool]:
    existing = (
        db.query(DomainEvent)
        .filter(DomainEvent.event_key == payload.event_key)
        .first()
    )
    if existing:
        return existing, True

    row = DomainEvent(
        event_key=payload.event_key,
        aggregate_type=payload.aggregate_type,
        aggregate_id=payload.aggregate_id,
        event_name=payload.event_name,
        event_version=payload.event_version,
        status=EventStatus.PENDING,
        payload=payload.payload,
        occurred_at=payload.occurred_at,
        published_at=None,
        created_at=_utc_now(),
    )

    db.add(row)
    db.commit()
    db.refresh(row)

    return row, False
