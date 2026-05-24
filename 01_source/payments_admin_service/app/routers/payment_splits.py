from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.payments import PaymentSplitIn, PaymentSplitListOut, PaymentSplitOut, PaymentSplitUpdate
from app.services import payments_service

router = APIRouter(prefix="/payment-splits", tags=["payment-splits"])


@router.get("", response_model=PaymentSplitListOut)
def list_items(
    order_id: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> PaymentSplitListOut:
    items = payments_service.list_splits(db, order_id=order_id, limit=limit)
    out = [PaymentSplitOut.model_validate(i) for i in items]
    return PaymentSplitListOut(items=out, total=len(out))


@router.post("", response_model=PaymentSplitOut, status_code=status.HTTP_201_CREATED)
def create_item(body: PaymentSplitIn, db: Session = Depends(get_db)) -> PaymentSplitOut:
    return PaymentSplitOut.model_validate(payments_service.create_split(db, body))


@router.get("/{item_id}", response_model=PaymentSplitOut)
def get_item(item_id: str, db: Session = Depends(get_db)) -> PaymentSplitOut:
    return PaymentSplitOut.model_validate(payments_service.get_split_or_404(db, item_id))


@router.patch("/{item_id}", response_model=PaymentSplitOut)
def update_item(item_id: str, body: PaymentSplitUpdate, db: Session = Depends(get_db)) -> PaymentSplitOut:
    return PaymentSplitOut.model_validate(payments_service.update_split(db, item_id, body))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: str, db: Session = Depends(get_db)) -> None:
    payments_service.delete_split(db, item_id)
