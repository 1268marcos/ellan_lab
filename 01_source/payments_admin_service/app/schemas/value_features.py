from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class IntegrationMilestoneOut(_Orm):
    id: str
    player_code: str
    phase: str
    title: str
    status: str
    target_date: date | None
    completed_at: datetime | None
    owner_team: str | None
    blockers_json: list[str] | Any


class IntegrationMilestoneListOut(BaseModel):
    items: list[IntegrationMilestoneOut]
    total: int


class IntegrationMilestoneIn(BaseModel):
    player_code: str = Field(..., min_length=2, max_length=64)
    phase: str = Field(..., max_length=30)
    title: str = Field(..., min_length=2, max_length=200)
    status: str = Field(default="PLANNED", max_length=20)
    target_date: date | None = None
    owner_team: str | None = None
    blockers_json: list[str] = Field(default_factory=list)


class IntegrationMilestoneUpdate(BaseModel):
    phase: str | None = None
    title: str | None = None
    status: str | None = None
    target_date: date | None = None
    owner_team: str | None = None
    blockers_json: list[str] | None = None
    completed_at: datetime | None = None


class SettlementCorridorOut(_Orm):
    id: str
    corridor_code: str
    origin_country: str
    destination_country: str
    source_player_code: str
    settlement_player_code: str
    source_currency: str
    settlement_currency: str
    fx_provider_code: str | None
    fee_basis_points: int
    settlement_delay_days: int
    is_active: bool


class SettlementCorridorListOut(BaseModel):
    items: list[SettlementCorridorOut]
    total: int


class PlayerComplianceOut(_Orm):
    id: str
    player_code: str
    country_code: str
    regulatory_framework: str
    kyc_level: str
    pci_scope: str
    gdpr_ready: bool
    audit_status: str
    risk_tier: str
    last_audit_at: date | None
    notes: str | None


class PlayerComplianceListOut(BaseModel):
    items: list[PlayerComplianceOut]
    total: int


class RoutingRuleOut(_Orm):
    id: str
    rule_code: str
    tenant_id: str | None
    country_code: str
    payment_method: str
    sales_channel: str | None
    primary_player_code: str
    fallback_player_code: str | None
    priority: int
    min_amount_cents: int | None
    max_amount_cents: int | None
    is_active: bool
    rationale: str | None


class RoutingRuleListOut(BaseModel):
    items: list[RoutingRuleOut]
    total: int


class RoutingRuleIn(BaseModel):
    rule_code: str = Field(..., min_length=2, max_length=64)
    country_code: str = Field(..., min_length=2, max_length=2)
    payment_method: str = Field(..., max_length=40)
    primary_player_code: str = Field(..., max_length=64)
    fallback_player_code: str | None = None
    sales_channel: str | None = None
    tenant_id: str | None = None
    priority: int = Field(default=100, ge=1, le=9999)
    min_amount_cents: int | None = Field(None, ge=0)
    max_amount_cents: int | None = Field(None, ge=0)
    is_active: bool = True
    rationale: str | None = None


class RoutingRuleUpdate(BaseModel):
    country_code: str | None = None
    payment_method: str | None = None
    primary_player_code: str | None = None
    fallback_player_code: str | None = None
    sales_channel: str | None = None
    priority: int | None = Field(None, ge=1, le=9999)
    min_amount_cents: int | None = Field(None, ge=0)
    max_amount_cents: int | None = Field(None, ge=0)
    is_active: bool | None = None
    rationale: str | None = None


class IntegrationIncidentOut(_Orm):
    id: str
    player_code: str
    severity: str
    incident_type: str
    title: str
    status: str
    started_at: datetime
    resolved_at: datetime | None
    impact_pct: float | None
    affected_orders_estimate: int | None


class IntegrationIncidentListOut(BaseModel):
    items: list[IntegrationIncidentOut]
    total: int


class EcosystemGraphNode(BaseModel):
    id: str
    code: str
    label: str
    segment: str
    integration_status: str
    readiness_score: int | None = None


class EcosystemGraphEdge(BaseModel):
    from_code: str
    to_code: str
    relation_type: str


class EcosystemGraphOut(BaseModel):
    nodes: list[EcosystemGraphNode]
    edges: list[EcosystemGraphEdge]
    node_count: int
    edge_count: int


class RoutingSuggestionOut(BaseModel):
    country_code: str
    payment_method: str
    amount_cents: int | None
    primary_player_code: str
    fallback_player_code: str | None
    rule_code: str
    rationale: str | None
    readiness_score: int | None


class GlobalReadinessOut(BaseModel):
    players_total: int
    production_integrations: int
    avg_readiness: float
    open_incidents: int
    critical_incidents: int
    milestones_in_progress: int
    milestones_blocked: int
    active_corridors: int
    compliance_approved: int
    active_routing_rules: int
    top_risk_players: list[str]
