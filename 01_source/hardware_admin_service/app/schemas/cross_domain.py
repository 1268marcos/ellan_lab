from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HardwareEcosystemPlayerIn(BaseModel):
    id: str | None = None
    player_code: str
    name: str
    segment: str
    parent_group: str = "LOCKER_NETWORK"
    integration_mode: str = "DIRECT_API"
    supports_lockers: bool = True
    supports_marketplace: bool = False
    supports_food_delivery: bool = False
    supports_aggregation: bool = False
    primary_country: str
    vendor_id: str | None = None
    operator_id: str | None = None
    marketplace_channel_code: str | None = None
    ml_network_code: str | None = None
    payment_provider_code: str | None = None
    finance_catalog_code: str | None = None
    fiscal_corridor_code: str | None = None
    carrier_code: str | None = None
    regions_json: list[str] = Field(default_factory=list)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class HardwareEcosystemPlayerUpdate(BaseModel):
    name: str | None = None
    segment: str | None = None
    integration_mode: str | None = None
    supports_lockers: bool | None = None
    supports_marketplace: bool | None = None
    supports_food_delivery: bool | None = None
    supports_aggregation: bool | None = None
    primary_country: str | None = None
    vendor_id: str | None = None
    operator_id: str | None = None
    marketplace_channel_code: str | None = None
    ml_network_code: str | None = None
    payment_provider_code: str | None = None
    finance_catalog_code: str | None = None
    fiscal_corridor_code: str | None = None
    carrier_code: str | None = None
    regions_json: list[str] | None = None
    metadata_json: dict[str, Any] | None = None
    is_active: bool | None = None


class HardwareEcosystemPlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    player_code: str
    name: str
    segment: str
    parent_group: str
    integration_mode: str
    supports_lockers: bool
    supports_marketplace: bool
    supports_food_delivery: bool
    supports_aggregation: bool
    primary_country: str
    vendor_id: str | None
    operator_id: str | None
    marketplace_channel_code: str | None
    ml_network_code: str | None
    payment_provider_code: str | None
    finance_catalog_code: str | None
    fiscal_corridor_code: str | None
    carrier_code: str | None
    regions_json: list[Any]
    metadata_json: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class HardwareEcosystemPlayerListOut(BaseModel):
    items: list[HardwareEcosystemPlayerOut]
    total: int


class HardwareLockerMarketplaceLinkIn(BaseModel):
    seller_id: str
    seller_name: str | None = None
    channel_partner_id: str
    channel_code: str
    channel_name: str | None = None
    locker_id: str | None = None
    vendor_id: str | None = None
    priority: int = 100
    active: bool = True


class HardwareLockerMarketplaceLinkUpdate(BaseModel):
    seller_name: str | None = None
    channel_code: str | None = None
    channel_name: str | None = None
    locker_id: str | None = None
    vendor_id: str | None = None
    priority: int | None = None
    active: bool | None = None


class HardwareLockerMarketplaceLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    seller_id: str
    seller_name: str | None
    channel_partner_id: str
    channel_code: str
    channel_name: str | None
    locker_id: str | None
    vendor_id: str | None
    priority: int
    active: bool
    created_at: datetime


class HardwareLockerMarketplaceLinkListOut(BaseModel):
    items: list[HardwareLockerMarketplaceLinkOut]
    total: int


class HardwareLockerPaymentBindingIn(BaseModel):
    locker_id: str
    payment_method_code: str
    payment_provider_code: str | None = None
    payment_interface_code: str | None = None
    is_active: bool = True
    priority: int = 100
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class HardwareLockerPaymentBindingUpdate(BaseModel):
    payment_provider_code: str | None = None
    payment_interface_code: str | None = None
    is_active: bool | None = None
    priority: int | None = None
    metadata_json: dict[str, Any] | None = None


class HardwareLockerPaymentBindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    locker_id: str
    payment_method_code: str
    payment_provider_code: str | None
    payment_interface_code: str | None
    is_active: bool
    priority: int
    metadata_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class HardwareLockerPaymentBindingListOut(BaseModel):
    items: list[HardwareLockerPaymentBindingOut]
    total: int


class HardwareLockerCarrierBindingIn(BaseModel):
    locker_id: str
    carrier_code: str
    carrier_name: str
    service_level: str = "STANDARD"
    country_code: str
    operator_id: str | None = None
    tracking_prefix: str | None = None
    is_active: bool = True
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class HardwareLockerCarrierBindingUpdate(BaseModel):
    carrier_name: str | None = None
    service_level: str | None = None
    country_code: str | None = None
    operator_id: str | None = None
    tracking_prefix: str | None = None
    is_active: bool | None = None
    metadata_json: dict[str, Any] | None = None


class HardwareLockerCarrierBindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    locker_id: str
    carrier_code: str
    carrier_name: str
    service_level: str
    country_code: str
    operator_id: str | None
    tracking_prefix: str | None
    is_active: bool
    metadata_json: dict[str, Any]
    created_at: datetime


class HardwareLockerCarrierBindingListOut(BaseModel):
    items: list[HardwareLockerCarrierBindingOut]
    total: int


class HardwareDomainReferenceIn(BaseModel):
    locker_id: str
    domain_type: str
    external_id: str
    external_code: str | None = None
    relation_type: str = "LINK"
    notes: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    active: bool = True


class HardwareDomainReferenceUpdate(BaseModel):
    external_id: str | None = None
    external_code: str | None = None
    relation_type: str | None = None
    notes: str | None = None
    metadata_json: dict[str, Any] | None = None
    active: bool | None = None


class HardwareDomainReferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    locker_id: str
    domain_type: str
    external_id: str
    external_code: str | None
    relation_type: str
    notes: str | None
    metadata_json: dict[str, Any]
    active: bool
    created_at: datetime


class HardwareDomainReferenceListOut(BaseModel):
    items: list[HardwareDomainReferenceOut]
    total: int


class HardwareCrossDomainDashboardOut(BaseModel):
    vendors: int
    operators: int
    runtime_lockers: int
    assets: int
    ecosystem_players: int
    marketplace_links: int
    payment_bindings: int
    carrier_bindings: int
    domain_references: int
    capex_records: int
    opex_records: int
    locker_features: int
    locker_slots: int
    devices: int
    sync_pending: int
    telemetry_24h: int
