from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import CommissionCreateIn, CommissionListOut, CommissionOut
from app.services import orders_domain_service

router = APIRouter(prefix="/marketplace-commissions", tags=["marketplace-commissions"])


@router.get("", response_model=CommissionListOut)
def list_commissions(
    order_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> CommissionListOut:
    items, total = orders_domain_service.list_commissions(
        db, order_id=order_id, status=status, limit=limit, offset=offset
    )
    return CommissionListOut(items=items, total=total)


@router.post("", response_model=CommissionOut, status_code=status.HTTP_201_CREATED)
def create_commission(body: CommissionCreateIn, db: Session = Depends(get_db)) -> CommissionOut:
    return orders_domain_service.create_commission(db, body)
