from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.types import JsonType


class CapabilityCountry(Base):
    __tablename__ = "capability_country"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(2), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    continent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    default_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    default_timezone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address_format: Mapped[str | None] = mapped_column(String(20), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=True, default=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CapabilityProvince(Base):
    __tablename__ = "capability_province"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    country_code: Mapped[str | None] = mapped_column(String(2), ForeignKey("capability_country.code", ondelete="CASCADE"), nullable=True)
    province_code_original: Mapped[str | None] = mapped_column(String(2), nullable=True)
    region: Mapped[str | None] = mapped_column(String(50), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=True, default=True)
    metadata_json: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CapabilityLockerLocation(Base):
    __tablename__ = "capability_locker_location"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    province_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    city_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(11, 8), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address_street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address_complement: Mapped[str | None] = mapped_column(String(100), nullable=True)
    operating_hours_json: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=True, default=True)
    metadata_json: Mapped[dict | None] = mapped_column(JsonType, nullable=True)
    has_ble: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
