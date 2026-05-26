from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class BiIntegrationProfileOut(BaseModel):
    id: str
    network_player_code: str
    segment_code: str
    integration_mode: str
    api_base_url: str | None = None
    auth_method: str
    webhook_support: bool
    bi_data_feed: bool
    ml_scoring_enabled: bool
    target_service: str
    docs_url: str | None = None
    status: str
    active: bool

    model_config = {"from_attributes": True}


class BiCapabilityLinkOut(BaseModel):
    id: str
    network_player_code: str
    capability_code: str
    capability_name: str | None = None
    protocol: str
    direction: str
    production_ready: bool

    model_config = {"from_attributes": True}


class BiCrossDomainOut(BaseModel):
    id: str
    source_player_code: str
    target_domain: str
    target_player_code: str | None = None
    integration_type: str
    route_path: str | None = None
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BiIntegrationMatrixOut(BaseModel):
    profiles: int
    capabilities: int
    cross_domain: int
    by_segment: dict[str, int]
    by_status: dict[str, int]
    ml_scoring_enabled: int
