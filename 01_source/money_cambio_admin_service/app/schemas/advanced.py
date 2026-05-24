from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentRailIn(BaseModel):
    player_code: str
    country_code: str
    payment_method_code: str | None = None
    wallet_provider_code: str | None = None
    channel: str = "LOCKER"
    is_enabled: bool = True
    max_amount_cents: int | None = None
    notes: str | None = None


class PaymentRailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    player_code: str
    country_code: str
    payment_method_code: str | None
    wallet_provider_code: str | None
    channel: str
    is_enabled: bool
    max_amount_cents: int | None
    notes: str | None
    created_at: datetime


class PaymentRailListOut(BaseModel):
    items: list[PaymentRailOut]
    total: int


class PricingPreviewIn(BaseModel):
    amount_cents: int = Field(gt=0)
    player_code: str
    country_code: str | None = None
    corridor_code: str | None = None
    payment_method_code: str | None = None
    on_date: date | None = None


class PricingLineOut(BaseModel):
    label: str
    amount_cents: int | None = None
    currency: str | None = None
    bps: int | None = None
    detail: str | None = None


class PricingPreviewOut(BaseModel):
    player_code: str
    corridor_code: str | None
    transaction_currency: str
    settlement_currency: str
    amount_cents: int
    fx_rate: Decimal | None
    fx_rate_date: date | None
    spread_bps: int
    markup_bps: int
    settlement_cents: int
    settlement_days: int | None
    cut_off_time_utc: str | None
    compliance_status: str
    compliance_notes: list[str] = Field(default_factory=list)
    rail_allowed: bool
    lines: list[PricingLineOut]
    warnings: list[str] = Field(default_factory=list)


class FxLockIn(BaseModel):
    player_code: str | None = None
    corridor_code: str
    amount_cents_ref: int | None = None
    ttl_hours: int = Field(default=24, ge=1, le=168)


class FxLockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    lock_reference: str
    player_code: str | None
    corridor_code: str
    base_currency: str
    quote_currency: str
    locked_rate: Decimal
    spread_bps: int
    amount_cents_ref: int | None
    status: str
    locked_at: datetime
    expires_at: datetime


class FxLockListOut(BaseModel):
    items: list[FxLockOut]
    total: int


class TreasuryExposureRow(BaseModel):
    currency_code: str
    player_count: int
    corridor_count: int
    has_fx_rate: bool
    active_locks: int
    risk_hint: str


class TreasuryDashboardOut(BaseModel):
    currencies_tracked: int
    players_active: int
    corridors_active: int
    fx_pairs_configured: int
    active_fx_locks: int
    exposures: list[TreasuryExposureRow]
    gaps: list[str]
