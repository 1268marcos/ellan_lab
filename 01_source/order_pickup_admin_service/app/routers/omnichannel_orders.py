from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import (
    OmnichannelOrderCreateIn,
    OmnichannelOrderListOut,
    OmnichannelOrderOut,
    OmnichannelOrderUpdateIn,
)
from app.services import extended_orders_service

router = APIRouter(prefix="/omnichannel-orders", tags=["omnichannel-orders"])


@router.get("", response_model=OmnichannelOrderListOut)
def list_omnichannel_orders(
    order_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> OmnichannelOrderListOut:
    items, total = extended_orders_service.list_omnichannel(
        db, order_id=order_id, status=status, limit=limit, offset=offset
    )
    return OmnichannelOrderListOut(items=items, total=total)


@router.post("", response_model=OmnichannelOrderOut, status_code=status.HTTP_201_CREATED)
def create_omnichannel_order(body: OmnichannelOrderCreateIn, db: Session = Depends(get_db)) -> OmnichannelOrderOut:
    return extended_orders_service.create_omnichannel(db, body)


@router.patch("/{row_id}", response_model=OmnichannelOrderOut)
def update_omnichannel_order(
    row_id: str, body: OmnichannelOrderUpdateIn, db: Session = Depends(get_db)
) -> OmnichannelOrderOut:
    return extended_orders_service.update_omnichannel(db, row_id, body)


@router.delete("/{row_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_omnichannel_order(row_id: str, db: Session = Depends(get_db)) -> None:
    extended_orders_service.delete_omnichannel(db, row_id)
