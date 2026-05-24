from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.payments import (
    PaymentTransactionIn,
    PaymentTransactionListOut,
    PaymentTransactionOut,
    PaymentTransactionUpdate,
)
from app.services import payments_service

router = APIRouter(prefix="/payment-transactions", tags=["payment-transactions"])


@router.get("", response_model=PaymentTransactionListOut)
def list_items(
    order_id: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> PaymentTransactionListOut:
    items = payments_service.list_transactions(db, order_id=order_id, status=status, limit=limit)
    out = [PaymentTransactionOut.model_validate(i) for i in items]
    return PaymentTransactionListOut(items=out, total=len(out))


@router.post("", response_model=PaymentTransactionOut, status_code=status.HTTP_201_CREATED)
def create_item(body: PaymentTransactionIn, db: Session = Depends(get_db)) -> PaymentTransactionOut:
    return PaymentTransactionOut.model_validate(payments_service.create_transaction(db, body))


@router.get("/{tx_id}", response_model=PaymentTransactionOut)
def get_item(tx_id: str, db: Session = Depends(get_db)) -> PaymentTransactionOut:
    return PaymentTransactionOut.model_validate(payments_service.get_transaction_or_404(db, tx_id))


@router.patch("/{tx_id}", response_model=PaymentTransactionOut)
def update_item(
    tx_id: str, body: PaymentTransactionUpdate, db: Session = Depends(get_db)
) -> PaymentTransactionOut:
    return PaymentTransactionOut.model_validate(payments_service.update_transaction(db, tx_id, body))


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(tx_id: str, db: Session = Depends(get_db)) -> None:
    payments_service.delete_transaction(db, tx_id)
