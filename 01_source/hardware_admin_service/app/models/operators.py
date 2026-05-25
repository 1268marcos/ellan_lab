from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LockerOperator(Base):
    __tablename__ = "locker_operators_admin"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    document = Column(String(32), nullable=True)
    email = Column(String(128), nullable=True)
    phone = Column(String(32), nullable=True)
    operator_type = Column(String(32), nullable=False, default="LOGISTICS")
    country = Column(String(2), nullable=False, default="BR")
    active = Column(Boolean, nullable=False, default=True)
    commission_rate = Column(Float, nullable=True)
    currency = Column(String(8), nullable=False, default="BRL")
    contract_ref = Column(String(255), nullable=True)
    sla_pickup_hours = Column(Integer, nullable=False, default=72)
    sla_return_hours = Column(Integer, nullable=False, default=24)
    status = Column(String(30), nullable=False, default="DRAFT")
    legal_name = Column(String(140), nullable=True)
    tier = Column(String(20), nullable=False, default="STANDARD")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
