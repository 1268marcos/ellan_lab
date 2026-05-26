from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ListOut(BaseModel):
    items: list[Any]
    total: int


class ChannelIn(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    is_active: bool = True


class ChannelOut(OrmModel):
    id: int
    code: str
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ContextIn(BaseModel):
    channel_id: int
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    is_active: bool = True


class ContextOut(OrmModel):
    id: int
    channel_id: int
    code: str
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RegionIn(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=120)
    country_code: str | None = None
    continent: str | None = None
    default_currency: str = Field(min_length=3, max_length=10)
    is_active: bool = True
    metadata_json: dict = Field(default_factory=dict)


class RegionOut(OrmModel):
    id: int
    code: str
    name: str
    country_code: str | None
    continent: str | None
    default_currency: str
    is_active: bool
    metadata_json: dict
    created_at: datetime
    updated_at: datetime


class ProfileIn(BaseModel):
    region_id: int
    channel_id: int
    context_id: int
    profile_code: str = Field(min_length=1, max_length=160)
    name: str = Field(min_length=1, max_length=180)
    priority: int = 100
    currency: str = Field(min_length=3, max_length=10)
    is_active: bool = True
    metadata_json: dict = Field(default_factory=dict)


class ProfileOut(OrmModel):
    id: int
    region_id: int
    channel_id: int
    context_id: int
    profile_code: str
    name: str
    priority: int
    currency: str
    is_active: bool
    metadata_json: dict
    created_at: datetime
    updated_at: datetime


class ProfileDetailOut(ProfileOut):
    actions: list[dict] = Field(default_factory=list)
    methods: list[dict] = Field(default_factory=list)
    constraints: list[dict] = Field(default_factory=list)
    targets: list[dict] = Field(default_factory=list)
    webhook: dict | None = None
    api_key_prefix: str | None = None


class CatalogMethodIn(BaseModel):
    code: str
    name: str
    family: str | None = None
    is_wallet: bool = False
    is_card: bool = False
    is_bnpl: bool = False
    is_cash_like: bool = False
    is_bank_transfer: bool = False
    is_instant: bool = False
    is_active: bool = True
    metadata_json: dict = Field(default_factory=dict)


class CountryIn(BaseModel):
    code: str = Field(min_length=2, max_length=2)
    name: str
    continent: str | None = None
    default_currency: str | None = None
    default_timezone: str | None = None
    is_active: bool = True
    metadata_json: dict | None = None


class ProvinceIn(BaseModel):
    code: str
    name: str
    country_code: str | None = None
    region: str | None = None
    timezone: str | None = None
    is_active: bool = True
    metadata_json: dict | None = None


class LockerLocationIn(BaseModel):
    external_id: str | None = None
    province_code: str | None = None
    city_name: str | None = None
    district: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None
    address_street: str | None = None
    address_number: str | None = None
    is_active: bool = True
    has_ble: bool = False
    operating_hours_json: dict | None = None
    metadata_json: dict | None = None


class WebhookIn(BaseModel):
    profile_id: int
    url: str
    secret: str | None = None
    events: list[str] | None = None
    active: bool = True


class WebhookOut(OrmModel):
    id: str
    profile_id: int
    profile_code: str
    url: str
    event_types_json: str
    active: bool
    last_http_status: int | None
    last_delivered_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ApiKeyRotateOut(BaseModel):
    api_key: str
    key_prefix: str
    profile_id: int
    profile_code: str


class DashboardOut(BaseModel):
    channels: int
    contexts: int
    regions: int
    profiles: int
    active_profiles: int
    payment_methods: int
    countries: int
    provinces: int
    locker_locations: int
    webhooks: int
    ecosystem_segments: int = 0
    ecosystem_players: int = 0
    player_bindings: int = 0
    matrix_coverage_pct: float = 0.0
    audit_events_24h: int = 0
