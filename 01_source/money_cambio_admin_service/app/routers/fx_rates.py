from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.cambio import FxConvertIn, FxConvertOut, FxRateIn, FxRateListOut, FxRateOut
from app.services import fx_service

router = APIRouter(prefix="/fx-rates", tags=["fx-rates"])


@router.get("", response_model=FxRateListOut)
def list_rates(
    base_currency: str | None = None,
    quote_currency: str | None = None,
    db: Session = Depends(get_db),
) -> FxRateListOut:
    rows = fx_service.list_fx_rates(db, base_currency, quote_currency)
    items = [FxRateOut.model_validate(r) for r in rows]
    return FxRateListOut(items=items, total=len(items))


@router.post("", response_model=FxRateOut, status_code=201)
def upsert_rate(body: FxRateIn, db: Session = Depends(get_db)) -> FxRateOut:
    return FxRateOut.model_validate(fx_service.upsert_fx_rate(db, body))


@router.post("/convert", response_model=FxConvertOut)
def convert(body: FxConvertIn, db: Session = Depends(get_db)) -> FxConvertOut:
    result = fx_service.convert_cents(db, body.amount_cents, body.from_currency, body.to_currency, body.on_date)
    return FxConvertOut(**result)
