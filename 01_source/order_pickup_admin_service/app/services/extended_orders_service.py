from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.order_ops import FulfillmentOrder, OmnichannelOrder
from app.schemas.order_ops import (
    FulfillmentOrderCreateIn,
    FulfillmentOrderListOut,
    FulfillmentOrderOut,
    FulfillmentOrderUpdateIn,
    OmnichannelOrderCreateIn,
    OmnichannelOrderListOut,
    OmnichannelOrderOut,
    OmnichannelOrderUpdateIn,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_omnichannel(
    db: Session,
    *,
    order_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[OmnichannelOrderOut], int]:
    q = db.query(OmnichannelOrder)
    if order_id:
        q = q.filter(OmnichannelOrder.order_id == order_id)
    if status:
        q = q.filter(OmnichannelOrder.status == status.upper())
    total = q.count()
    rows = q.order_by(OmnichannelOrder.created_at.desc()).offset(offset).limit(limit).all()
    return [OmnichannelOrderOut.model_validate(r) for r in rows], total


def create_omnichannel(db: Session, body: OmnichannelOrderCreateIn) -> OmnichannelOrderOut:
    oid = body.id or new_id()
    if db.get(OmnichannelOrder, oid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="omnichannel_id_exists")
    now = _utcnow()
    row = OmnichannelOrder(
        id=oid,
        order_id=body.order_id,
        store_id=body.store_id,
        pickup_type=body.pickup_type,
        status=body.status,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return OmnichannelOrderOut.model_validate(row)


def update_omnichannel(db: Session, row_id: str, body: OmnichannelOrderUpdateIn) -> OmnichannelOrderOut:
    row = db.get(OmnichannelOrder, row_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="omnichannel_not_found")
    if body.status is not None:
        row.status = body.status
    if body.pickup_type is not None:
        row.pickup_type = body.pickup_type
    if body.ready_at is not None:
        row.ready_at = body.ready_at
    if body.picked_up_at is not None:
        row.picked_up_at = body.picked_up_at
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return OmnichannelOrderOut.model_validate(row)


def delete_omnichannel(db: Session, row_id: str) -> None:
    row = db.get(OmnichannelOrder, row_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="omnichannel_not_found")
    db.delete(row)
    db.commit()


def list_fulfillment_orders(
    db: Session,
    *,
    order_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[FulfillmentOrderOut], int]:
    q = db.query(FulfillmentOrder)
    if order_id:
        q = q.filter(FulfillmentOrder.order_id == order_id)
    if status:
        q = q.filter(FulfillmentOrder.status == status.upper())
    total = q.count()
    rows = q.order_by(FulfillmentOrder.created_at.desc()).offset(offset).limit(limit).all()
    return [FulfillmentOrderOut.model_validate(r) for r in rows], total


def create_fulfillment_order(db: Session, body: FulfillmentOrderCreateIn) -> FulfillmentOrderOut:
    fid = body.id or new_id()
    if db.get(FulfillmentOrder, fid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="fulfillment_order_id_exists")
    now = _utcnow()
    row = FulfillmentOrder(
        id=fid,
        order_id=body.order_id,
        fulfillment_center_id=body.fulfillment_center_id,
        status=body.status,
        priority=body.priority,
        tracking_code=body.tracking_code,
        carrier=body.carrier,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return FulfillmentOrderOut.model_validate(row)


def update_fulfillment_order(db: Session, row_id: str, body: FulfillmentOrderUpdateIn) -> FulfillmentOrderOut:
    row = db.get(FulfillmentOrder, row_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="fulfillment_order_not_found")
    for field in ("status", "priority", "tracking_code", "carrier", "picked_at", "packed_at", "shipped_at", "delivered_to_locker_at"):
        val = getattr(body, field, None)
        if val is not None:
            setattr(row, field, val)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return FulfillmentOrderOut.model_validate(row)


def delete_fulfillment_order(db: Session, row_id: str) -> None:
    row = db.get(FulfillmentOrder, row_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="fulfillment_order_not_found")
    db.delete(row)
    db.commit()
