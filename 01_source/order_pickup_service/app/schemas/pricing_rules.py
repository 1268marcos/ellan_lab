from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PricingRuleOut(BaseModel):
    id: str
    region: str | None = None
    locker_id: str | None = None
    product_category: str | None = None
    valid_from: datetime
    valid_until: datetime | None = None
    base_amount_cents: int
    discount_pct: float = 0.0
    min_amount_cents: int | None = None
    max_amount_cents: int | None = None
    is_active: bool = True
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class PricingRuleListOut(BaseModel):
    ok: bool = True
    items: list[PricingRuleOut]


class PricingRuleCreateIn(BaseModel):
    region: str | None = Field(default=None, max_length=20)
    locker_id: str | None = Field(default=None, max_length=36)
    product_category: str | None = Field(default=None, max_length=64)
    valid_from: datetime
    valid_until: datetime | None = None
    base_amount_cents: int = Field(..., ge=0)
    discount_pct: float = Field(default=0.0, ge=0, le=100)
    min_amount_cents: int | None = Field(default=None, ge=0)
    max_amount_cents: int | None = Field(default=None, ge=0)
    is_active: bool = True
    metadata_json: dict[str, Any] | None = None


class PricingRulePatchIn(BaseModel):
    region: str | None = Field(default=None, max_length=20)
    locker_id: str | None = Field(default=None, max_length=36)
    product_category: str | None = Field(default=None, max_length=64)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    base_amount_cents: int | None = Field(default=None, ge=0)
    discount_pct: float | None = Field(default=None, ge=0, le=100)
    min_amount_cents: int | None = Field(default=None, ge=0)
    max_amount_cents: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    metadata_json: dict[str, Any] | None = None
