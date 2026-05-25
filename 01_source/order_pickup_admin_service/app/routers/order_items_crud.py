from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import OrderItemCreateIn, OrderItemListOut, OrderItemOut, OrderItemUpdateIn
from app.services import order_ops_service, orders_domain_service

router = APIRouter(prefix="/order-items", tags=["order-items"])


@router.get("", response_model=OrderItemListOut)
def list_order_items(
    order_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> OrderItemListOut:
    items, total = order_ops_service.list_order_items(db, order_id=order_id, limit=limit, offset=offset)
    return OrderItemListOut(items=items, total=total)


@router.post("", response_model=OrderItemOut, status_code=status.HTTP_201_CREATED)
def create_order_item(body: OrderItemCreateIn, db: Session = Depends(get_db)) -> OrderItemOut:
    return orders_domain_service.create_order_item(db, body)


@router.patch("/{item_id}", response_model=OrderItemOut)
def update_order_item(item_id: str, body: OrderItemUpdateIn, db: Session = Depends(get_db)) -> OrderItemOut:
    return orders_domain_service.update_order_item(db, item_id, body)
