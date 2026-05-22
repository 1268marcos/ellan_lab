from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from app.core.database import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaymentGatewayDeviceRegistry(Base):
    __tablename__ = "payment_gateway_device_registry"

    device_hash = Column(Text, primary_key=True)
    version = Column(Text, nullable=False)
    first_seen_at_epoch = Column(BigInteger, nullable=False)
    last_seen_at_epoch = Column(BigInteger, nullable=False)
    seen_count = Column(Integer, nullable=False, default=1)
    region_code = Column(String(20), nullable=True)
    locker_id = Column(String(120), nullable=True)
    flags_json = Column(JsonType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PaymentGatewayIdempotencyKey(Base):
    __tablename__ = "payment_gateway_idempotency_keys"

    id = Column(Text, primary_key=True)
    endpoint = Column(Text, nullable=False)
    idem_key = Column(Text, nullable=False)
    payload_hash = Column(Text, nullable=False)
    response_blob = Column(JsonType, nullable=False, default=dict)
    status = Column(Text, nullable=False)
    region_code = Column(String(20), nullable=True)
    sales_channel = Column(String(50), nullable=True)
    request_fingerprint = Column(Text, nullable=True)
    created_at_epoch = Column(BigInteger, nullable=False)
    expires_at_epoch = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PaymentGatewayRiskEvent(Base):
    __tablename__ = "payment_gateway_risk_events"

    id = Column(Text, primary_key=True)
    request_id = Column(Text, nullable=False, index=True)
    event_type = Column(Text, nullable=False)
    decision = Column(Text, nullable=False)
    score = Column(Integer, nullable=False)
    policy_id = Column(Text, nullable=False)
    region_code = Column(String(20), nullable=False)
    locker_id = Column(String(120), nullable=False)
    slot = Column(Integer, nullable=False)
    audit_event_id = Column(Text, nullable=False)
    reasons_json = Column(JsonType, nullable=False, default=list)
    signals_json = Column(JsonType, nullable=False, default=dict)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    created_at_epoch = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
