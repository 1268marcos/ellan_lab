from __future__ import annotations

from pydantic import BaseModel, Field


class ProductCompatibilityCheckIn(BaseModel):
    partner_sku: str
    locker_id: str


class LockerSpecIn(BaseModel):
    slot_size: str = Field(default="M", max_length=8)
    max_weight_g: int = Field(default=5000, ge=0)


class LockerCompatibilityCheckIn(BaseModel):
    locker_spec: LockerSpecIn


class CompatibilityOut(BaseModel):
    compatible: bool
    reason: str | None = None
    recommended_slot_size: str | None = None


class EligibleLockersOut(BaseModel):
    partner_id: str
    product_sku: str | None
    lockers: list[dict[str, str | int]]
