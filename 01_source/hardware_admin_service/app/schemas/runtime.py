from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuntimeLockerIn(BaseModel):
    locker_id: str
    machine_id: str
    display_name: str
    region: str
    country: str
    timezone: str
    operator_id: str | None = None
    vendor_id: str | None = None
    temperature_zone: str = "AMBIENT"
    security_level: str = "STANDARD"
    active: bool = True
    runtime_enabled: bool = True
    mqtt_region: str
    mqtt_locker_id: str
    topology_version: int = 1
    slot_count_total: int
    payment_methods_json: list[Any] = Field(default_factory=list)


class RuntimeLockerUpdate(BaseModel):
    display_name: str | None = None
    operator_id: str | None = None
    vendor_id: str | None = None
    temperature_zone: str | None = None
    security_level: str | None = None
    active: bool | None = None
    runtime_enabled: bool | None = None
    slot_count_total: int | None = None
    payment_methods_json: list[Any] | None = None


class RuntimeLockerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    locker_id: str
    machine_id: str
    display_name: str
    region: str
    country: str
    timezone: str
    operator_id: str | None
    vendor_id: str | None
    temperature_zone: str
    security_level: str
    active: bool
    runtime_enabled: bool
    mqtt_region: str
    mqtt_locker_id: str
    topology_version: int
    slot_count_total: int
    payment_methods_json: list[Any]
    created_at: datetime
    updated_at: datetime


class RuntimeLockerListOut(BaseModel):
    items: list[RuntimeLockerOut]
    total: int


class HardwareDeviceRegistryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    device_hash: str
    version: str
    first_seen_at_epoch: int
    last_seen_at_epoch: int
    seen_count: int
    locker_id: str | None
    vendor_id: str | None
    region_code: str | None
    flags_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class HardwareDeviceRegistryListOut(BaseModel):
    items: list[HardwareDeviceRegistryOut]
    total: int


class HardwareSyncQueueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    locker_id: str
    operation: str
    status: str
    payload_json: dict[str, Any] = Field(default_factory=dict)
    retry_count: int
    max_retries: int
    last_error: str | None
    processed_at: datetime | None
    next_retry_at: datetime | None
    created_at: datetime
    updated_at: datetime


class HardwareSyncQueueListOut(BaseModel):
    items: list[HardwareSyncQueueOut]
    total: int


class HardwareTelemetryEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    locker_id: str
    event_type: str
    severity: str
    slot_number: int | None
    payload_json: dict[str, Any]
    created_at_epoch: int
    created_at: datetime


class HardwareTelemetryListOut(BaseModel):
    items: list[HardwareTelemetryEventOut]
    total: int
