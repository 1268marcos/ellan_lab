from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.payments import PaymentIn, PaymentListOut, PaymentOut, PaymentUpdate
from app.services import payments_service

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=PaymentListOut)
def list_items(
    order_id: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> PaymentListOut:
    items = payments_service.list_payments(db, order_id=order_id, limit=limit)
    out = [PaymentOut.model_validate(i) for i in items]
    return PaymentListOut(items=out, total=len(out))


@router.post("", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_item(body: PaymentIn, db: Session = Depends(get_db)) -> PaymentOut:
    return PaymentOut.model_validate(payments_service.create_payment(db, body))


@router.get("/{item_id}", response_model=PaymentOut)
def get_item(item_id: str, db: Session = Depends(get_db)) -> PaymentOut:
    return PaymentOut.model_validate(payments_service.get_payment_or_404(db, item_id))


@router.patch("/{item_id}", response_model=PaymentOut)
def update_item(item_id: str, body: PaymentUpdate, db: Session = Depends(get_db)) -> PaymentOut:
    return PaymentOut.model_validate(payments_service.update_payment(db, item_id, body))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: str, db: Session = Depends(get_db)) -> None:
    payments_service.delete_payment(db, item_id)
