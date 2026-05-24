from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.cross_domain import (
    PartnerPaymentHoldIn,
    PartnerPaymentHoldListOut,
    PartnerPaymentHoldOut,
    PartnerPaymentHoldUpdate,
)
from app.services import cross_domain_service

router = APIRouter(prefix="/partner-holds", tags=["partner-holds"])


@router.get("", response_model=PartnerPaymentHoldListOut)
def list_items(
    partner_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> PartnerPaymentHoldListOut:
    items = cross_domain_service.list_partner_holds(db, partner_id=partner_id, status=status, limit=limit)
    out = [PartnerPaymentHoldOut.model_validate(i) for i in items]
    return PartnerPaymentHoldListOut(items=out, total=len(out))


@router.post("", response_model=PartnerPaymentHoldOut, status_code=status.HTTP_201_CREATED)
def create_item(body: PartnerPaymentHoldIn, db: Session = Depends(get_db)) -> PartnerPaymentHoldOut:
    return PartnerPaymentHoldOut.model_validate(cross_domain_service.create_partner_hold(db, body))


@router.patch("/{hold_id}", response_model=PartnerPaymentHoldOut)
def update_item(
    hold_id: str, body: PartnerPaymentHoldUpdate, db: Session = Depends(get_db)
) -> PartnerPaymentHoldOut:
    return PartnerPaymentHoldOut.model_validate(cross_domain_service.update_partner_hold(db, hold_id, body))
