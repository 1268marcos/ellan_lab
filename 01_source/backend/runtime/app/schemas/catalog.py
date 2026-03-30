# 01_source/backend/runtime/app/schemas/catalog.py
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class CatalogSkuOut(BaseModel):
    locker_id: str
    sku_id: str
    name: str
    amount_cents: int
    currency: str
    imageURL: str
    is_active: bool
    updated_at: str


class CatalogSlotOut(BaseModel):
    locker_id: str
    slot: int
    sku_id: Optional[str] = None
    name: Optional[str] = None
    amount_cents: Optional[int] = None
    currency: str
    imageURL: str
    is_active: bool
    updated_at: str