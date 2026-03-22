# 01_source/backend/billing_fiscal_service/app/integrations/lifecycle_client.py
from __future__ import annotations

import logging

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.external_domain_event import DomainEvent

logger = logging.getLogger("billing_fiscal_service.lifecycle_client")

INVOICE_TRIGGER_EVENT_NAMES = {
    "pickup.ready_for_pickup",
}


def has_invoice_trigger_event(db: Session, order_id: str) -> bool:
    normalized_order_id = str(order_id).strip()

    stmt = (
        select(DomainEvent)
        .where(
            or_(
                DomainEvent.aggregate_id == normalized_order_id,
                DomainEvent.payload["order_id"].astext == normalized_order_id,
            )
        )
        .where(DomainEvent.event_name.in_(INVOICE_TRIGGER_EVENT_NAMES))
        .order_by(DomainEvent.created_at.desc())
        .limit(1)
    )

    event = db.execute(stmt).scalar_one_or_none()

    if event:
        logger.info(
            "invoice_trigger_event_found",
            extra={
                "order_id": normalized_order_id,
                "event_name": event.event_name,
                "aggregate_id": event.aggregate_id,
                "aggregate_type": event.aggregate_type,
            },
        )
        return True

    related_stmt = (
        select(
            DomainEvent.event_name,
            DomainEvent.aggregate_type,
            DomainEvent.aggregate_id,
            DomainEvent.payload,
            DomainEvent.created_at,
        )
        .where(
            or_(
                DomainEvent.aggregate_id == normalized_order_id,
                DomainEvent.payload["order_id"].astext == normalized_order_id,
            )
        )
        .order_by(DomainEvent.created_at.desc())
        .limit(20)
    )

    related = db.execute(related_stmt).all()

    logger.warning(
        "invoice_trigger_event_not_found",
        extra={
            "order_id": normalized_order_id,
            "related_events": [
                {
                    "event_name": row.event_name,
                    "aggregate_type": row.aggregate_type,
                    "aggregate_id": row.aggregate_id,
                    "payload": row.payload,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in related
            ],
        },
    )

    return False