from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.data.catalog_global_players import CHANNEL_CODES, TAXONOMY_SCHEMES


class CategoryTaxonomyOut(BaseModel):
    id: str
    category_id: str
    taxonomy_scheme: str
    external_code: str
    external_name: str | None = None
    country_code: str | None = None
    is_primary: bool = False
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class CategoryTaxonomyListOut(BaseModel):
    ok: bool
    items: list[CategoryTaxonomyOut]


class CategoryTaxonomyCreateIn(BaseModel):
    category_id: str = Field(..., max_length=64)
    taxonomy_scheme: str = Field(..., max_length=40)
    external_code: str = Field(..., max_length=128)
    external_name: str | None = Field(default=None, max_length=255)
    country_code: str | None = Field(default=None, max_length=3)
    is_primary: bool = False
    metadata_json: dict[str, Any] | None = None


class CategoryTaxonomyUpdateIn(BaseModel):
    external_code: str | None = Field(default=None, max_length=128)
    external_name: str | None = Field(default=None, max_length=255)
    country_code: str | None = Field(default=None, max_length=3)
    is_primary: bool | None = None
    metadata_json: dict[str, Any] | None = None


class ProductChannelListingOut(BaseModel):
    id: str
    product_id: str
    channel_code: str
    external_sku: str | None = None
    external_category_id: str | None = None
    listing_status: str
    price_cents: int | None = None
    currency: str = "BRL"
    partner_id: str | None = None
    sync_mode: str = "MANUAL"
    last_synced_at: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class ProductChannelListingListOut(BaseModel):
    ok: bool
    total: int
    items: list[ProductChannelListingOut]


class ProductChannelListingCreateIn(BaseModel):
    product_id: str = Field(..., max_length=255)
    channel_code: str = Field(..., max_length=40)
    external_sku: str | None = Field(default=None, max_length=255)
    external_category_id: str | None = Field(default=None, max_length=128)
    listing_status: str = Field(default="DRAFT", max_length=20)
    price_cents: int | None = Field(default=None, ge=0)
    currency: str = Field(default="BRL", max_length=8)
    partner_id: str | None = Field(default=None, max_length=36)
    sync_mode: str = Field(default="MANUAL", max_length=20)
    metadata_json: dict[str, Any] | None = None


class ProductChannelListingUpdateIn(BaseModel):
    external_sku: str | None = Field(default=None, max_length=255)
    external_category_id: str | None = Field(default=None, max_length=128)
    listing_status: str | None = Field(default=None, max_length=20)
    price_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=8)
    partner_id: str | None = Field(default=None, max_length=36)
    sync_mode: str | None = Field(default=None, max_length=20)
    metadata_json: dict[str, Any] | None = None


class ProductAttributeDefinitionOut(BaseModel):
    id: str
    category_id: str | None = None
    attr_key: str
    attr_label: str
    data_type: str
    enum_values_json: list[str] | None = None
    is_required: bool = False
    sort_order: int = 0
    created_at: str


class ProductAttributeDefinitionListOut(BaseModel):
    ok: bool
    items: list[ProductAttributeDefinitionOut]


class ProductAttributeDefinitionCreateIn(BaseModel):
    category_id: str | None = Field(default=None, max_length=64)
    attr_key: str = Field(..., max_length=64)
    attr_label: str = Field(..., max_length=128)
    data_type: str = Field(default="STRING", max_length=20)
    enum_values: list[str] | None = None
    is_required: bool = False
    sort_order: int = 0


class ProductAttributeValueOut(BaseModel):
    id: str
    product_id: str
    definition_id: str
    attr_key: str | None = None
    attr_label: str | None = None
    value_text: str | None = None
    value_number: float | None = None
    value_bool: bool | None = None
    updated_at: str


class ProductAttributeValueListOut(BaseModel):
    ok: bool
    items: list[ProductAttributeValueOut]


class ProductAttributeValueUpsertIn(BaseModel):
    definition_id: str = Field(..., max_length=36)
    value_text: str | None = None
    value_number: float | None = None
    value_bool: bool | None = None


class CatalogProfessionalSeedOut(BaseModel):
    ok: bool
    taxonomy_rows: int
    channel_rows: int
    attribute_definitions: int
    locker_categories_created: int = 0
    global_players: GlobalPlayersSeedOut | None = None


class GlobalPlayerOut(BaseModel):
    code: str
    name: str
    player_type: str
    country: str
    supports_lockers: bool = False
    supports_pudo: bool = False
    supports_food_delivery: bool = False
    supports_marketplace: bool = False
    operator_id: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)


class GlobalPlayersCatalogOut(BaseModel):
    ok: bool
    taxonomy_schemes: list[str]
    channel_codes: list[str]
    player_types: list[str]
    capabilities: list[str]
    players: list[GlobalPlayerOut]
    source: str = "registry"


class GlobalPlayerDetailOut(GlobalPlayerOut):
    integration_modes: list[str] = Field(default_factory=list)
    eligibility: list[dict[str, str]] = Field(default_factory=list)


class GlobalPlayerListOut(BaseModel):
    ok: bool
    total: int
    items: list[GlobalPlayerOut]


class GlobalPlayersSeedOut(BaseModel):
    ok: bool
    players: int
    regions: int
    capabilities: int
    eligibility: int
    integrations: int
    operators_created: int = 0
    ecommerce_partners_created: int = 0
    logistics_partners_created: int = 0
    ecommerce_links: int = 0
    logistics_links: int = 0


class PlayerTypeCountOut(BaseModel):
    player_type: str
    count: int


class EcosystemOverviewOut(BaseModel):
    ok: bool
    source: str = "registry"
    players_total: int = 0
    players_locker_ready: int = 0
    taxonomy_mappings: int = 0
    channel_listings: int = 0
    eligibility_rules: int = 0
    integration_targets: int = 0
    ecommerce_partner_links: int = 0
    logistics_partner_links: int = 0
    locker_operators_total: int = 0
    locker_categories_global: int = 0
    players_by_type: list[PlayerTypeCountOut] = Field(default_factory=list)
    top_players: list[GlobalPlayerOut] = Field(default_factory=list)


class CategoryEligibilityOut(BaseModel):
    id: str
    category_id: str
    category_name: str | None = None
    player_code: str
    player_name: str | None = None
    eligibility: str
    notes: str | None = None
    created_at: str


class CategoryEligibilityListOut(BaseModel):
    ok: bool
    total: int
    items: list[CategoryEligibilityOut]


class CategoryEligibilityCreateIn(BaseModel):
    category_id: str = Field(..., max_length=64)
    player_code: str = Field(..., max_length=40)
    eligibility: str = Field(default="ALLOWED", max_length=20)
    notes: str | None = Field(default=None, max_length=500)


class PlayerIntegrationTargetOut(BaseModel):
    target_type: str
    target_key: str
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class PlayerIntegrationsOut(BaseModel):
    ok: bool
    player_code: str
    items: list[PlayerIntegrationTargetOut]
