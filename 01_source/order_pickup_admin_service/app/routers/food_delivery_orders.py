from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import (
    FoodDeliveryOrderCreateIn,
    FoodDeliveryOrderListOut,
    FoodDeliveryOrderOut,
    FoodDeliveryOrderUpdateIn,
)
from app.services import orders_domain_service

router = APIRouter(prefix="/food-delivery-orders", tags=["food-delivery"])


@router.get("", response_model=FoodDeliveryOrderListOut)
def list_food_delivery_orders(
    order_id: str | None = Query(default=None),
    platform_code: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> FoodDeliveryOrderListOut:
    items, total = orders_domain_service.list_food_delivery(
        db, order_id=order_id, platform_code=platform_code, limit=limit, offset=offset
    )
    return FoodDeliveryOrderListOut(items=items, total=total)


@router.post("", response_model=FoodDeliveryOrderOut, status_code=status.HTTP_201_CREATED)
def create_food_delivery_order(body: FoodDeliveryOrderCreateIn, db: Session = Depends(get_db)) -> FoodDeliveryOrderOut:
    return orders_domain_service.create_food_delivery(db, body)


@router.patch("/{row_id}", response_model=FoodDeliveryOrderOut)
def update_food_delivery_order(
    row_id: str, body: FoodDeliveryOrderUpdateIn, db: Session = Depends(get_db)
) -> FoodDeliveryOrderOut:
    return orders_domain_service.update_food_delivery(db, row_id, body)
