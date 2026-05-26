from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class PlayerSegmentOut(BaseModel):
    code: str
    name: str
    parent_group: str
    description: str | None = None
    default_integration_mode: str
    sort_order: int
    active: bool
    partner_count: int = 0

    model_config = {"from_attributes": True}


class PlayerSegmentListOut(BaseModel):
    segments: list[PlayerSegmentOut]
    total: int


class PlayerRelationshipOut(BaseModel):
    id: str
    from_partner_id: str
    from_partner_code: str | None = None
    to_partner_id: str
    to_partner_code: str | None = None
    relationship_type: str
    corridor_code: str | None = None
    notes: str | None = None
    active: bool

    model_config = {"from_attributes": True}


class PlayerRelationshipListOut(BaseModel):
    relationships: list[PlayerRelationshipOut]
    total: int


class CorridorOut(BaseModel):
    code: str
    name: str
    origin_country: str
    destination_country: str
    corridor_type: str
    currency: str
    active: bool
    notes: str | None = None
    player_count: int = 0

    model_config = {"from_attributes": True}


class CorridorPlayerOut(BaseModel):
    id: str
    corridor_code: str
    channel_partner_id: str
    partner_code: str | None = None
    partner_name: str | None = None
    player_role_in_corridor: str
    priority: int
    active: bool

    model_config = {"from_attributes": True}


class CorridorDetailOut(CorridorOut):
    players: list[CorridorPlayerOut] = Field(default_factory=list)


class CorridorListOut(BaseModel):
    corridors: list[CorridorOut]
    total: int


class SellerIntegrationPlanOut(BaseModel):
    id: str
    seller_id: str
    channel_partner_id: str
    partner_code: str | None = None
    integration_path: str
    status: str
    target_go_live: date | None = None
    primary_capability: str | None = None
    via_partner_id: str | None = None
    corridor_code: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SellerIntegrationPlanCreateIn(BaseModel):
    seller_id: str
    channel_partner_id: str
    integration_path: str = "DIRECT_API"
    status: str = "PLANNED"
    target_go_live: date | None = None
    primary_capability: str | None = None
    via_partner_id: str | None = None
    corridor_code: str | None = None
    notes: str | None = None


class SellerIntegrationPlanListOut(BaseModel):
    plans: list[SellerIntegrationPlanOut]
    total: int


class WorldEcosystemMapOut(BaseModel):
    segments_total: int
    partners_total: int
    relationships_total: int
    corridors_total: int
    catalog_players_total: int
    parent_groups: dict[str, int]
