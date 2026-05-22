from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CategoryCreateIn(BaseModel):
    code: str
    name: str
    parent_id: Optional[str] = None
    active: bool = True
    sort_order: int = 100


class CategoryOut(BaseModel):
    id: str
    code: str
    name: str
    parent_id: Optional[str] = None
    active: bool
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryListOut(BaseModel):
    categories: list[CategoryOut]
    total: int


class SellerCategoryLinkCreateIn(BaseModel):
    seller_id: str
    category_id: str
    is_primary: bool = False


class SellerCategoryLinkOut(BaseModel):
    id: str
    seller_id: str
    category_id: str
    is_primary: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SellerCategoryLinkListOut(BaseModel):
    links: list[SellerCategoryLinkOut]
    total: int


class SellerContactCreateIn(BaseModel):
    seller_id: str
    contact_type: str = "PRIMARY"
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_primary: bool = False


class SellerContactOut(BaseModel):
    id: str
    seller_id: str
    contact_type: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_primary: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SellerContactListOut(BaseModel):
    contacts: list[SellerContactOut]
    total: int


class PayoutAccountCreateIn(BaseModel):
    seller_id: str
    account_type: str = "PIX"
    label: Optional[str] = None
    pix_key: Optional[str] = None
    bank_code: Optional[str] = None
    branch: Optional[str] = None
    account_number: Optional[str] = None
    holder_name: str
    holder_tax_id: Optional[str] = None
    is_default: bool = False


class PayoutAccountOut(BaseModel):
    id: str
    seller_id: str
    account_type: str
    label: Optional[str] = None
    pix_key: Optional[str] = None
    bank_code: Optional[str] = None
    branch: Optional[str] = None
    account_number: Optional[str] = None
    holder_name: str
    holder_tax_id: Optional[str] = None
    is_default: bool
    verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PayoutAccountListOut(BaseModel):
    accounts: list[PayoutAccountOut]
    total: int


class SettlementBatchCreateIn(BaseModel):
    seller_id: str
    period_start: date
    period_end: date
    fees_cents: int = 0
    notes: Optional[str] = None


class SettlementBatchUpdateIn(BaseModel):
    status: Optional[str] = None
    settlement_ref: Optional[str] = None
    notes: Optional[str] = None


class SettlementBatchOut(BaseModel):
    id: str
    seller_id: str
    period_start: date
    period_end: date
    currency: str
    commission_count: int
    gross_net_cents: int
    fees_cents: int
    net_payout_cents: int
    status: str
    settled_at: Optional[datetime] = None
    settlement_ref: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SettlementBatchListOut(BaseModel):
    batches: list[SettlementBatchOut]
    total: int


class SettlementItemOut(BaseModel):
    id: str
    batch_id: str
    commission_id: str
    order_id: str
    net_to_seller_cents: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SettlementItemListOut(BaseModel):
    items: list[SettlementItemOut]
    total: int


class KycDocumentCreateIn(BaseModel):
    seller_id: str
    doc_type: str
    file_ref: Optional[str] = None
    notes: Optional[str] = None


class KycDocumentUpdateIn(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    file_ref: Optional[str] = None


class KycDocumentOut(BaseModel):
    id: str
    seller_id: str
    doc_type: str
    status: str
    file_ref: Optional[str] = None
    notes: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class KycDocumentListOut(BaseModel):
    documents: list[KycDocumentOut]
    total: int


class DisputeCreateIn(BaseModel):
    commission_id: str
    seller_id: str
    reason: str


class DisputeUpdateIn(BaseModel):
    status: str
    resolution_notes: Optional[str] = None


class DisputeOut(BaseModel):
    id: str
    commission_id: str
    seller_id: str
    reason: str
    status: str
    resolution_notes: Optional[str] = None
    opened_at: datetime
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DisputeListOut(BaseModel):
    disputes: list[DisputeOut]
    total: int


class ChannelCapabilityOut(BaseModel):
    capability_code: str
    protocol: str
    direction: str
    enabled: bool
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class ChannelPartnerOut(BaseModel):
    id: str
    code: str
    name: str
    partner_role: str
    country: str
    website: Optional[str] = None
    integration_type: str
    locker_operator_ref: Optional[str] = None
    ecommerce_partner_code: Optional[str] = None
    supports_marketplace: bool
    supports_lockers: bool
    active: bool
    sort_order: int
    parent_group: str = "MARKETPLACE"
    integration_mode: str = "DIRECT_API"
    regions_json: str = "[]"
    api_docs_url: Optional[str] = None
    notes: Optional[str] = None
    capabilities: list[ChannelCapabilityOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class IntegrationMatrixGroupOut(BaseModel):
    parent_group: str
    partners: list[ChannelPartnerOut]
    total: int


class IntegrationMatrixOut(BaseModel):
    groups: list[IntegrationMatrixGroupOut]
    total_partners: int


class ChannelPartnerListOut(BaseModel):
    partners: list[ChannelPartnerOut]
    total: int


class SellerChannelListingCreateIn(BaseModel):
    seller_id: str
    channel_partner_id: str
    external_store_id: Optional[str] = None
    listing_status: str = "ACTIVE"
    commission_override_pct: Optional[Decimal] = None


class SellerChannelListingOut(BaseModel):
    id: str
    seller_id: str
    channel_partner_id: str
    external_store_id: Optional[str] = None
    listing_status: str
    commission_override_pct: Optional[Decimal] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SellerChannelListingListOut(BaseModel):
    listings: list[SellerChannelListingOut]
    total: int


class SellerLockerNetworkLinkCreateIn(BaseModel):
    seller_id: str
    channel_partner_id: str
    locker_id: Optional[str] = None
    priority: int = 100
    active: bool = True


class SellerLockerNetworkLinkOut(BaseModel):
    id: str
    seller_id: str
    channel_partner_id: str
    locker_id: Optional[str] = None
    priority: int
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SellerLockerNetworkLinkListOut(BaseModel):
    links: list[SellerLockerNetworkLinkOut]
    total: int


class MarketplaceDashboardOut(BaseModel):
    sellers_total: int
    sellers_active: int
    sellers_pending_approval: int
    products_active: int
    commissions_pending: int
    commissions_pending_cents: int
    commissions_settled: int
    open_disputes: int
    settlement_batches_draft: int
    kyc_pending: int
    avg_seller_rating: Optional[float] = None
    channel_partners_active: int = 0
    seller_channel_listings: int = 0
    locker_network_links: int = 0
