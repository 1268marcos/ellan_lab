from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FxRateIn(BaseModel):
    base_currency: str
    quote_currency: str
    rate_date: date
    rate: Decimal = Field(..., gt=0)
    source: str = "MANUAL"


class FxRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    base_currency: str
    quote_currency: str
    rate_date: date
    rate: Decimal
    source: str
    created_at: datetime


class FxRateListOut(BaseModel):
    items: list[FxRateOut]
    total: int


class FxConvertIn(BaseModel):
    amount_cents: int
    from_currency: str
    to_currency: str
    on_date: date | None = None


class FxConvertOut(BaseModel):
    amount_cents: int
    from_currency: str
    to_currency: str
    to_amount_cents: int
    rate: Decimal | None
    rate_date: date | None
