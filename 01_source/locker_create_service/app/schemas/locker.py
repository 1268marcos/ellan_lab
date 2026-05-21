from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SlotConfigIn(BaseModel):
    slot_size: str = Field(..., min_length=1, max_length=8)
    slot_count: int = Field(..., ge=0)
    available_count: Optional[int] = None
    width_mm: Optional[int] = None
    height_mm: Optional[int] = None
    depth_mm: Optional[int] = None
    max_weight_g: Optional[int] = None


class ProductConfigIn(BaseModel):
    category: str
    allowed: bool = True
    temperature_zone: str = "ANY"


class LockerAddressIn(BaseModel):
    line: Optional[str] = None
    number: Optional[str] = None
    extra: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "BR"
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LockerCreateIn(BaseModel):
    id: str = Field(..., min_length=5, max_length=64)
    display_name: str = Field(..., min_length=3, max_length=255)
    region: str = Field(..., min_length=2, max_length=10)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=100)
    country: str = "BR"
    timezone: str = "America/Sao_Paulo"
    operator_id: Optional[str] = None
    external_id: Optional[str] = None
    description: Optional[str] = None
    site_id: Optional[str] = None
    district: Optional[str] = None
    address: Optional[LockerAddressIn] = None
    active: bool = True
    temperature_zone: str = "AMBIENT"
    security_level: str = "STANDARD"
    has_camera: bool = False
    has_alarm: bool = False
    has_kiosk: bool = False
    has_printer: bool = False
    has_card_reader: bool = False
    has_nfc: bool = False
    slot_configs: Optional[List[SlotConfigIn]] = None
    product_configs: Optional[List[ProductConfigIn]] = None
    copy_product_configs_from: Optional[str] = Field(
        default=None,
        description="Copia product_locker_configs de outro locker (ex: SP-OSASCO-CENTRO-LK-001)",
    )


class LockerBulkCreateIn(BaseModel):
    lockers: List[LockerCreateIn] = Field(..., min_length=1, max_length=50)


class LockerUpdateIn(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    temperature_zone: Optional[str] = None
    security_level: Optional[str] = None
    has_camera: Optional[bool] = None
    has_alarm: Optional[bool] = None
    has_kiosk: Optional[bool] = None
    has_printer: Optional[bool] = None
    has_card_reader: Optional[bool] = None
    has_nfc: Optional[bool] = None
    operator_id: Optional[str] = None
    slots_available: Optional[int] = None


class SlotConfigOut(BaseModel):
    slot_size: str
    slot_count: int
    available_count: int
    width_mm: Optional[int] = None
    height_mm: Optional[int] = None
    depth_mm: Optional[int] = None
    max_weight_g: Optional[int] = None


class ProductConfigOut(BaseModel):
    category: str
    allowed: bool
    temperature_zone: str


class LockerOut(BaseModel):
    id: str
    display_name: str
    region: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: str
    timezone: str
    active: bool
    slots_count: int
    slots_available: int
    temperature_zone: str
    security_level: str
    operator_id: Optional[str] = None
    has_camera: bool
    has_alarm: bool
    has_kiosk: bool
    has_printer: bool
    has_card_reader: bool
    has_nfc: bool
    slot_configs: List[SlotConfigOut] = []
    product_configs: List[ProductConfigOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LockerListOut(BaseModel):
    lockers: List[LockerOut]
    total: int


class LockerBulkCreateOut(BaseModel):
    created: List[LockerOut]
    failed: List[dict]
