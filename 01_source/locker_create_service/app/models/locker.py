from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Locker(Base):
    __tablename__ = "lockers"

    id = Column(String(64), primary_key=True)
    external_id = Column(String(100), nullable=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    region = Column(String(10), nullable=False, index=True)
    site_id = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=False, default="America/Sao_Paulo")
    address_line = Column(String(255), nullable=True)
    address_number = Column(String(50), nullable=True)
    address_extra = Column(String(255), nullable=True)
    district = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(50), nullable=True)
    country = Column(String(100), nullable=False, default="BR")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    slots_count = Column(Integer, nullable=False, default=0)
    slots_available = Column(Integer, nullable=False, default=0)
    temperature_zone = Column(String(50), nullable=False, default="AMBIENT")
    security_level = Column(String(50), nullable=False, default="STANDARD")
    has_camera = Column(Boolean, nullable=False, default=False)
    has_alarm = Column(Boolean, nullable=False, default=False)
    has_kiosk = Column(Boolean, nullable=False, default=False)
    has_printer = Column(Boolean, nullable=False, default=False)
    has_card_reader = Column(Boolean, nullable=False, default=False)
    has_nfc = Column(Boolean, nullable=False, default=False)
    operator_id = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    slot_configs = relationship("LockerSlotConfig", back_populates="locker", cascade="all, delete-orphan")
    product_configs = relationship("ProductLockerConfig", back_populates="locker", cascade="all, delete-orphan")
    webhook = relationship("LockerWebhookConfig", back_populates="locker", uselist=False, cascade="all, delete-orphan")
    api_keys = relationship("LockerApiKey", back_populates="locker", cascade="all, delete-orphan")


class LockerSlotConfig(Base):
    __tablename__ = "locker_slot_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    locker_id = Column(String(64), ForeignKey("lockers.id"), nullable=False, index=True)
    slot_size = Column(String(8), nullable=False)
    slot_count = Column(Integer, nullable=False, default=0)
    available_count = Column(Integer, nullable=True)
    width_mm = Column(Integer, nullable=True)
    height_mm = Column(Integer, nullable=True)
    depth_mm = Column(Integer, nullable=True)
    max_weight_g = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    locker = relationship("Locker", back_populates="slot_configs")


class ProductLockerConfig(Base):
    __tablename__ = "product_locker_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    locker_id = Column(String(64), ForeignKey("lockers.id"), nullable=False, index=True)
    category = Column(String(64), nullable=False, index=True)
    allowed = Column(Boolean, nullable=False, default=True)
    temperature_zone = Column(String(32), nullable=False, default="ANY")
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    locker = relationship("Locker", back_populates="product_configs")
