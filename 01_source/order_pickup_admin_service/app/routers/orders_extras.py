from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import (
    DisputeCreateIn,
    DisputeListOut,
    DisputeOut,
    IntegrationHealthListOut,
    IntegrationHealthOut,
    Order360Out,
    SlaWatchListOut,
    TimelineCreateIn,
    TimelineEventOut,
    TimelineListOut,
)
from app.services import orders_extras_service

router = APIRouter(tags=["orders-extras"])


@router.get("/orders/{order_id}/360", response_model=Order360Out)
def order_360(order_id: str, db: Session = Depends(get_db)) -> Order360Out:
    return orders_extras_service.get_order_360(db, order_id)


@router.get("/orders/{order_id}/timeline", response_model=TimelineListOut)
def order_timeline(
    order_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> TimelineListOut:
    items, total = orders_extras_service.list_timeline(db, order_id, limit, offset)
    return TimelineListOut(items=items, total=total)


@router.post("/orders/{order_id}/timeline", response_model=TimelineEventOut, status_code=status.HTTP_201_CREATED)
def add_timeline_note(order_id: str, body: TimelineCreateIn, db: Session = Depends(get_db)) -> TimelineEventOut:
    return orders_extras_service.append_timeline(
        db,
        order_id=order_id,
        event_source=body.event_source,
        event_type=body.event_type,
        title=body.title,
        severity=body.severity,
        detail=body.detail,
    )


@router.get("/sla-watches", response_model=SlaWatchListOut)
def list_sla(
    status: str | None = Query(default=None),
    order_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> SlaWatchListOut:
    items, total = orders_extras_service.list_sla_watches(db, status=status, order_id=order_id, limit=limit, offset=offset)
    return SlaWatchListOut(items=items, total=total)


@router.post("/sla-watches/sync", response_model=dict)
def sync_sla(db: Session = Depends(get_db)) -> dict:
    return orders_extras_service.sync_sla_watches(db)


@router.get("/order-disputes", response_model=DisputeListOut)
def list_disputes(
    order_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> DisputeListOut:
    items, total = orders_extras_service.list_disputes(db, order_id=order_id, status=status, limit=limit, offset=offset)
    return DisputeListOut(items=items, total=total)


@router.post("/order-disputes", response_model=DisputeOut, status_code=status.HTTP_201_CREATED)
def create_dispute(body: DisputeCreateIn, db: Session = Depends(get_db)) -> DisputeOut:
    return orders_extras_service.create_dispute(db, body)


@router.get("/integration-health", response_model=IntegrationHealthListOut)
def list_health(
    channel_code: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> IntegrationHealthListOut:
    items, total = orders_extras_service.list_integration_health(
        db, channel_code=channel_code, limit=limit, offset=offset
    )
    return IntegrationHealthListOut(items=items, total=total)
