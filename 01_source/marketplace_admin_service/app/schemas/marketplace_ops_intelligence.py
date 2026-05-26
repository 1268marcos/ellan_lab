from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SellerHealthSnapshotOut(BaseModel):
    id: str
    seller_id: str
    snapshot_date: date
    health_score: Decimal
    health_band: str
    coverage_pct: Decimal
    readiness_avg: Decimal
    open_incidents: int
    kyc_status: str | None = None
    risk_level: str | None = None
    factors: list[str] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


class SellerHealthListOut(BaseModel):
    snapshots: list[SellerHealthSnapshotOut]
    total: int


class OpsPlaybookOut(BaseModel):
    id: str
    code: str
    name: str
    trigger_type: str
    severity: str
    steps: list[dict]
    owner_team: str | None = None
    active: bool

    model_config = {"from_attributes": True}


class OpsPlaybookListOut(BaseModel):
    playbooks: list[OpsPlaybookOut]
    total: int


class SellerChannelQuotaOut(BaseModel):
    id: str
    seller_id: str
    channel_partner_id: str
    partner_code: str | None = None
    max_active_skus: int
    max_orders_per_day: int
    max_lockers_linked: int
    current_skus: int
    current_orders_today: int
    quota_status: str
    utilization_skus_pct: float = 0
    utilization_orders_pct: float = 0

    model_config = {"from_attributes": True}


class SellerChannelQuotaListOut(BaseModel):
    quotas: list[SellerChannelQuotaOut]
    total: int


class CatalogSyncJobCreateIn(BaseModel):
    seller_id: str
    channel_partner_id: str
    job_type: str = "FULL_CATALOG_PUSH"
    items_total: int = 0


class CatalogSyncJobOut(BaseModel):
    id: str
    seller_id: str
    channel_partner_id: str
    partner_code: str | None = None
    job_type: str
    status: str
    items_total: int
    items_ok: int
    items_failed: int
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_summary: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CatalogSyncJobListOut(BaseModel):
    jobs: list[CatalogSyncJobOut]
    total: int


class CrossBorderProfileCreateIn(BaseModel):
    seller_id: str
    corridor_code: str
    customs_scheme: str
    origin_country: str
    dest_country: str
    ioss_number: str | None = None
    vat_number: str | None = None
    eori_number: str | None = None
    status: str = "PENDING"
    notes: str | None = None


class CrossBorderProfileOut(BaseModel):
    id: str
    seller_id: str
    corridor_code: str
    customs_scheme: str
    ioss_number: str | None = None
    vat_number: str | None = None
    eori_number: str | None = None
    origin_country: str
    dest_country: str
    status: str
    verified_at: datetime | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


class CrossBorderProfileListOut(BaseModel):
    profiles: list[CrossBorderProfileOut]
    total: int


class PartnerApiHealthOut(BaseModel):
    id: str
    channel_partner_id: str
    partner_code: str
    measured_at: datetime
    availability_pct: Decimal
    p95_latency_ms: int
    error_rate_pct: Decimal
    rate_limit_hits: int
    health_status: str
    notes: str | None = None

    model_config = {"from_attributes": True}


class PartnerApiHealthListOut(BaseModel):
    snapshots: list[PartnerApiHealthOut]
    total: int


class PromotionCampaignCreateIn(BaseModel):
    seller_id: str
    channel_partner_id: str
    campaign_code: str
    name: str
    discount_pct: float | None = None
    starts_at: datetime
    ends_at: datetime
    status: str = "DRAFT"
    budget_cents: int = 0


class PromotionCampaignOut(BaseModel):
    id: str
    seller_id: str
    channel_partner_id: str
    partner_code: str | None = None
    campaign_code: str
    name: str
    discount_pct: Decimal | None = None
    starts_at: datetime
    ends_at: datetime
    status: str
    budget_cents: int
    spent_cents: int

    model_config = {"from_attributes": True}


class PromotionCampaignListOut(BaseModel):
    campaigns: list[PromotionCampaignOut]
    total: int


class OpsIntelligenceSummaryOut(BaseModel):
    playbooks_total: int
    api_health_degraded: int
    sellers_with_health: int
    active_promotions: int
    sync_jobs_running: int
    cross_border_profiles: int
