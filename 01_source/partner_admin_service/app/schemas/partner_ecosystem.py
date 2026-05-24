from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class EcosystemPlayerOut(BaseModel):
    id: str
    code: str
    name: str
    player_role: str
    parent_group: str
    country: str
    regions: list[str] = Field(default_factory=list)
    supports_lockers: bool
    supports_marketplace: bool
    integration_mode: str
    marketplace_channel_id: Optional[str] = None
    marketplace_channel_code: Optional[str] = None
    locker_operator_ref: Optional[str] = None
    ecommerce_partner_code: Optional[str] = None
    api_docs_url: Optional[str] = None
    notes: Optional[str] = None
    global_tier: str
    finance_catalog_code: str | None = None
    sort_order: int
    active: bool


class EcosystemPlayerListOut(BaseModel):
    items: list[EcosystemPlayerOut]
    total: int
    priority_count: int
    catalog_source: str = "marketplace_channel_players"


class EcosystemSyncOut(BaseModel):
    inserted: int
    updated: int
    total: int


class EcosystemLinkCreateIn(BaseModel):
    ecosystem_player_id: str
    partner_type: str = Field(default="ECOMMERCE", description="ECOMMERCE|LOGISTICS")
    link_role: str = Field(default="CHANNEL")
    is_primary: bool = False
    integration_status: str = Field(default="PLANNED")
    notes: Optional[str] = None


class EcosystemLinkOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    ecosystem_player_id: str
    player_code: str
    player_name: str
    parent_group: str
    global_tier: str
    link_role: str
    is_primary: bool
    integration_status: str
    notes: Optional[str] = None
    locker_operator_ref: Optional[str] = None
    marketplace_channel_code: Optional[str] = None
    created_at: datetime


class EcosystemLinkListOut(BaseModel):
    partner_id: str
    items: list[EcosystemLinkOut]
    total: int


class EcosystemSummaryOut(BaseModel):
    total_players: int
    by_parent_group: dict[str, int]
    integration_capabilities: int
    player_capabilities: int
    player_relations: int
    market_presence_rows: int
    priority_players: int


class IntegrationMatrixGroupOut(BaseModel):
    parent_group: str
    total: int
    players: list[dict]


class PlayerCapabilityOut(BaseModel):
    id: str
    player_code: str
    capability_code: str
    capability_name: str
    protocol: str
    direction: str
    sandbox_ready: bool
    production_ready: bool


class PlayerRelationOut(BaseModel):
    id: str
    from_player_code: Optional[str] = None
    to_player_code: Optional[str] = None
    relation_type: str
    strength: str


class MarketPresenceOut(BaseModel):
    player_code: str
    country: str
    service_level: str
    locker_density: str


class PlayerCertificationOut(BaseModel):
    id: str
    player_code: str
    certification_type: str
    status: str
    issuer: Optional[str] = None
    issued_at: Optional[date] = None
    expires_at: Optional[date] = None
    evidence_url: Optional[str] = None

    model_config = {"from_attributes": True}


class GlobalCorridorOut(BaseModel):
    id: str
    corridor_code: str
    name: str
    origin_country: str
    dest_country: str
    primary_player_code: str
    fallback_player_code: Optional[str] = None
    handoff_type: str
    service_level: str
    transit_days_min: int
    transit_days_max: int
    supports_returns: bool
    active: bool
    priority: int

    model_config = {"from_attributes": True}


class EcosystemReadinessOut(BaseModel):
    ecosystem_player_id: str
    player_code: str
    score_total: float
    score_certifications: float
    score_capabilities: float
    score_corridors: float
    score_webhooks: float
    readiness_band: str
    blockers: list[str] = Field(default_factory=list)
    computed_at: datetime


class RelationHealthOut(BaseModel):
    id: str
    from_player_code: str
    to_player_code: str
    relation_type: str
    health_status: str
    cascade_from_player_code: Optional[str] = None
    last_check_at: datetime

    model_config = {"from_attributes": True}


class CorridorSlaOut(BaseModel):
    id: str
    corridor_code: str
    uptime_target_pct: float
    on_time_delivery_pct: float
    max_transit_hours: int
    webhook_p95_latency_ms: int
    compliance_status: str
    breach_count: int

    model_config = {"from_attributes": True}


class CertificationMirrorOut(BaseModel):
    from_marketplace: dict[str, int] = Field(default_factory=dict)
    to_marketplace: dict[str, int] = Field(default_factory=dict)


class GlobalOpsSummaryOut(BaseModel):
    certifications: int
    certifications_valid: int
    corridors_active: int
    corridor_sla_rows: int = 0
    certifications_mirrored: int = 0
    readiness_by_band: dict[str, int] = Field(default_factory=dict)
    relation_health: dict[str, int] = Field(default_factory=dict)
