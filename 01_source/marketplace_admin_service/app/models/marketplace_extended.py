from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MarketplaceCategory(Base):
    __tablename__ = "marketplace_categories"

    id = Column(String(36), primary_key=True)
    code = Column(String(32), nullable=False, unique=True)
    name = Column(String(128), nullable=False)
    parent_id = Column(String(36), nullable=True, index=True)
    active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=100)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SellerCategoryLink(Base):
    __tablename__ = "seller_category_links"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    category_id = Column(String(36), nullable=False, index=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SellerContact(Base):
    __tablename__ = "seller_contacts"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    contact_type = Column(String(20), nullable=False, default="PRIMARY")
    name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=True)
    phone = Column(String(32), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class SellerPayoutAccount(Base):
    __tablename__ = "seller_payout_accounts"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    account_type = Column(String(20), nullable=False, default="PIX")
    label = Column(String(64), nullable=True)
    pix_key = Column(String(128), nullable=True)
    bank_code = Column(String(10), nullable=True)
    branch = Column(String(10), nullable=True)
    account_number = Column(String(20), nullable=True)
    holder_name = Column(String(140), nullable=False)
    holder_tax_id = Column(String(32), nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class SellerSettlementBatch(Base):
    __tablename__ = "seller_settlement_batches"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    commission_count = Column(Integer, nullable=False, default=0)
    gross_net_cents = Column(BigInteger, nullable=False, default=0)
    fees_cents = Column(BigInteger, nullable=False, default=0)
    net_payout_cents = Column(BigInteger, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="DRAFT")
    settled_at = Column(DateTime(timezone=True), nullable=True)
    settlement_ref = Column(String(128), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class SellerSettlementItem(Base):
    __tablename__ = "seller_settlement_items"

    id = Column(String(36), primary_key=True)
    batch_id = Column(String(36), nullable=False, index=True)
    commission_id = Column(String(36), nullable=False)
    order_id = Column(String(36), nullable=False)
    net_to_seller_cents = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SellerKycDocument(Base):
    __tablename__ = "seller_kyc_documents"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    doc_type = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    file_ref = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class MarketplaceChannelPartner(Base):
    __tablename__ = "marketplace_channel_partners"

    id = Column(String(36), primary_key=True)
    code = Column(String(32), nullable=False, unique=True)
    name = Column(String(128), nullable=False)
    partner_role = Column(String(32), nullable=False)
    country = Column(String(2), nullable=False, default="BR")
    website = Column(String(255), nullable=True)
    integration_type = Column(String(30), nullable=False, default="REST")
    locker_operator_ref = Column(String(64), nullable=True)
    ecommerce_partner_code = Column(String(32), nullable=True)
    supports_marketplace = Column(Boolean, nullable=False, default=True)
    supports_lockers = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=100)
    notes = Column(Text, nullable=True)
    parent_group = Column(String(32), nullable=False, default="MARKETPLACE")
    integration_mode = Column(String(32), nullable=False, default="DIRECT_API")
    regions_json = Column(Text, nullable=False, default="[]")
    api_docs_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MarketplaceChannelCapability(Base):
    __tablename__ = "marketplace_channel_capabilities"

    id = Column(String(36), primary_key=True)
    channel_partner_id = Column(String(36), nullable=False, index=True)
    capability_code = Column(String(40), nullable=False)
    protocol = Column(String(20), nullable=False, default="REST")
    direction = Column(String(10), nullable=False, default="INBOUND")
    enabled = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SellerChannelListing(Base):
    __tablename__ = "seller_channel_listings"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    channel_partner_id = Column(String(36), nullable=False, index=True)
    external_store_id = Column(String(128), nullable=True)
    listing_status = Column(String(20), nullable=False, default="ACTIVE")
    commission_override_pct = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class SellerLockerNetworkLink(Base):
    __tablename__ = "seller_locker_network_links"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    channel_partner_id = Column(String(36), nullable=False, index=True)
    locker_id = Column(String(36), nullable=True)
    priority = Column(Integer, nullable=False, default=100)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SellerCommissionDispute(Base):
    __tablename__ = "seller_commission_disputes"

    id = Column(String(36), primary_key=True)
    commission_id = Column(String(36), nullable=False, index=True)
    seller_id = Column(String(36), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="OPEN")
    resolution_notes = Column(Text, nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
