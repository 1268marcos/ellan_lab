from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import OrderCreateIn, OrderListOut, OrderOut, OrderUpdateIn
from app.services import order_ops_service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=OrderListOut)
def list_orders(
    status: str | None = Query(default=None),
    partner_id: str | None = Query(default=None),
    order_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> OrderListOut:
    items, total = order_ops_service.list_orders(
        db, status=status, partner_id=partner_id, order_id=order_id, limit=limit, offset=offset
    )
    return OrderListOut(items=items, total=total)


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(body: OrderCreateIn, db: Session = Depends(get_db)) -> OrderOut:
    return order_ops_service.create_order(db, body)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: str, db: Session = Depends(get_db)) -> OrderOut:
    return OrderOut.model_validate(order_ops_service.get_order_or_404(db, order_id))


@router.patch("/{order_id}", response_model=OrderOut)
def update_order(order_id: str, body: OrderUpdateIn, db: Session = Depends(get_db)) -> OrderOut:
    return order_ops_service.update_order(db, order_id, body)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: str, db: Session = Depends(get_db)) -> None:
    order_ops_service.delete_order(db, order_id)
