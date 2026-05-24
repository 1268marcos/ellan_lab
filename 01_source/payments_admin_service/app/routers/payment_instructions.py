from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.payments import (
    PaymentInstructionIn,
    PaymentInstructionListOut,
    PaymentInstructionOut,
    PaymentInstructionUpdate,
)
from app.services import payments_service

router = APIRouter(prefix="/payment-instructions", tags=["payment-instructions"])


@router.get("", response_model=PaymentInstructionListOut)
def list_items(
    order_id: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> PaymentInstructionListOut:
    items = payments_service.list_instructions(db, order_id=order_id, limit=limit)
    out = [PaymentInstructionOut.model_validate(i) for i in items]
    return PaymentInstructionListOut(items=out, total=len(out))


@router.post("", response_model=PaymentInstructionOut, status_code=status.HTTP_201_CREATED)
def create_item(body: PaymentInstructionIn, db: Session = Depends(get_db)) -> PaymentInstructionOut:
    return PaymentInstructionOut.model_validate(payments_service.create_instruction(db, body))


@router.get("/{item_id}", response_model=PaymentInstructionOut)
def get_item(item_id: str, db: Session = Depends(get_db)) -> PaymentInstructionOut:
    return PaymentInstructionOut.model_validate(payments_service.get_instruction_or_404(db, item_id))


@router.patch("/{item_id}", response_model=PaymentInstructionOut)
def update_item(
    item_id: str, body: PaymentInstructionUpdate, db: Session = Depends(get_db)
) -> PaymentInstructionOut:
    return PaymentInstructionOut.model_validate(payments_service.update_instruction(db, item_id, body))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: str, db: Session = Depends(get_db)) -> None:
    payments_service.delete_instruction(db, item_id)
