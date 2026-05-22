from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from app.core.database import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaymentMethodCatalog(Base):
    __tablename__ = "payment_method_catalog"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(80), nullable=False, unique=True, index=True)
    name = Column(String(120), nullable=False)
    family = Column(String(80), nullable=True)
    is_wallet = Column(Boolean, nullable=False, default=False)
    is_card = Column(Boolean, nullable=False, default=False)
    is_bnpl = Column(Boolean, nullable=False, default=False)
    is_cash_like = Column(Boolean, nullable=False, default=False)
    is_bank_transfer = Column(Boolean, nullable=False, default=False)
    is_instant = Column(Boolean, nullable=False, default=False)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PaymentInterfaceCatalog(Base):
    __tablename__ = "payment_interface_catalog"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(80), nullable=False, unique=True, index=True)
    name = Column(String(120), nullable=False)
    interface_type = Column(String(60), nullable=True)
    requires_hw = Column(Boolean, nullable=False, default=False)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PaymentMethodUiAlias(Base):
    __tablename__ = "payment_method_ui_alias"

    id = Column(String(64), primary_key=True)
    ui_code = Column(String(80), nullable=False, index=True)
    canonical_method_code = Column(String(80), nullable=False)
    default_payment_interface_code = Column(String(80), nullable=True)
    default_wallet_provider_code = Column(String(80), nullable=True)
    requires_customer_phone = Column(Boolean, nullable=False, default=False)
    requires_wallet_provider = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)


class LockerPaymentMethod(Base):
    __tablename__ = "locker_payment_methods"

    locker_id = Column(String(120), primary_key=True)
    method = Column(String(64), primary_key=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)
