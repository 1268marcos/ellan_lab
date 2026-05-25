from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HardwareLockerFeature(Base):
    __tablename__ = "hardware_locker_features"

    locker_id = Column(String(120), primary_key=True)
    supports_kiosk = Column(Boolean, nullable=False, default=True)
    supports_ble = Column(Boolean, nullable=False, default=False)
    supports_nfc = Column(Boolean, nullable=False, default=False)
    supports_printer = Column(Boolean, nullable=False, default=False)
    supports_card_reader = Column(Boolean, nullable=False, default=False)
    supports_open_command = Column(Boolean, nullable=False, default=True)
    supports_light_command = Column(Boolean, nullable=False, default=True)
    supports_refrigerated = Column(Boolean, nullable=False, default=False)
    supports_high_value = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class HardwareLockerSlot(Base):
    __tablename__ = "hardware_locker_slots"

    id = Column(String(36), primary_key=True)
    locker_id = Column(String(120), nullable=False, index=True)
    slot_number = Column(Integer, nullable=False)
    slot_size = Column(String(16), nullable=False)
    width_mm = Column(Integer, nullable=True)
    height_mm = Column(Integer, nullable=True)
    depth_mm = Column(Integer, nullable=True)
    max_weight_g = Column(Integer, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
