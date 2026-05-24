from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.money import MoneyCurrencyIn, MoneyCurrencyListOut, MoneyCurrencyOut, MoneyCurrencyUpdate
from app.services import currency_service

router = APIRouter(prefix="/currencies", tags=["currencies"])


@router.get("", response_model=MoneyCurrencyListOut)
def list_items(active_only: bool = Query(False), db: Session = Depends(get_db)) -> MoneyCurrencyListOut:
    items = currency_service.list_currencies(db, active_only=active_only)
    out = [MoneyCurrencyOut.model_validate(i) for i in items]
    return MoneyCurrencyListOut(items=out, total=len(out))


@router.post("", response_model=MoneyCurrencyOut, status_code=status.HTTP_201_CREATED)
def create_item(body: MoneyCurrencyIn, db: Session = Depends(get_db)) -> MoneyCurrencyOut:
    return MoneyCurrencyOut.model_validate(currency_service.create_currency(db, body))


@router.get("/{item_id}", response_model=MoneyCurrencyOut)
def get_item(item_id: int, db: Session = Depends(get_db)) -> MoneyCurrencyOut:
    return MoneyCurrencyOut.model_validate(currency_service.get_currency_or_404(db, item_id))


@router.patch("/{item_id}", response_model=MoneyCurrencyOut)
def update_item(item_id: int, body: MoneyCurrencyUpdate, db: Session = Depends(get_db)) -> MoneyCurrencyOut:
    return MoneyCurrencyOut.model_validate(currency_service.update_currency(db, item_id, body))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)) -> None:
    currency_service.delete_currency(db, item_id)
