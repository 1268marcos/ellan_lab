from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrderPickupProductCacheDTO(BaseModel):
    """DTO estável (anti-corruption) para cache local de produto."""

    model_config = ConfigDict(extra="ignore")

    sku_id: str
    partner_id: str | None = None
    partner_sku: str | None = None
    name: str
    description: str | None = None
    category_id: str
    amount_cents: int
    currency: str
    width_mm: int | None = None
    height_mm: int | None = None
    depth_mm: int | None = None
    weight_g: int | None = None
    is_active: bool = True
    requires_signature: bool = False
    is_hazardous: bool = False
    temperature_zone: str = "AMBIENT"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    synced_at: datetime | None = None
