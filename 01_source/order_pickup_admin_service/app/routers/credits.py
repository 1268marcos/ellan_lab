from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import CreditCreateIn, CreditListOut, CreditOut
from app.services import order_ops_service

router = APIRouter(prefix="/credits", tags=["credits"])


@router.post("", response_model=CreditOut, status_code=status.HTTP_201_CREATED)
def create_credit(body: CreditCreateIn, db: Session = Depends(get_db)) -> CreditOut:
    return order_ops_service.create_credit(db, body)


@router.get("", response_model=CreditListOut)
def list_credits(
    order_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> CreditListOut:
    items, total = order_ops_service.list_credits(db, order_id=order_id, limit=limit, offset=offset)
    return CreditListOut(items=items, total=total)
