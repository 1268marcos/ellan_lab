from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


SCOPE_TYPES = (
    "COUNTRY",
    "CHANNEL",
    "PARTNER",
    "PLAYER",
    "REGION",
    "TENANT",
    "LOCKER_OPERATOR",
    "MARKETPLACE",
)

CHANNEL_FAMILIES = (
    "GENERAL",
    "MARKETPLACE",
    "LOCKER_NETWORK",
    "CARRIER",
    "PUDO",
    "AGGREGATOR",
    "FOOD_DELIVERY",
)


class PromotionLockerPlayerOut(BaseModel):
    code: str
    display_name: str
    segment: str
    countries: list[str]
    aliases: list[str]
    notes: str | None = None


class LockerPlayerCatalogOut(BaseModel):
    ok: bool = True
    total: int
    items: list[PromotionLockerPlayerOut]
    featured_codes: list[str]


class PlayerSegmentSummary(BaseModel):
    segment: str
    count: int


class PlayerMatrixSummary(BaseModel):
    player_code: str
    active_promotions: int


class PromotionOverviewOut(BaseModel):
    ok: bool = True
    promotions_total: int
    promotions_active: int
    campaigns_total: int
    campaigns_active: int
    redemptions_24h: int
    redemptions_total: int
    top_promotion_codes: list[dict]
    top_player_scopes: list[dict]
    locker_players_catalog_size: int = 0
    featured_locker_players: list[str] = Field(default_factory=list)
    player_segments: list[PlayerSegmentSummary] = Field(default_factory=list)
    player_promotion_matrix: list[PlayerMatrixSummary] = Field(default_factory=list)


class PromotionCampaignCreateIn(BaseModel):
    code: str = Field(..., min_length=1, max_length=32)
    name: str = Field(..., min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=4000)
    channel_family: str = Field(default="GENERAL", max_length=32)
    primary_country: str | None = Field(default=None, max_length=8)
    priority: int = Field(default=100, ge=0, le=9999)
    max_stack_promotions: int = Field(default=1, ge=1, le=10)
    valid_from: datetime
    valid_until: datetime | None = None
    metadata_json: dict = Field(default_factory=dict)


class PromotionCampaignOut(BaseModel):
    id: str
    code: str
    name: str
    description: str | None = None
    channel_family: str
    primary_country: str | None = None
    priority: int
    max_stack_promotions: int
    is_active: bool
    valid_from: str
    valid_until: str | None = None
    metadata_json: dict
    promotions_count: int = 0
    created_at: str


class PromotionCampaignListOut(BaseModel):
    ok: bool
    total: int
    limit: int
    offset: int
    items: list[PromotionCampaignOut]


class PromotionCampaignStatusPatchIn(BaseModel):
    is_active: bool


class PromotionScopeCreateIn(BaseModel):
    scope_type: str = Field(..., min_length=1, max_length=32)
    scope_value: str = Field(..., min_length=1, max_length=128)
    mode: str = Field(default="INCLUDE", pattern="^(INCLUDE|EXCLUDE)$")
    notes: str | None = Field(default=None, max_length=255)


class PromotionScopeOut(BaseModel):
    id: str
    promotion_id: str
    scope_type: str
    scope_value: str
    mode: str
    notes: str | None = None
    created_at: str


class PromotionScopeListOut(BaseModel):
    ok: bool
    promotion_id: str
    total: int
    items: list[PromotionScopeOut]


class PromotionProductInclusionCreateIn(BaseModel):
    product_id: str = Field(..., min_length=1, max_length=255)


class PromotionProductInclusionOut(BaseModel):
    promotion_id: str
    product_id: str


class PromotionProductInclusionListOut(BaseModel):
    ok: bool
    total: int
    items: list[PromotionProductInclusionOut]


class PromotionRedemptionOut(BaseModel):
    id: str
    promotion_id: str
    campaign_id: str | None = None
    order_id: str
    user_id: str | None = None
    partner_id: str | None = None
    channel_code: str | None = None
    country_code: str | None = None
    player_code: str | None = None
    discount_cents: int
    currency: str
    redeemed_at: str


class PromotionRedemptionListOut(BaseModel):
    ok: bool
    total: int
    limit: int
    offset: int
    items: list[PromotionRedemptionOut]


class PromotionWorldSeedOut(BaseModel):
    ok: bool = True
    campaigns_inserted: int
    campaigns_skipped: int
    promotions_inserted: int
    promotions_skipped: int
    scopes_inserted: int
    global_players_inserted: int = 0
    player_aliases_inserted: int = 0
    player_relations_inserted: int = 0


class PromotionSimulateIn(BaseModel):
    promotion_code: str = Field(..., min_length=1, max_length=32)
    order_id: str = Field(default="SIM-PREVIEW", max_length=64)
    total_amount_cents: int = Field(default=0, ge=0)
    items: list[dict] = Field(default_factory=list)
    country_code: str | None = Field(default=None, max_length=8)
    channel_code: str | None = Field(default=None, max_length=32)
    player_code: str | None = Field(default=None, max_length=64)
    partner_id: str | None = Field(default=None, max_length=36)
    marketplace_code: str | None = Field(default=None, max_length=64)


class PromotionSimulateOut(BaseModel):
    ok: bool = True
    valid: bool
    reason: str | None = None
    promotion_id: str | None = None
    promotion_code: str | None = None
    promotion_name: str | None = None
    promotion_type: str | None = None
    discount_cents: int = 0
    total_amount_cents: int = 0
    net_amount_cents: int = 0
    dry_run: bool = True


class PromotionMatchIn(BaseModel):
    total_amount_cents: int = Field(default=0, ge=0)
    items: list[dict] = Field(default_factory=list)
    country_code: str | None = None
    channel_code: str | None = None
    player_code: str | None = None
    partner_id: str | None = None
    marketplace_code: str | None = None
    limit: int = Field(default=10, ge=1, le=50)


class PromotionMatchItemOut(BaseModel):
    promotion_id: str
    promotion_code: str
    promotion_name: str
    eligible: bool
    reason: str | None = None
    estimated_discount_cents: int = 0


class PromotionMatchOut(BaseModel):
    ok: bool = True
    total: int
    items: list[PromotionMatchItemOut]


class PromotionConflictOut(BaseModel):
    scope_type: str
    scope_value: str
    promotions_count: int
    promotions: list[dict]
    hint: str


class PromotionConflictsOut(BaseModel):
    ok: bool = True
    total: int
    items: list[PromotionConflictOut]


class PlayerPromotionMatrixOut(BaseModel):
    ok: bool = True
    items: list[dict]


class PromotionCloneIn(BaseModel):
    new_code: str = Field(..., min_length=1, max_length=32)
    new_name: str | None = Field(default=None, max_length=128)


class PromotionCloneOut(BaseModel):
    ok: bool = True
    promotion_id: str
    promotion_code: str
    source_id: str


class PromotionAuditEventOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    actor_id: str | None = None
    created_at: str
    payload_json: dict = Field(default_factory=dict)


class PromotionAuditListOut(BaseModel):
    ok: bool = True
    total: int
    items: list[PromotionAuditEventOut]
