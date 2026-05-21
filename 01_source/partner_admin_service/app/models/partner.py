from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EcommercePartner(Base):
    __tablename__ = "ecommerce_partners"

    id = Column(String(36), primary_key=True)
    name = Column(String(128), nullable=False)
    code = Column(String(32), nullable=False, unique=True, index=True)
    integration_type = Column(String(30), nullable=False, default="REST")
    api_base_url = Column(String(500), nullable=True)
    credentials_secret_ref = Column(String(255), nullable=True)
    webhook_secret_ref = Column(String(255), nullable=True)
    revenue_share_pct = Column(Numeric(6, 4), nullable=True)
    currency = Column(String(8), nullable=False, default="BRL")
    sla_pickup_hours = Column(Integer, nullable=False, default=72)
    active = Column(Boolean, nullable=False, default=True)
    country = Column(String(2), nullable=False, default="BR")
    status = Column(String(30), nullable=False, default="DRAFT")
    legal_name = Column(String(140), nullable=True)
    tax_id = Column(String(32), nullable=True)
    tier = Column(String(20), nullable=True, default="STANDARD")
    support_email = Column(String(128), nullable=True)
    support_phone = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class LogisticsPartner(Base):
    __tablename__ = "logistics_partners"

    id = Column(String(36), primary_key=True)
    name = Column(String(128), nullable=False)
    code = Column(String(32), nullable=False, unique=True, index=True)
    integration_type = Column(String(30), nullable=False, default="REST")
    api_base_url = Column(String(500), nullable=True)
    tracking_url_template = Column(String(500), nullable=True)
    auth_type = Column(String(20), nullable=True)
    credentials_secret_ref = Column(String(255), nullable=True)
    default_sla_hours = Column(Integer, nullable=False, default=72)
    reminder_hours_before = Column(Integer, nullable=False, default=24)
    active = Column(Boolean, nullable=False, default=True)
    country = Column(String(2), nullable=False, default="BR")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
