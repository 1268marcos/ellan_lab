from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OrderRecord(Base):
    __tablename__ = "orders"

    id = Column(String(64), primary_key=True)
    channel = Column(String(32), nullable=False, default="KIOSK")
    region = Column(String(32), nullable=False, default="BR")
    totem_id = Column(String(100), nullable=False, default="")
    amount_cents = Column(Integer, nullable=False, default=0)
    currency = Column(String(8), nullable=False, default="BRL")
    status = Column(String(32), nullable=False, default="PENDING")
    payment_status = Column(String(32), nullable=False, default="PENDING")
    ecommerce_partner_id = Column(String(100), nullable=True, index=True)
    tenant_id = Column(String(100), nullable=True, index=True)
    partner_order_ref = Column(String(255), nullable=True)
    sku_id = Column(String(255), nullable=True)
    locker_id = Column(String(120), nullable=True)
    pickup_deadline_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)
    order_metadata = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PickupRecord(Base):
    __tablename__ = "pickups"

    id = Column(String(64), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    channel = Column(String(32), nullable=False, default="KIOSK")
    region = Column(String(32), nullable=False, default="BR")
    locker_id = Column(String(120), nullable=True, index=True)
    slot = Column(String(32), nullable=True)
    status = Column(String(32), nullable=False, default="PENDING")
    lifecycle_stage = Column(String(40), nullable=False, default="CREATED")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    ready_at = Column(DateTime(timezone=True), nullable=True)
    redeemed_at = Column(DateTime(timezone=True), nullable=True)
    fraud_flag = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class CreditRecord(Base):
    __tablename__ = "credits"

    id = Column(String(64), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    type = Column(String(32), nullable=False, default="REFUND")
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    status = Column(String(32), nullable=False, default="AVAILABLE")
    created_at_epoch = Column(BigInteger, nullable=False, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    meta_json = Column(Text, nullable=False, default="{}")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerOrderEventsOutbox(Base):
    __tablename__ = "partner_order_events_outbox"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    order_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    payload_json = Column(Text, nullable=False, default="{}")
    status = Column(String(20), nullable=False, default="PENDING")
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class OrderFulfillmentTracking(Base):
    __tablename__ = "order_fulfillment_tracking"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    fulfillment_type = Column(String(30), nullable=False, default="ECOMMERCE_PARTNER")
    partner_id = Column(String(36), nullable=True, index=True)
    status = Column(String(30), nullable=False, default="PENDING")
    last_event_type = Column(String(50), nullable=True)
    last_outbox_status = Column(String(20), nullable=True)
    allocated_at = Column(DateTime(timezone=True), nullable=True)
    dispensed_at = Column(DateTime(timezone=True), nullable=True)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
