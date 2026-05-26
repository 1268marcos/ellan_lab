from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SellerOnboardingTask(Base):
    __tablename__ = "seller_onboarding_tasks"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    task_code = Column(String(48), nullable=False)
    title = Column(String(160), nullable=False)
    category = Column(String(32), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    required = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=100)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completed_by = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SellerChannelSkuMap(Base):
    __tablename__ = "seller_channel_sku_maps"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    channel_partner_id = Column(String(36), nullable=False, index=True)
    internal_sku = Column(String(64), nullable=False)
    channel_sku = Column(String(128), nullable=False)
    seller_product_id = Column(String(36), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class SellerPricingRule(Base):
    __tablename__ = "seller_pricing_rules"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    channel_partner_id = Column(String(36), nullable=True)
    rule_type = Column(String(32), nullable=False)
    name = Column(String(128), nullable=False)
    min_price_cents = Column(Integer, nullable=True)
    max_discount_pct = Column(Numeric(5, 2), nullable=True)
    markup_pct = Column(Numeric(5, 2), nullable=True)
    currency = Column(String(8), nullable=False, default="BRL")
    priority = Column(Integer, nullable=False, default=100)
    active = Column(Boolean, nullable=False, default=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    conditions_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SellerReturnPolicy(Base):
    __tablename__ = "seller_return_policies"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    channel_partner_id = Column(String(36), nullable=True)
    policy_code = Column(String(48), nullable=False)
    return_window_days = Column(Integer, nullable=False, default=7)
    restocking_fee_pct = Column(Numeric(5, 2), nullable=False, default=0)
    accepts_locker_return = Column(Boolean, nullable=False, default=True)
    rma_required = Column(Boolean, nullable=False, default=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SellerNotificationSubscription(Base):
    __tablename__ = "seller_notification_subscriptions"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    event_type = Column(String(48), nullable=False)
    channel = Column(String(24), nullable=False)
    destination = Column(String(255), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    locale = Column(String(8), nullable=False, default="pt-BR")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SellerInventoryAllocation(Base):
    __tablename__ = "seller_inventory_allocations"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    seller_product_id = Column(String(36), nullable=False)
    channel_partner_id = Column(String(36), nullable=False)
    locker_id = Column(String(36), nullable=True)
    allocated_qty = Column(Integer, nullable=False, default=0)
    reserved_qty = Column(Integer, nullable=False, default=0)
    available_qty = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class SellerFulfillmentPreference(Base):
    __tablename__ = "seller_fulfillment_preferences"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, unique=True)
    default_locker_id = Column(String(36), nullable=True)
    split_shipments_allowed = Column(Boolean, nullable=False, default=False)
    max_packages_per_order = Column(Integer, nullable=False, default=1)
    prefer_nearest_locker = Column(Boolean, nullable=False, default=True)
    handoff_mode = Column(String(24), nullable=False, default="LOCKER_FIRST")
    packaging_notes = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
