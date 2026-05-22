from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MlPlayerCapabilityOut(BaseModel):
    id: str
    network_player_id: str
    network_player_code: str
    capability_code: str
    capability_name: str
    protocol: str
    direction: str
    enabled: bool
    sandbox_ready: bool
    production_ready: bool


class MlPlayerCapabilityListOut(BaseModel):
    items: list[MlPlayerCapabilityOut]
    total: int


class MlPlayerRelationOut(BaseModel):
    id: str
    from_player_code: str | None
    to_player_code: str | None
    relation_type: str
    strength: str
    active: bool


class MlPlayerRelationListOut(BaseModel):
    items: list[MlPlayerRelationOut]
    total: int


class MlMarketPresenceOut(BaseModel):
    id: str
    network_player_code: str
    country: str
    region_code: str | None
    service_level: str
    locker_density: str
    active: bool


class MlMarketPresenceListOut(BaseModel):
    items: list[MlMarketPresenceOut]
    total: int


class MlEcosystemSummaryOut(BaseModel):
    integration_capabilities: int
    player_capabilities: int
    player_relations: int
    market_presence_rows: int
    tier1_players: int


class MlIntegrationCapabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    category: str
    default_protocol: str
    description: str | None = None
    sort_order: int


class MlIntegrationCapabilityListOut(BaseModel):
    items: list[MlIntegrationCapabilityOut]
    total: int
