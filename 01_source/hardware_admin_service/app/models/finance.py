from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import BigInteger, Column, Date, DateTime, Integer, String, Text
from sqlalchemy.types import JSON

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HardwareLockerCapex(Base):
    __tablename__ = "hardware_locker_capex"

    id = Column(String(36), primary_key=True)
    locker_id = Column(String(120), nullable=False, index=True)
    asset_id = Column(String(36), nullable=True, index=True)
    acquisition_cost_cents = Column(BigInteger, nullable=False)
    installation_cost_cents = Column(BigInteger, nullable=False, default=0)
    equipment_cost_cents = Column(BigInteger, nullable=False, default=0)
    connectivity_setup_cents = Column(BigInteger, nullable=False, default=0)
    residual_value_cents = Column(BigInteger, nullable=False, default=0)
    useful_life_months = Column(Integer, nullable=False, default=60)
    depreciation_method = Column(String(20), nullable=False, default="STRAIGHT_LINE")
    depreciation_start_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    supplier = Column(String(255), nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class HardwareLockerOpex(Base):
    __tablename__ = "hardware_locker_opex"

    id = Column(String(36), primary_key=True)
    locker_id = Column(String(120), nullable=False, index=True)
    reference_month = Column(Date, nullable=False, index=True)
    cost_type = Column(String(40), nullable=False)
    amount_cents = Column(BigInteger, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    description = Column(Text, nullable=True)
    invoice_ref = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
