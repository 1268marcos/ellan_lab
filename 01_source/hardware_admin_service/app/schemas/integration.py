from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HardwarePlayerSegmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    parent_group: str
    description: str | None
    sort_order: int
    is_active: bool


class HardwarePlayerSegmentListOut(BaseModel):
    items: list[HardwarePlayerSegmentOut]
    total: int


class HardwarePlayerIntegrationCapabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    player_id: str
    player_code: str
    capability_code: str
    protocol: str
    direction: str
    target_domain: str
    is_active: bool
    created_at: datetime


class HardwarePlayerIntegrationCapabilityListOut(BaseModel):
    items: list[HardwarePlayerIntegrationCapabilityOut]
    total: int


class HardwareEcosystemPlayerRelationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    from_player_id: str
    from_player_code: str
    to_player_id: str
    to_player_code: str
    relation_type: str
    notes: str | None
    metadata_json: dict[str, Any]
    is_active: bool
    created_at: datetime


class HardwareEcosystemPlayerRelationListOut(BaseModel):
    items: list[HardwareEcosystemPlayerRelationOut]
    total: int


class HardwareLockerChannelBindingIn(BaseModel):
    locker_id: str
    channel_type: str
    player_code: str
    player_name: str
    player_id: str | None = None
    integration_mode: str = "DIRECT_API"
    priority: int = 100
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class HardwareLockerChannelBindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    locker_id: str
    channel_type: str
    player_id: str | None
    player_code: str
    player_name: str
    integration_mode: str
    priority: int
    metadata_json: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class HardwareLockerChannelBindingListOut(BaseModel):
    items: list[HardwareLockerChannelBindingOut]
    total: int


class HardwareIntegrationHubSummaryOut(BaseModel):
    segments: int
    ecosystem_players: int
    capabilities: int
    player_relations: int
    locker_channel_bindings: int
    food_delivery_bindings: int
    aggregator_bindings: int
    marketplace_bindings: int
    readiness_rows: int = 0
    avg_score: float = 0.0
    bands: dict[str, int] = Field(default_factory=dict)
    partners_with_blockers: int = 0
    marketplace_partners_linked: int = 0
    capabilities_in_sync: int = 0
    marketplace_capability_gaps: int = 0
    open_incidents: int = 0
    open_readiness_alerts: int = 0
    certifications: int = 0
    corridors: int = 0
    onboarding_runs_active: int = 0


class HardwareIntegrationReadinessOut(BaseModel):
    player_id: str
    player_code: str
    marketplace_partner_code: str | None
    score_total: float
    score_capabilities: float
    score_api: float
    score_operations: float
    readiness_band: str
    blockers: list[str]
    capability_count: int
    computed_at: datetime


class HardwareIntegrationReadinessListOut(BaseModel):
    items: list[HardwareIntegrationReadinessOut]
    total: int


class HardwareMarketplaceBridgePlayerOut(BaseModel):
    hardware_player_code: str
    marketplace_partner_code: str
    marketplace_channel_partner_id: str | None
    capabilities_expected: int
    capabilities_db: int
    in_sync: bool
    missing_capabilities: list[str]
    extra_capabilities: list[str]


class HardwareMarketplaceBridgeOut(BaseModel):
    marketplace_partners_linked: int
    capabilities_in_sync: int
    marketplace_capability_gaps: int
    capabilities_catalog_expected: int
    capabilities_db_enabled: int
    items: list[HardwareMarketplaceBridgePlayerOut]
