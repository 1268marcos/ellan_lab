from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.types import JSON

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RuntimeLocker(Base):
    __tablename__ = "runtime_lockers_admin"

    locker_id = Column(String(120), primary_key=True)
    machine_id = Column(String(120), nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    region = Column(String(16), nullable=False)
    country = Column(String(8), nullable=False)
    timezone = Column(String(64), nullable=False)
    operator_id = Column(String(120), nullable=True, index=True)
    vendor_id = Column(String(36), nullable=True, index=True)
    temperature_zone = Column(String(32), nullable=False, default="AMBIENT")
    security_level = Column(String(32), nullable=False, default="STANDARD")
    active = Column(Boolean, nullable=False, default=True)
    runtime_enabled = Column(Boolean, nullable=False, default=True)
    mqtt_region = Column(String(32), nullable=False)
    mqtt_locker_id = Column(String(120), nullable=False)
    topology_version = Column(Integer, nullable=False, default=1)
    slot_count_total = Column(Integer, nullable=False)
    payment_methods_json = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class HardwareDeviceRegistry(Base):
    __tablename__ = "hardware_device_registry"

    device_hash = Column(String(128), primary_key=True)
    version = Column(String(32), nullable=False)
    first_seen_at_epoch = Column(BigInteger, nullable=False)
    last_seen_at_epoch = Column(BigInteger, nullable=False)
    seen_count = Column(Integer, nullable=False, default=1)
    locker_id = Column(String(120), nullable=True, index=True)
    vendor_id = Column(String(36), nullable=True, index=True)
    region_code = Column(String(20), nullable=True)
    flags_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
