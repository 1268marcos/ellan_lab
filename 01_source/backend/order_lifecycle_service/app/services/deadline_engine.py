from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.lifecycle import (
    AnalyticsFact,
    DeadlineStatus,
    DomainEvent,
    EventStatus,
    LifecycleDeadline,
)


def utc_now():
    return datetime.now(timezone.utc)


def execute_prepayment_timeout(db: Session, deadline: LifecycleDeadline) -> None:
    now = utc_now()

    if deadline.status not in {DeadlineStatus.PENDING, DeadlineStatus.EXECUTING}:
        return

    deadline.status = DeadlineStatus.EXECUTED
    deadline.executed_at = now
    deadline.updated_at = now

    order_id = deadline.order_id
    order_channel = deadline.order_channel
    payload = deadline.payload or {}

    event = DomainEvent(
        event_key=f"order.prepayment_timed_out:{order_id}",
        aggregate_type="order",
        aggregate_id=order_id,
        event_name="order.prepayment_timed_out",
        event_version=1,
        status=EventStatus.PENDING,
        payload={
            "order_id": order_id,
            "order_channel": order_channel,
            "deadline_type": deadline.deadline_type.value,
            "due_at": deadline.due_at.isoformat(),
            "reason": "payment_not_confirmed_before_deadline",
            **payload,
        },
        occurred_at=now,
        created_at=now,
    )
    db.add(event)

    fact = AnalyticsFact(
        fact_key=f"order_abandoned_before_payment:{order_id}",
        fact_name="order_abandoned_before_payment",
        order_id=order_id,
        order_channel=order_channel,
        region_code=payload.get("region_code"),
        slot_id=payload.get("slot_id"),
        payload={
            "order_id": order_id,
            "abandonment_stage": "prepayment",
            "reason": "payment_not_confirmed_before_deadline",
            "deadline_type": deadline.deadline_type.value,
            "due_at": deadline.due_at.isoformat(),
            **payload,
        },
        occurred_at=now,
        created_at=now,
    )
    db.add(fact)