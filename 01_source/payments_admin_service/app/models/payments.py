from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from app.core.database import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(36), nullable=False, index=True)
    gateway = Column(String(50), nullable=False)
    gateway_transaction_id = Column(String(128), nullable=True)
    gateway_idempotency_key = Column(String(128), nullable=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    payment_method = Column(String(30), nullable=False)
    card_brand = Column(String(20), nullable=True)
    card_last4 = Column(String(4), nullable=True)
    card_type = Column(String(10), nullable=True)
    installments = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="INITIATED")
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    reconciliation_status = Column(String(20), nullable=False, default="PENDING")
    reconciliation_batch_id = Column(String(100), nullable=True)
    gateway_fee_cents = Column(Integer, nullable=False, default=0)
    net_amount_cents = Column(Integer, nullable=True)
    initiated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PaymentInstruction(Base):
    __tablename__ = "payment_instructions"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(36), nullable=False, index=True)
    instruction_type = Column(String(50), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    status = Column(String(30), nullable=False, default="PENDING")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    qr_code_text = Column(Text, nullable=True)
    provider_payment_id = Column(Text, nullable=True)
    provider_name = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PaymentSplit(Base):
    __tablename__ = "payment_splits"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(36), nullable=False, index=True)
    recipient_type = Column(String(30), nullable=False)
    recipient_id = Column(String(36), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    percentage = Column(Numeric(5, 2), nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")
    settled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Text, primary_key=True)
    order_id = Column(Text, nullable=False, index=True)
    provider = Column(Text, nullable=False)
    provider_payment_id = Column(Text, nullable=True)
    method = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(Text, nullable=False, default="EUR")
    created_at = Column(BigInteger, nullable=False)
    confirmed_at = Column(BigInteger, nullable=True)
    idempotency_key = Column(Text, nullable=True)
    raw_json = Column(JsonType, nullable=False, default=dict)


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(String(36), primary_key=True)
    partner_type = Column(String(20), nullable=False)
    partner_id = Column(String(36), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    events = Column(Text, nullable=False, default='["payment.*"]')
    secret_ref = Column(String(255), nullable=True)
    signing_algo = Column(String(20), nullable=False, default="HMAC_SHA256")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class GatewayEvent(Base):
    __tablename__ = "gateway_events"

    id = Column(Text, primary_key=True)
    gateway_id = Column(Text, nullable=False)
    region = Column(Text, nullable=False)
    locker_id = Column(Text, nullable=False)
    porta = Column(Integer, nullable=True)
    event_type = Column(Text, nullable=False)
    created_at = Column(BigInteger, nullable=False)
    request_id = Column(Text, nullable=True)
    order_id = Column(Text, nullable=True, index=True)
    payload_json = Column(JsonType, nullable=False, default=dict)
