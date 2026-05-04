from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DimensionsIn(BaseModel):
    width_mm: int | None = None
    height_mm: int | None = None
    depth_mm: int | None = None
    weight_g: int | None = None


class CompatibilityRulesIn(BaseModel):
    requires_signature: bool = False
    is_fragile: bool = False
    temperature_zone: str = Field(default="AMBIENT", max_length=32)


class ProductCreateIn(BaseModel):
    partner_sku: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category_id: str = Field(..., min_length=1, max_length=64)
    dimensions: DimensionsIn = Field(default_factory=DimensionsIn)
    price_cents: int = Field(..., ge=0)
    currency: str = Field(default="BRL", max_length=8)
    images: list[str] = Field(default_factory=list)
    compatibility_rules: CompatibilityRulesIn = Field(default_factory=CompatibilityRulesIn)


class ProductCreateResponse(BaseModel):
    sku_id: str
    partner_id: str
    partner_sku: str
    version: int


class OrderPickupProductCacheDTO(BaseModel):
    """ACL DTO consumido pelo order_pickup_service (seção 4.4)."""

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
    created_at: datetime | None = None
    updated_at: datetime | None = None
    synced_at: datetime | None = None


class ProductDetailOut(BaseModel):
    sku_id: str
    partner_id: str
    partner_sku: str
    name: str
    description: str | None
    category_id: str
    price_cents: int
    currency: str
    images: list[str]
    requires_signature: bool
    is_hazardous: bool
    temperature_zone: str
    version: int
    is_active: bool
    order_pickup_cache: OrderPickupProductCacheDTO


class ProductVersionOut(BaseModel):
    version: int
    snapshot: dict[str, Any]
    created_at: datetime


class BulkProductItem(BaseModel):
    partner_sku: str
    name: str
    category_id: str
    dimensions: DimensionsIn = Field(default_factory=DimensionsIn)
    price_cents: int = Field(..., ge=0)
    currency: str = "BRL"
    images: list[str] = Field(default_factory=list)
    compatibility_rules: CompatibilityRulesIn = Field(default_factory=CompatibilityRulesIn)


class BulkProductIn(BaseModel):
    partner_id: str = Field(..., min_length=8)
    items: list[BulkProductItem] = Field(..., max_length=100)


class BulkProductResponse(BaseModel):
    created: list[ProductCreateResponse]
    errors: list[dict[str, Any]] = Field(default_factory=list)
