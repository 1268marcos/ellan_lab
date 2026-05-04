from __future__ import annotations

from pydantic import BaseModel, Field


class EligibleLockerOut(BaseModel):
    id: str
    site_id: str
    slot_size: str
    max_weight_g: int = Field(ge=0)


class EligibleLockersResponse(BaseModel):
    partner_id: str
    product_sku: str | None = None
    lockers: list[EligibleLockerOut]


class CompatibilityCheckIn(BaseModel):
    partner_sku: str
    locker_id: str


class CompatibilityCheckOut(BaseModel):
    compatible: bool
    reason: str | None = None
    recommended_slot_size: str | None = None
