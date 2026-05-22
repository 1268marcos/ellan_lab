from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.marketplace import (
    CommissionCreateIn,
    CommissionListOut,
    CommissionOut,
    CommissionUpdateIn,
)
from app.services import commission_service

router = APIRouter(prefix="/commissions", tags=["commissions"])


@router.get("", response_model=CommissionListOut)
def list_commissions(
    seller_id: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
) -> CommissionListOut:
    rows = commission_service.list_commissions(db, seller_id=seller_id, status_filter=status_filter)
    out = [CommissionOut.model_validate(r) for r in rows]
    return CommissionListOut(commissions=out, total=len(out))


@router.post("", response_model=CommissionOut, status_code=status.HTTP_201_CREATED)
def create_commission(body: CommissionCreateIn, db: Session = Depends(get_db)) -> CommissionOut:
    return CommissionOut.model_validate(commission_service.create_commission(db, body))


@router.patch("/{commission_id}", response_model=CommissionOut)
def update_commission(
    commission_id: str, body: CommissionUpdateIn, db: Session = Depends(get_db)
) -> CommissionOut:
    return CommissionOut.model_validate(commission_service.update_commission(db, commission_id, body))
