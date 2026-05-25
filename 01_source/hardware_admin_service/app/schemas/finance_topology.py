from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HardwareLockerCapexIn(BaseModel):
    locker_id: str
    asset_id: str | None = None
    acquisition_cost_cents: int
    installation_cost_cents: int = 0
    equipment_cost_cents: int = 0
    connectivity_setup_cents: int = 0
    residual_value_cents: int = 0
    useful_life_months: int = 60
    depreciation_method: str = "STRAIGHT_LINE"
    depreciation_start_date: date
    status: str = "ACTIVE"
    supplier: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class HardwareLockerCapexOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    locker_id: str
    asset_id: str | None
    acquisition_cost_cents: int
    installation_cost_cents: int
    equipment_cost_cents: int
    connectivity_setup_cents: int
    residual_value_cents: int
    useful_life_months: int
    depreciation_method: str
    depreciation_start_date: date
    status: str
    supplier: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class HardwareLockerCapexListOut(BaseModel):
    items: list[HardwareLockerCapexOut]
    total: int


class HardwareLockerOpexIn(BaseModel):
    locker_id: str
    reference_month: date
    cost_type: str
    amount_cents: int
    currency: str = "BRL"
    description: str | None = None
    invoice_ref: str | None = None


class HardwareLockerOpexOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    locker_id: str
    reference_month: date
    cost_type: str
    amount_cents: int
    currency: str
    description: str | None
    invoice_ref: str | None
    created_at: datetime
    updated_at: datetime


class HardwareLockerOpexListOut(BaseModel):
    items: list[HardwareLockerOpexOut]
    total: int


class HardwareLockerFeatureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    locker_id: str
    supports_kiosk: bool
    supports_ble: bool
    supports_nfc: bool
    supports_printer: bool
    supports_card_reader: bool
    supports_open_command: bool
    supports_light_command: bool
    supports_refrigerated: bool
    supports_high_value: bool
    created_at: datetime
    updated_at: datetime


class HardwareLockerFeatureListOut(BaseModel):
    items: list[HardwareLockerFeatureOut]
    total: int


class HardwareLockerSlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    locker_id: str
    slot_number: int
    slot_size: str
    width_mm: int | None
    height_mm: int | None
    depth_mm: int | None
    max_weight_g: int | None
    is_active: bool
    created_at: datetime


class HardwareLockerSlotListOut(BaseModel):
    items: list[HardwareLockerSlotOut]
    total: int
