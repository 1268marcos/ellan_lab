from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import (
    FulfillmentOrderCreateIn,
    FulfillmentOrderListOut,
    FulfillmentOrderOut,
    FulfillmentOrderUpdateIn,
)
from app.services import extended_orders_service

router = APIRouter(prefix="/fulfillment-orders", tags=["fulfillment-orders"])


@router.get("", response_model=FulfillmentOrderListOut)
def list_fulfillment_orders(
    order_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> FulfillmentOrderListOut:
    items, total = extended_orders_service.list_fulfillment_orders(
        db, order_id=order_id, status=status, limit=limit, offset=offset
    )
    return FulfillmentOrderListOut(items=items, total=total)


@router.post("", response_model=FulfillmentOrderOut, status_code=status.HTTP_201_CREATED)
def create_fulfillment_order(body: FulfillmentOrderCreateIn, db: Session = Depends(get_db)) -> FulfillmentOrderOut:
    return extended_orders_service.create_fulfillment_order(db, body)


@router.patch("/{row_id}", response_model=FulfillmentOrderOut)
def update_fulfillment_order(
    row_id: str, body: FulfillmentOrderUpdateIn, db: Session = Depends(get_db)
) -> FulfillmentOrderOut:
    return extended_orders_service.update_fulfillment_order(db, row_id, body)


@router.delete("/{row_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fulfillment_order(row_id: str, db: Session = Depends(get_db)) -> None:
    extended_orders_service.delete_fulfillment_order(db, row_id)
