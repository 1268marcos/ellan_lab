from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class EcosystemSegmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    description: str | None
    sort_order: int


class PlayerRelationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    from_catalog_code: str
    to_catalog_code: str
    relation_type: str
    notes: str | None


class PlayerCapabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    catalog_code: str
    capability_code: str
    protocol: str
    direction: str


class LockerNetworkCatalogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    player_role: str
    parent_group: str
    segment_code: str | None = None
    country_code: str
    regions_json: str
    supports_lockers: bool
    supports_marketplace: bool
    supports_collection_points: bool = False
    supports_food_delivery: bool = False
    integration_modes_json: str = "[]"
    global_tier: str
    locker_operator_ref: str | None
    default_billing_model: str
    default_revenue_share_pct: Decimal | None
    monthly_fee_cents: int | None
    integration_status: str
    estimated_locker_count: int | None
    finance_partner_id: str | None
    finance_partner_code: str | None = None
    api_docs_url: str | None
    notes: str | None
    sort_order: int
    active: bool
    updated_at: datetime


class LockerNetworkCatalogListOut(BaseModel):
    items: list[LockerNetworkCatalogOut]
    total: int
    by_parent_group: dict[str, int] = Field(default_factory=dict)


class SegmentListOut(BaseModel):
    items: list[EcosystemSegmentOut]
    total: int


class RelationListOut(BaseModel):
    items: list[PlayerRelationOut]
    total: int


class CapabilityListOut(BaseModel):
    items: list[PlayerCapabilityOut]
    total: int


class PlayerAliasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alias_code: str
    catalog_code: str
    source: str
    notes: str | None


class CountryCoverageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    catalog_code: str
    country_code: str
    locker_service: bool
    pudo_service: bool
    marketplace_channel: bool
    food_pickup: bool


class IntegrationBlueprintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    target_segments_json: str
    auth_type: str
    primary_capability: str
    webhook_events_json: str
    reference_players_json: str
    docs_hint: str | None
    sort_order: int


class CatalogSyncOut(BaseModel):
    catalog_upserted: int
    partners_created: int
    partners_linked: int
    plans_created: int
    segments_upserted: int = 0
    relations_upserted: int = 0
    capabilities_upserted: int = 0
    relation_types_upserted: int = 0
    aliases_upserted: int = 0
    coverage_upserted: int = 0
    blueprints_upserted: int = 0


class IntegrationGuideOut(BaseModel):
    catalog_code: str
    name: str
    segment_code: str
    parent_group: str
    integration_status: str
    finance_partner_code: str | None = None
    blueprint: dict | None = None
    integration_steps: list[str] = Field(default_factory=list)
    capabilities: list[dict] = Field(default_factory=list)
    relations: list[dict] = Field(default_factory=list)
    country_coverage: list[dict] = Field(default_factory=list)
    readiness: dict | None = None
    cross_refs: dict = Field(default_factory=dict)
