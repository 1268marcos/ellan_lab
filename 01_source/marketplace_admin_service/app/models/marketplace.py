from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MarketplaceSeller(Base):
    __tablename__ = "marketplace_sellers"

    id = Column(String(36), primary_key=True)
    legal_name = Column(String(140), nullable=False)
    trade_name = Column(String(140), nullable=True)
    tax_id = Column(String(32), nullable=False, unique=True)
    email = Column(String(128), nullable=False)
    phone = Column(String(32), nullable=True)
    website = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="PENDING_APPROVAL")
    commission_pct = Column(Numeric(5, 2), nullable=False, default=5.00)
    monthly_fee_cents = Column(BigInteger, nullable=False, default=0)
    seller_rating = Column(Numeric(3, 2), nullable=True, default=0)
    total_sales_cents = Column(BigInteger, nullable=False, default=0)
    total_orders = Column(Integer, nullable=False, default=0)
    joined_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    suspended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class SellerProduct(Base):
    __tablename__ = "seller_products"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    locker_id = Column(String(36), nullable=False)
    product_id = Column(String(255), nullable=False)
    seller_sku = Column(String(64), nullable=True)
    price_cents = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    max_quantity_per_order = Column(Integer, nullable=False, default=10)
    status = Column(String(20), nullable=False, default="ACTIVE")
    priority = Column(Integer, nullable=False, default=100)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class MarketplaceCommission(Base):
    __tablename__ = "marketplace_commissions"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    order_id = Column(String(36), nullable=False)
    order_item_id = Column(BigInteger, nullable=True)
    commission_rate_pct = Column(Numeric(5, 2), nullable=False)
    commission_amount_cents = Column(Integer, nullable=False)
    ellan_fee_cents = Column(Integer, nullable=False)
    payment_gateway_fee_cents = Column(Integer, nullable=False)
    net_to_seller_cents = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    settled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SellerReview(Base):
    __tablename__ = "seller_reviews"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    order_id = Column(String(36), nullable=False)
    user_id = Column(String(36), nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    delivery_rating = Column(Integer, nullable=True)
    product_quality_rating = Column(Integer, nullable=True)
    communication_rating = Column(Integer, nullable=True)
    verified_purchase = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
