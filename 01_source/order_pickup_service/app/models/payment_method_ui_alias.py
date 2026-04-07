# 01_source/order_pickup_service/app/models/payment_method_ui_alias.py
# 06/04/2026

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String

from app.core.db import Base


class PaymentMethodUiAlias(Base):
    __tablename__ = "payment_method_ui_alias"

    id = Column(String, primary_key=True)
    ui_code = Column(String(100), nullable=False, unique=True)
    canonical_method_code = Column(String(100), nullable=False)
    default_payment_interface_code = Column(String(100), nullable=True)
    default_wallet_provider_code = Column(String(100), nullable=True)
    requires_customer_phone = Column(Boolean, nullable=False, default=False)
    requires_wallet_provider = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

