from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MlLockerNetworkPlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    marketplace_channel_id: str | None
    marketplace_channel_code: str | None
    locker_operator_ref: str | None
    ecommerce_partner_code: str | None
    api_docs_url: str | None
    ml_scoring_weight: float = 1.0
    ml_notes: str | None
    global_tier: str = "REGIONAL"
    integration_status: str = "PLANNED"
    data_source: str = "CATALOG"
    finance_catalog_code: str | None = None
    sort_order: int
    active: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("regions", mode="before")
    @classmethod
    def parse_regions(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except json.JSONDecodeError:
                return []
        return []


class MlLockerNetworkPlayerListOut(BaseModel):
    items: list[MlLockerNetworkPlayerOut]
    total: int
    priority_codes: list[str] = Field(default_factory=list)


class MlNetworkMlProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    network_player_id: str
    network_player_code: str | None = None
    use_case_id: str | None
    use_case_code: str | None = None
    telemetry_density: str
    drift_baseline_psi: float | None = None
    feature_pack: list[str] = Field(default_factory=list)
    active: bool
    created_at: datetime

    @field_validator("feature_pack", mode="before")
    @classmethod
    def parse_feature_pack(cls, v):
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                return json.loads(v) if v else []
            except json.JSONDecodeError:
                return []
        return []

    @field_validator("drift_baseline_psi", mode="before")
    @classmethod
    def decimal_to_float(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        return v


class MlNetworkMlProfileListOut(BaseModel):
    items: list[MlNetworkMlProfileOut]
    total: int


class MlNetworkSeedResultOut(BaseModel):
    inserted: int
    updated: int
    profiles_created: int
    partners_linked: int
    catalog_size: int
    capability_catalog: int = 0
    player_capabilities: int = 0
    player_relations: int = 0
    market_presence: int = 0
