# 01_source/backend/order_lifecycle_service/app/routers/internal.py
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.internal_auth import require_internal_token
from app.models.lifecycle import (
    DeadlineStatus,
    DeadlineType,
    DomainEvent,
    EventStatus,
    LifecycleDeadline,
)
from app.schemas.internal import (
    AckEventRequest,
    AckEventResponse,
    CancelDeadlineRequest,
    CancelDeadlineResponse,
    CreateDeadlineRequest,
    CreateDeadlineResponse,
    PendingEventItem,
    PendingEventsResponse,
)
from app.schemas.pickup_events import (
    PickupEventIn,
    PickupEventResponse,
)

router = APIRouter(prefix="/internal", tags=["internal"])


def utc_now():
    return datetime.now(timezone.utc)


@router.post("/deadlines", response_model=CreateDeadlineResponse)
def create_deadline(
    payload: CreateDeadlineRequest,
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    try:
        deadline_type = DeadlineType(payload.deadline_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid deadline_type",
        )

    existing = (
        db.query(LifecycleDeadline)
        .filter(LifecycleDeadline.deadline_key == payload.deadline_key)
        .first()
    )
    if existing:
        return CreateDeadlineResponse(
            id=str(existing.id),
            deadline_key=existing.deadline_key,
            status=existing.status.value,
            order_id=existing.order_id,
            deadline_type=existing.deadline_type.value,
            due_at=existing.due_at,
        )

    now = utc_now()

    deadline = LifecycleDeadline(
        deadline_key=payload.deadline_key,
        order_id=payload.order_id,
        order_channel=payload.order_channel,
        deadline_type=deadline_type,
        status=DeadlineStatus.PENDING,
        due_at=payload.due_at,
        payload=payload.payload,
        created_at=now,
        updated_at=now,
    )
    db.add(deadline)
    db.commit()
    db.refresh(deadline)

    return CreateDeadlineResponse(
        id=str(deadline.id),
        deadline_key=deadline.deadline_key,
        status=deadline.status.value,
        order_id=deadline.order_id,
        deadline_type=deadline.deadline_type.value,
        due_at=deadline.due_at,
    )


@router.post("/deadlines/cancel", response_model=CancelDeadlineResponse)
def cancel_deadline(
    payload: CancelDeadlineRequest,
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    deadline = (
        db.query(LifecycleDeadline)
        .filter(LifecycleDeadline.deadline_key == payload.deadline_key)
        .first()
    )

    if deadline is None:
        return CancelDeadlineResponse(
            deadline_key=payload.deadline_key,
            status="NOT_FOUND",
            cancelled=False,
        )

    if deadline.status in {DeadlineStatus.EXECUTED, DeadlineStatus.CANCELLED}:
        return CancelDeadlineResponse(
            deadline_key=deadline.deadline_key,
            status=deadline.status.value,
            cancelled=False,
        )

    now = utc_now()
    deadline.status = DeadlineStatus.CANCELLED
    deadline.cancelled_at = now
    deadline.updated_at = now
    db.commit()

    return CancelDeadlineResponse(
        deadline_key=deadline.deadline_key,
        status=deadline.status.value,
        cancelled=True,
    )


@router.get("/events/pending", response_model=PendingEventsResponse)
def list_pending_events(
    limit: int = Query(default=100, ge=1, le=500),
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    events = (
        db.query(DomainEvent)
        .filter(DomainEvent.status == EventStatus.PENDING)
        .order_by(DomainEvent.created_at.asc())
        .limit(limit)
        .all()
    )

    return PendingEventsResponse(
        items=[
            PendingEventItem(
                id=str(event.id),
                event_key=event.event_key,
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                event_name=event.event_name,
                event_version=event.event_version,
                status=event.status.value,
                payload=event.payload or {},
                occurred_at=event.occurred_at,
                created_at=event.created_at,
            )
            for event in events
        ]
    )


@router.post("/events/ack", response_model=AckEventResponse)
def ack_event(
    payload: AckEventRequest,
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    event = (
        db.query(DomainEvent)
        .filter(DomainEvent.event_key == payload.event_key)
        .first()
    )

    if event is None:
        return AckEventResponse(
            event_key=payload.event_key,
            status="NOT_FOUND",
            acknowledged=False,
        )

    if event.status == EventStatus.PUBLISHED:
        return AckEventResponse(
            event_key=event.event_key,
            status=event.status.value,
            acknowledged=False,
        )

    now = utc_now()
    event.status = EventStatus.PUBLISHED
    event.published_at = now
    db.commit()

    return AckEventResponse(
        event_key=event.event_key,
        status=event.status.value,
        acknowledged=True,
    )


@router.post(
    "/pickup-events",
    response_model=PickupEventResponse,
)
def ingest_pickup_event(
    payload: PickupEventIn,
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    """
    Ingestão de eventos de pickup no DomainEvent (fonte oficial)
    """

    # idempotência por event_key
    existing = (
        db.query(DomainEvent)
        .filter(DomainEvent.event_key == payload.event_key)
        .first()
    )

    if existing:
        return PickupEventResponse(
            ok=True,
            event_key=existing.event_key,
            stored=False,
        )

    now = utc_now()

    event = DomainEvent(
        event_key=payload.event_key,
        aggregate_type="pickup",
        aggregate_id=payload.pickup_id,
        event_name=payload.event_type,
        event_version=1,
        status=EventStatus.PENDING,
        payload={
            "order_id": payload.order_id,
            "pickup_id": payload.pickup_id,
            "channel": payload.channel,
            "region": payload.region,
            "locker_id": payload.locker_id,
            "machine_id": payload.machine_id,
            "slot": payload.slot,
            "operator_id": payload.operator_id,
            "tenant_id": payload.tenant_id,
            "site_id": payload.site_id,
            "correlation_id": payload.correlation_id,
            "source_service": payload.source_service,
            **(payload.payload or {}),
        },
        occurred_at=payload.occurred_at,
        created_at=now,
    )

    db.add(event)
    db.commit()

    return PickupEventResponse(
        ok=True,
        event_key=event.event_key,
        stored=True,
    )