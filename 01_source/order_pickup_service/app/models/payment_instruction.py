# 01_source/order_pickup_service/app/models/payment_instruction.py
# 13/04/2026

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.db import Base


class PaymentInstruction(Base):
    __tablename__ = "payment_instructions"

    id = Column(String, primary_key=True)
    order_id = Column(String, nullable=False, index=True)

    instruction_type = Column(String(50), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    status = Column(String(30), nullable=False, default="PENDING")

    expires_at = Column(DateTime, nullable=True)

    qr_code = Column(Text, nullable=True)
    qr_code_text = Column(Text, nullable=True)

    authorization_code = Column(String(100), nullable=True)
    captured_at = Column(DateTime, nullable=True)

    redirect_url = Column(Text, nullable=True)
    provider_payment_id = Column(String(120), nullable=True)
    provider_name = Column(String(80), nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

