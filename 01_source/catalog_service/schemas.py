from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DimensionsIn(BaseModel):
    width_mm: int = Field(ge=0)
    height_mm: int = Field(ge=0)
    depth_mm: int = Field(ge=0)
    weight_g: int = Field(ge=0)


class CompatibilityRulesIn(BaseModel):
    requires_signature: bool = False
    is_fragile: bool = False
    temperature_zone: str = Field(default="AMBIENT", max_length=32)
    is_hazardous: bool = False


class EligibleLockerSeedIn(BaseModel):
    locker_id: str = Field(min_length=1, max_length=36)
    locker_label: str | None = Field(default=None, max_length=255)
    recommended_slot_size: str | None = Field(default=None, max_length=32)
    slot_width_mm: int | None = Field(default=None, ge=0)
    slot_height_mm: int | None = Field(default=None, ge=0)
    slot_depth_mm: int | None = Field(default=None, ge=0)
    max_weight_g: int | None = Field(default=None, ge=0)
    temperature_zone: str | None = Field(default=None, max_length=32)
    signature_available: bool = True
    hazardous_allowed: bool = False


class PartnerProductCreateIn(BaseModel):
    partner_sku: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category_id: str = Field(min_length=1, max_length=64)
    dimensions: DimensionsIn
    price_cents: int = Field(ge=0)
    currency: str = Field(default="BRL", max_length=8)
    images: list[str] = Field(default_factory=list)
    compatibility_rules: CompatibilityRulesIn = Field(default_factory=CompatibilityRulesIn)
    eligible_lockers: list[EligibleLockerSeedIn] | None = None
    mark_deprecated: bool = False


class PartnerProductCreateOut(BaseModel):
    sku_id: str
    partner_id: str
    partner_sku: str


class LockerCheckIn(BaseModel):
    locker_id: str
    slot_width_mm: int = Field(ge=1)
    slot_height_mm: int = Field(ge=1)
    slot_depth_mm: int = Field(ge=1)
    max_weight_g: int = Field(ge=1)
    temperature_zone: str = Field(default="AMBIENT", max_length=32)
    signature_available: bool = True
    hazardous_allowed: bool = False


class CompatibilityCheckOut(BaseModel):
    compatible: bool
    reason: str | None
    recommended_slot_size: str | None


class EligibleLockerOut(BaseModel):
    locker_id: str
    locker_label: str | None
    recommended_slot_size: str | None
    sku_id: str | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None


class OrderPickupProductCacheDTO(BaseModel):
    """DTO consumido pelo order_pickup_service (anti-corruption layer)."""

    sku_id: str
    partner_id: str | None
    partner_sku: str | None
    name: str
    description: str | None
    category_id: str
    amount_cents: int
    currency: str
    width_mm: int | None
    height_mm: int | None
    depth_mm: int | None
    weight_g: int | None
    is_active: bool
    requires_signature: bool
    is_hazardous: bool
    temperature_zone: str
    created_at: datetime
    updated_at: datetime
    synced_at: datetime | None = None


class ProductDetailOut(BaseModel):
    sku_id: str
    partner_id: str
    partner_sku: str
    name: str
    description: str | None
    category_id: str
    amount_cents: int
    currency: str
    images: list[str]
    is_active: bool
    is_deprecated: bool
    requires_signature: bool
    is_fragile: bool
    is_hazardous: bool
    temperature_zone: str
    dimensions: DimensionsIn | None
    order_pickup_cache: OrderPickupProductCacheDTO
    created_at: datetime
    updated_at: datetime

    @field_validator("images", mode="before")
    @classmethod
    def parse_images(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            try:
                data = json.loads(v)
            except json.JSONDecodeError:
                return []
            return data if isinstance(data, list) else []
        if v is None:
            return []
        return list(v)
