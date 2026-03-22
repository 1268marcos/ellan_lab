# 01_source/backend/billing_fiscal_service/app/integrations/lifecycle_client.py
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.external_domain_event import DomainEvent


def has_order_paid_event(db: Session, order_id: str) -> bool:
    normalized_order_id = str(order_id).strip()

    stmt = (
        select(DomainEvent)
        .where(DomainEvent.aggregate_type == "order")
        .where(DomainEvent.aggregate_id == normalized_order_id)
        .where(DomainEvent.event_name == "order.paid")
        .order_by(DomainEvent.created_at.desc())
        .limit(1)
    )

    event = db.execute(stmt).scalar_one_or_none()
    return event is not None
