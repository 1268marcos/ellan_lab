from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MoneyCurrencyIn(BaseModel):
    code: str = Field(..., min_length=3, max_length=3)
    name: str
    symbol: str | None = None
    minor_units: int = 2
    numeric_code: str | None = None
    region_hint: str | None = None
    metadata_json: dict = Field(default_factory=dict)
    is_active: bool = True


class MoneyCurrencyUpdate(BaseModel):
    name: str | None = None
    symbol: str | None = None
    minor_units: int | None = None
    numeric_code: str | None = None
    region_hint: str | None = None
    metadata_json: dict | None = None
    is_active: bool | None = None


class MoneyCurrencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    symbol: str | None
    minor_units: int
    numeric_code: str | None
    region_hint: str | None
    metadata_json: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MoneyCurrencyListOut(BaseModel):
    items: list[MoneyCurrencyOut]
    total: int
