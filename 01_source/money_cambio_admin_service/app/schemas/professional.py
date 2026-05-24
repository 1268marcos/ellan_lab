from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class OperatingCountryIn(BaseModel):
    country_code: str = Field(..., min_length=2, max_length=2)
    name: str
    continent: str | None = None
    default_currency_code: str
    regulatory_zone: str
    primary_languages_json: list[str] = Field(default_factory=list)
    locker_networks_json: list[str] = Field(default_factory=list)
    metadata_json: dict = Field(default_factory=dict)
    is_active: bool = True


class OperatingCountryUpdate(BaseModel):
    name: str | None = None
    continent: str | None = None
    default_currency_code: str | None = None
    regulatory_zone: str | None = None
    primary_languages_json: list[str] | None = None
    locker_networks_json: list[str] | None = None
    metadata_json: dict | None = None
    is_active: bool | None = None


class OperatingCountryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country_code: str
    name: str
    continent: str | None
    default_currency_code: str
    regulatory_zone: str
    primary_languages_json: list
    locker_networks_json: list
    metadata_json: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime


class OperatingCountryListOut(BaseModel):
    items: list[OperatingCountryOut]
    total: int


class MethodCountryMatrixIn(BaseModel):
    country_code: str
    payment_method_code: str
    min_amount_cents: int = 0
    max_amount_cents: int | None = None
    is_instant_settlement: bool = False
    requires_kyc_above_cents: int | None = None
    sort_order: int = 100
    is_active: bool = True


class MethodCountryMatrixOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country_code: str
    payment_method_code: str
    min_amount_cents: int
    max_amount_cents: int | None
    is_instant_settlement: bool
    requires_kyc_above_cents: int | None
    sort_order: int
    is_active: bool
    created_at: datetime


class MethodCountryMatrixListOut(BaseModel):
    items: list[MethodCountryMatrixOut]
    total: int


class WalletCountryMatrixIn(BaseModel):
    country_code: str
    wallet_provider_code: str
    is_active: bool = True


class WalletCountryMatrixOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    country_code: str
    wallet_provider_code: str
    is_active: bool
    created_at: datetime


class WalletCountryMatrixListOut(BaseModel):
    items: list[WalletCountryMatrixOut]
    total: int


class PaymentCorridorIn(BaseModel):
    id: str | None = None
    corridor_code: str
    name: str
    origin_country_code: str
    destination_country_code: str
    transaction_currency: str
    settlement_currency: str
    corridor_type: str = "CROSS_BORDER"
    default_spread_bps: int = 0
    fx_partner_code: str | None = None
    notes: str | None = None
    is_active: bool = True


class PaymentCorridorUpdate(BaseModel):
    name: str | None = None
    default_spread_bps: int | None = None
    fx_partner_code: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class PaymentCorridorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    corridor_code: str
    name: str
    origin_country_code: str
    destination_country_code: str
    transaction_currency: str
    settlement_currency: str
    corridor_type: str
    default_spread_bps: int
    fx_partner_code: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PaymentCorridorListOut(BaseModel):
    items: list[PaymentCorridorOut]
    total: int


class CorridorMarkupIn(BaseModel):
    corridor_id: str
    partner_code: str | None = None
    markup_bps: int = 0
    valid_from: date
    valid_until: date | None = None
    is_active: bool = True


class CorridorMarkupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    corridor_id: str
    partner_code: str | None
    markup_bps: int
    valid_from: date
    valid_until: date | None
    is_active: bool
    created_at: datetime


class CorridorMarkupListOut(BaseModel):
    items: list[CorridorMarkupOut]
    total: int


class ComplianceLimitIn(BaseModel):
    country_code: str
    currency_code: str
    limit_type: str
    amount_cents: int
    description: str | None = None
    regulatory_ref: str | None = None
    is_active: bool = True


class ComplianceLimitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    country_code: str
    currency_code: str
    limit_type: str
    amount_cents: int
    description: str | None
    regulatory_ref: str | None
    is_active: bool
    created_at: datetime


class ComplianceLimitListOut(BaseModel):
    items: list[ComplianceLimitOut]
    total: int


class FxRateAuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    base_currency: str
    quote_currency: str
    rate_date: date
    old_rate: float | None
    new_rate: float
    source: str
    changed_by: str
    created_at: datetime


class FxRateAuditListOut(BaseModel):
    items: list[FxRateAuditOut]
    total: int


class LockerPlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    player_code: str
    name: str
    segment: str
    primary_country: str
    regions_json: list
    default_settlement_currency: str
    finance_catalog_code: str | None
    fiscal_corridor_code: str | None
    cambio_corridor_code: str | None
    notes: str | None
    is_active: bool


class LockerPlayerListOut(BaseModel):
    items: list[LockerPlayerOut]
    total: int


class EcosystemLinkOut(BaseModel):
    player_code: str
    name: str
    finance_catalog_code: str | None
    fiscal_corridor_code: str | None
    cambio_corridor_code: str | None
    finance_admin_path: str
    fiscal_admin_path: str


class EcosystemMatrixOut(BaseModel):
    items: list[EcosystemLinkOut]
    total: int


class EcosystemSegmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    description: str | None
    sort_order: int
    is_active: bool
    player_count: int = 0


class EcosystemSegmentListOut(BaseModel):
    items: list[EcosystemSegmentOut]
    total: int


class PlayerRelationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    from_player_code: str
    to_player_code: str
    relation_type: str
    notes: str | None
    is_active: bool


class PlayerRelationListOut(BaseModel):
    items: list[PlayerRelationOut]
    total: int


class EcosystemIntelligenceOut(BaseModel):
    segments: list[EcosystemSegmentOut]
    relations_total: int
    players_total: int
    by_segment: dict[str, int]
    integration_modes: list[str]


class GlobalOpsDashboardOut(BaseModel):
    currencies: int
    countries: int
    payment_methods: int
    wallets: int
    corridors: int
    fx_rates: int
    method_matrix_rows: int
    compliance_limits: int
    integration_partners: int
    locker_players: int
    ecosystem_segments: int = 0
    player_relations: int = 0
    avg_player_readiness: float = 0.0
    open_insights: int = 0
    open_fx_alerts: int = 0
    world_coverage_pct: float
    readiness_grade: str
