# 01_source/backend/runtime/app/schemas/runtime_registry.py
from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel


class RuntimeLockerSlotOut(BaseModel):
    slot_number: int
    slot_size: str
    width_cm: Optional[int] = None
    height_cm: Optional[int] = None
    depth_cm: Optional[int] = None
    max_weight_kg: Optional[float] = None
    is_active: bool


class RuntimeLockerContextOut(BaseModel):
    locker_id: str
    machine_id: str
    display_name: str
    region: str
    country: str
    timezone: str
    operator_id: Optional[str] = None
    temperature_zone: str
    security_level: str
    active: bool
    runtime_enabled: bool
    mqtt_region: str
    mqtt_locker_id: str
    topology_version: int
    slot_count_total: int
    slot_ids: List[int]
    slots: List[RuntimeLockerSlotOut]