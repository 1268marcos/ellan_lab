from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import PickupCreateIn, PickupListOut, PickupOut, PickupUpdateIn
from app.services import order_ops_service

router = APIRouter(prefix="/pickups", tags=["pickups"])


@router.get("", response_model=PickupListOut)
def list_pickups(
    order_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> PickupListOut:
    items, total = order_ops_service.list_pickups(db, order_id=order_id, status=status, limit=limit, offset=offset)
    return PickupListOut(items=items, total=total)


@router.post("", response_model=PickupOut, status_code=status.HTTP_201_CREATED)
def create_pickup(body: PickupCreateIn, db: Session = Depends(get_db)) -> PickupOut:
    return order_ops_service.create_pickup(db, body)


@router.get("/{pickup_id}", response_model=PickupOut)
def get_pickup(pickup_id: str, db: Session = Depends(get_db)) -> PickupOut:
    return PickupOut.model_validate(order_ops_service.get_pickup_or_404(db, pickup_id))


@router.patch("/{pickup_id}", response_model=PickupOut)
def update_pickup(pickup_id: str, body: PickupUpdateIn, db: Session = Depends(get_db)) -> PickupOut:
    return order_ops_service.update_pickup(db, pickup_id, body)
