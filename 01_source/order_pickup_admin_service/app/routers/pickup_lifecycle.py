from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import (
    DomainOutboxListOut,
    DomainOutboxReplayOut,
    OrderItemListOut,
    PickupAttemptListOut,
    PickupEventListOut,
    PickupTokenListOut,
)
from app.services import order_ops_service

router = APIRouter(tags=["pickup-lifecycle"])


@router.get("/order-items", response_model=OrderItemListOut)
def list_order_items(
    order_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> OrderItemListOut:
    items, total = order_ops_service.list_order_items(db, order_id=order_id, limit=limit, offset=offset)
    return OrderItemListOut(items=items, total=total)


@router.get("/pickup-events", response_model=PickupEventListOut)
def list_pickup_events(
    pickup_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PickupEventListOut:
    items, total = order_ops_service.list_pickup_events(db, pickup_id=pickup_id, limit=limit, offset=offset)
    return PickupEventListOut(items=items, total=total)


@router.get("/pickup-tokens", response_model=PickupTokenListOut)
def list_pickup_tokens(
    order_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PickupTokenListOut:
    items, total = order_ops_service.list_pickup_tokens(db, order_id=order_id, limit=limit, offset=offset)
    return PickupTokenListOut(items=items, total=total)


@router.get("/pickup-attempts", response_model=PickupAttemptListOut)
def list_pickup_attempts(
    order_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PickupAttemptListOut:
    items, total = order_ops_service.list_pickup_attempts(db, order_id=order_id, limit=limit, offset=offset)
    return PickupAttemptListOut(items=items, total=total)


@router.get("/domain-event-outbox", response_model=DomainOutboxListOut)
def list_domain_outbox(
    status: str | None = Query(default=None),
    aggregate_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> DomainOutboxListOut:
    items, total = order_ops_service.list_domain_outbox(
        db, status=status, aggregate_id=aggregate_id, limit=limit, offset=offset
    )
    return DomainOutboxListOut(items=items, total=total)


@router.post("/domain-event-outbox/{outbox_id}/replay", response_model=DomainOutboxReplayOut)
def replay_domain_outbox(outbox_id: str, db: Session = Depends(get_db)) -> DomainOutboxReplayOut:
    replayed, item = order_ops_service.replay_domain_outbox(db, outbox_id)
    return DomainOutboxReplayOut(ok=True, replayed=replayed, item=item)
