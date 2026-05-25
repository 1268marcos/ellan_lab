from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, Date, DateTime, Integer, String, Text
from sqlalchemy.types import JSON

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HardwareAsset(Base):
    __tablename__ = "hardware_assets"

    id = Column(String(36), primary_key=True)
    asset_code = Column(String(64), nullable=False, unique=True, index=True)
    locker_id = Column(String(36), nullable=True, index=True)
    partner_id = Column(String(36), nullable=True, index=True)
    vendor_id = Column(String(36), nullable=True, index=True)
    asset_category = Column(String(40), nullable=False)
    description = Column(String(255), nullable=False)
    acquisition_date = Column(Date, nullable=False)
    in_service_date = Column(Date, nullable=True)
    acquisition_cost_cents = Column(BigInteger, nullable=False)
    installation_cost_cents = Column(BigInteger, nullable=False, default=0)
    residual_value_cents = Column(BigInteger, nullable=False, default=0)
    useful_life_months = Column(Integer, nullable=False)
    depreciation_method = Column(String(20), nullable=False, default="STRAIGHT_LINE")
    currency = Column(String(8), nullable=False, default="BRL")
    country_code = Column(String(2), nullable=True)
    jurisdiction_code = Column(String(32), nullable=True)
    supplier_name = Column(String(140), nullable=True)
    warranty_ends_at = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    notes = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
