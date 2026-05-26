from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BiLockerNetworkPlayerIn(BaseModel):
    code: str
    name: str
    player_role: str = "LOCKER_NETWORK"
    parent_group: str = "GLOBAL"
    country: str = "BR"
    regions: list[str] = Field(default_factory=lambda: ["BR"])
    supports_lockers: bool = True
    supports_marketplace: bool = False
    integration_mode: str = "API"
    global_tier: str = "TIER1"
    bi_priority_score: float = 50
    sort_order: int = 100


class BiLockerNetworkPlayerOut(BiLockerNetworkPlayerIn):
    id: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BiLockerNetworkPlayerListOut(BaseModel):
    players: list[BiLockerNetworkPlayerOut]
    total: int


class BiPlayerRelationIn(BaseModel):
    from_player_code: str
    to_player_code: str
    relation_type: str = "DATA_SHARE"
    notes: str | None = None


class BiPlayerRelationOut(BiPlayerRelationIn):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BiPlayerRelationListOut(BaseModel):
    relations: list[BiPlayerRelationOut]
    total: int
