from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import FulfillmentListOut, FulfillmentOut, FulfillmentUpdateIn
from app.services import order_ops_service

router = APIRouter(prefix="/fulfillment-tracking", tags=["fulfillment-tracking"])


@router.get("", response_model=FulfillmentListOut)
def list_fulfillment(
    status: str | None = Query(default=None),
    partner_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> FulfillmentListOut:
    items, total = order_ops_service.list_fulfillment(
        db, status=status, partner_id=partner_id, limit=limit, offset=offset
    )
    return FulfillmentListOut(items=items, total=total)


@router.patch("/{tracking_id}", response_model=FulfillmentOut)
def update_fulfillment(
    tracking_id: str, body: FulfillmentUpdateIn, db: Session = Depends(get_db)
) -> FulfillmentOut:
    return order_ops_service.update_fulfillment(db, tracking_id, body)
