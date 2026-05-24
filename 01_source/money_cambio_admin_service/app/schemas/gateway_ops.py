from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DeviceRegistryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_hash: str
    version: str
    first_seen_at_epoch: int
    last_seen_at_epoch: int
    seen_count: int
    region_code: str | None
    locker_id: str | None
    flags_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DeviceRegistryListOut(BaseModel):
    items: list[DeviceRegistryOut]
    total: int


class DeviceRegistryUpdate(BaseModel):
    region_code: str | None = None
    locker_id: str | None = None
    flags_json: dict[str, Any] | None = None


class IdempotencyKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    endpoint: str
    idem_key: str
    status: str
    region_code: str | None
    sales_channel: str | None
    created_at_epoch: int
    expires_at_epoch: int
    created_at: datetime


class IdempotencyKeyListOut(BaseModel):
    items: list[IdempotencyKeyOut]
    total: int


class RiskEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    request_id: str
    event_type: str
    decision: str
    score: int
    policy_id: str
    region_code: str
    locker_id: str
    slot: int
    created_at_epoch: int
    created_at: datetime


class RiskEventListOut(BaseModel):
    items: list[RiskEventOut]
    total: int
