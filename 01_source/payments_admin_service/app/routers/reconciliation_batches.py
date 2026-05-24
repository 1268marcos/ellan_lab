from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.cross_domain import (
    PaymentReconciliationBatchIn,
    PaymentReconciliationBatchListOut,
    PaymentReconciliationBatchOut,
    PaymentReconciliationBatchUpdate,
)
from app.services import cross_domain_service

router = APIRouter(prefix="/reconciliation-batches", tags=["reconciliation-batches"])


class AssignTransactionsIn(BaseModel):
    transaction_ids: list[str]


@router.get("", response_model=PaymentReconciliationBatchListOut)
def list_items(
    status: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> PaymentReconciliationBatchListOut:
    items = cross_domain_service.list_reconciliation_batches(db, status=status, limit=limit)
    out = [PaymentReconciliationBatchOut.model_validate(i) for i in items]
    return PaymentReconciliationBatchListOut(items=out, total=len(out))


@router.post("", response_model=PaymentReconciliationBatchOut, status_code=status.HTTP_201_CREATED)
def create_item(body: PaymentReconciliationBatchIn, db: Session = Depends(get_db)) -> PaymentReconciliationBatchOut:
    return PaymentReconciliationBatchOut.model_validate(
        cross_domain_service.create_reconciliation_batch(db, body)
    )


@router.patch("/{batch_id}", response_model=PaymentReconciliationBatchOut)
def update_item(
    batch_id: str, body: PaymentReconciliationBatchUpdate, db: Session = Depends(get_db)
) -> PaymentReconciliationBatchOut:
    return PaymentReconciliationBatchOut.model_validate(
        cross_domain_service.update_reconciliation_batch(db, batch_id, body)
    )


@router.post("/{batch_code}/assign-transactions")
def assign_transactions(
    batch_code: str, body: AssignTransactionsIn, db: Session = Depends(get_db)
) -> dict[str, int]:
    return cross_domain_service.assign_transactions_to_batch(db, batch_code, body.transaction_ids)
