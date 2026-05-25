from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HardwareAssetIn(BaseModel):
    id: str | None = None
    asset_code: str
    locker_id: str | None = None
    partner_id: str | None = None
    vendor_id: str | None = None
    asset_category: str
    description: str
    acquisition_date: date
    in_service_date: date | None = None
    acquisition_cost_cents: int
    installation_cost_cents: int = 0
    residual_value_cents: int = 0
    useful_life_months: int
    currency: str = "BRL"
    country_code: str | None = None
    supplier_name: str | None = None
    warranty_ends_at: date | None = None
    status: str = "ACTIVE"
    notes: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class HardwareAssetUpdate(BaseModel):
    locker_id: str | None = None
    partner_id: str | None = None
    vendor_id: str | None = None
    asset_category: str | None = None
    description: str | None = None
    in_service_date: date | None = None
    status: str | None = None
    notes: str | None = None
    metadata_json: dict[str, Any] | None = None


class HardwareAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_code: str
    locker_id: str | None
    partner_id: str | None
    vendor_id: str | None
    asset_category: str
    description: str
    acquisition_date: date
    in_service_date: date | None
    acquisition_cost_cents: int
    installation_cost_cents: int
    residual_value_cents: int
    useful_life_months: int
    depreciation_method: str
    currency: str
    country_code: str | None
    supplier_name: str | None
    warranty_ends_at: date | None
    status: str
    notes: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class HardwareAssetListOut(BaseModel):
    items: list[HardwareAssetOut]
    total: int
