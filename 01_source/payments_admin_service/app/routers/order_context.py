from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.cross_domain import PaymentContextPlayerLink
from app.schemas.cross_domain import (
    PaymentContextPlayerLinkOut,
    PaymentOrderContextIn,
    PaymentOrderContextListOut,
    PaymentOrderContextOut,
)
from app.services import cross_domain_service

router = APIRouter(prefix="/order-context", tags=["order-context"])


def _context_out(db: Session, ctx) -> PaymentOrderContextOut:
    links = (
        db.query(PaymentContextPlayerLink)
        .filter(PaymentContextPlayerLink.order_context_id == ctx.id)
        .all()
    )
    base = PaymentOrderContextOut.model_validate(ctx)
    base.player_links = [PaymentContextPlayerLinkOut.model_validate(l) for l in links]
    return base


@router.get("", response_model=PaymentOrderContextListOut)
def list_items(
    tenant_id: str | None = Query(None),
    locker_id: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> PaymentOrderContextListOut:
    items = cross_domain_service.list_order_contexts(db, tenant_id=tenant_id, locker_id=locker_id, limit=limit)
    out = [_context_out(db, i) for i in items]
    return PaymentOrderContextListOut(items=out, total=len(out))


@router.get("/by-order/{order_id}", response_model=PaymentOrderContextOut)
def get_by_order(order_id: str, db: Session = Depends(get_db)) -> PaymentOrderContextOut:
    row = cross_domain_service.get_order_context_by_order(db, order_id)
    if not row:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order_context_not_found")
    return _context_out(db, row)


@router.post("", response_model=PaymentOrderContextOut, status_code=status.HTTP_201_CREATED)
def create_item(body: PaymentOrderContextIn, db: Session = Depends(get_db)) -> PaymentOrderContextOut:
    return _context_out(db, cross_domain_service.create_order_context(db, body))
