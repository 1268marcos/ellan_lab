from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.payments import GatewayEventIn, GatewayEventListOut, GatewayEventOut
from app.services import payments_service

router = APIRouter(prefix="/gateway-events", tags=["gateway-events"])


@router.get("", response_model=GatewayEventListOut)
def list_items(
    order_id: str | None = Query(None),
    locker_id: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> GatewayEventListOut:
    items = payments_service.list_gateway_events(db, order_id=order_id, locker_id=locker_id, limit=limit)
    out = [GatewayEventOut.model_validate(i) for i in items]
    return GatewayEventListOut(items=out, total=len(out))


@router.post("", response_model=GatewayEventOut, status_code=status.HTTP_201_CREATED)
def create_item(body: GatewayEventIn, db: Session = Depends(get_db)) -> GatewayEventOut:
    return GatewayEventOut.model_validate(payments_service.create_gateway_event(db, body))


@router.get("/{item_id}", response_model=GatewayEventOut)
def get_item(item_id: str, db: Session = Depends(get_db)) -> GatewayEventOut:
    return GatewayEventOut.model_validate(payments_service.get_gateway_event_or_404(db, item_id))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: str, db: Session = Depends(get_db)) -> None:
    payments_service.delete_gateway_event(db, item_id)
