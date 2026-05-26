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
    integration_readiness_rows: int = 0
    integration_go_live: int = 0
    integration_open_incidents: int = 0
    integration_avg_score: float = 0.0


class IntegrationReadinessOut(BaseModel):
    channel_partner_id: str
    partner_code: str
    score_total: float
    score_capabilities: float
    score_api: float
    score_operations: float
    readiness_band: str
    blockers: list[str] = []
    ml_network_code: Optional[str] = None
    computed_at: datetime

    model_config = {"from_attributes": True}


class IntegrationReadinessListOut(BaseModel):
    items: list[IntegrationReadinessOut]
    total: int


class IntegrationIncidentOut(BaseModel):
    id: str
    channel_partner_id: str
    partner_code: str
    severity: str
    incident_type: str
    title: str
    status: str
    opened_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class IntegrationIncidentListOut(BaseModel):
    items: list[IntegrationIncidentOut]
    total: int


class IntegrationHubSummaryOut(BaseModel):
    readiness_rows: int
    avg_score: float
    bands: dict[str, int]
    open_incidents: int
    open_readiness_alerts: int = 0
    partners_with_blockers: int
    top_go_live: list[dict]


class ReadinessAlertOut(BaseModel):
    id: str
    channel_partner_id: str
    partner_code: str
    alert_type: str
    severity: str
    previous_score: Optional[float] = None
    new_score: float
    score_delta: float
    previous_band: Optional[str] = None
    new_band: str
    status: str
    webhook_dispatched: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ReadinessAlertListOut(BaseModel):
    items: list[ReadinessAlertOut]
    total: int


class CapabilityWebhookIn(BaseModel):
    channel_partner_id: str
    capability_code: str
    url: str
    secret: Optional[str] = None
    events: list[str] | None = None
    active: bool = True


class CapabilityWebhookOut(BaseModel):
    id: str
    channel_partner_id: str
    partner_code: str
    capability_code: str
    url: str
    active: bool
    event_types: list[str] = []
    last_http_status: Optional[int] = None
    last_delivered_at: Optional[datetime] = None
    last_error: Optional[str] = None

    model_config = {"from_attributes": True}


class CapabilityWebhookListOut(BaseModel):
    items: list[CapabilityWebhookOut]
    total: int


class SimulateScoreDropIn(BaseModel):
    partner_code: str
    new_score: float = Field(ge=0, le=100)


class SyncAuditLogOut(BaseModel):
    id: str
    event_type: str
    entity_type: str
    entity_id: Optional[str] = None
    summary: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SyncAuditLogListOut(BaseModel):
    items: list[SyncAuditLogOut]
    total: int


class MarketplaceCertificationOut(BaseModel):
    id: str
    partner_code: str
    certification_type: str
    status: str
    issuer: Optional[str] = None
    issued_at: Optional[date] = None
    expires_at: Optional[date] = None
    evidence_url: Optional[str] = None

    model_config = {"from_attributes": True}


class MarketplaceCorridorStepOut(BaseModel):
    id: str
    step_order: int
    partner_code: str
    step_role: str

    model_config = {"from_attributes": True}


class MarketplaceGlobalCorridorOut(BaseModel):
    id: str
    corridor_code: str
    name: str
    origin_country: str
    dest_country: str
    primary_partner_code: str
    fallback_partner_code: Optional[str] = None
    handoff_type: str
    service_level: str
    transit_days_min: int
    transit_days_max: int
    supports_returns: bool
    active: bool
    priority: int
    steps: list[MarketplaceCorridorStepOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class MarketplaceCorridorSlaOut(BaseModel):
    id: str
    corridor_code: str
    uptime_target_pct: float
    on_time_delivery_pct: float
    max_transit_hours: int
    webhook_p95_latency_ms: int
    compliance_status: str
    breach_count: int

    model_config = {"from_attributes": True}


class CapabilityWebhookDeliveryMktOut(BaseModel):
    id: str
    webhook_id: str
    event_type: str
    http_status: Optional[int] = None
    success: bool
    response_snippet: Optional[str] = None
    status: str = "DELIVERED"
    attempt_count: int = 1
    replay_of_delivery_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PriorityWorldPlayerOut(BaseModel):
    partner_id: str
    code: str
    role: str
    regions: list[str]
    listing: bool
    locker_network: bool
    notes: str
    in_catalog: bool = False
    partner_active: bool = False
    supports_lockers: bool = False
    supports_marketplace: bool = False
    readiness_band: Optional[str] = None
    score_total: Optional[float] = None


class PriorityWorldPlayersOut(BaseModel):
    players: list[PriorityWorldPlayerOut]
    total: int


class SellerPlayerCoverageRowOut(BaseModel):
    partner_code: str
    partner_id: str
    role: str
    regions: list[str]
    notes: str
    has_marketplace_listing: bool
    listing_status: Optional[str] = None
    external_store_id: Optional[str] = None
    has_locker_network: bool
    locker_id: Optional[str] = None
    network_priority: Optional[int] = None
    partner_active: bool
    expected_listing: bool
    expected_locker_network: bool
    coverage_complete: bool


class SellerPlayerCoverageOut(BaseModel):
    seller_id: str
    priority_players_total: int
    coverage_complete_count: int
    coverage_pct: float
    players: list[SellerPlayerCoverageRowOut]


class MarketplaceGlobalOpsSummaryOut(BaseModel):
    certifications: int
    certifications_valid: int
    corridors_active: int
    corridor_steps: int
    corridor_sla_rows: int = 0
    certifications_mirrored: int = 0
