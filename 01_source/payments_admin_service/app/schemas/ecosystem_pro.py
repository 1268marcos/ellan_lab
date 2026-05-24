from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class _Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class EcosystemSegmentOut(_Orm):
    code: str
    name: str
    description: str | None
    sort_order: int
    default_protocol: str


class EcosystemSegmentListOut(BaseModel):
    items: list[EcosystemSegmentOut]
    total: int


class PlayerCountryCoverageOut(_Orm):
    id: str
    player_code: str
    country_code: str
    coverage_role: str
    is_primary_market: bool
    locker_density: str


class PlayerCountryCoverageListOut(BaseModel):
    items: list[PlayerCountryCoverageOut]
    total: int


class PlayerIntegrationOut(_Orm):
    id: str
    player_code: str
    integration_protocol: str
    sandbox_ready: bool
    production_ready: bool
    payment_capture_mode: str
    split_settlement_supported: bool
    cross_border_supported: bool
    readiness_score: int
    linked_domains_json: list[str] | Any
    integration_notes: str | None
    updated_at: datetime


class PlayerIntegrationListOut(BaseModel):
    items: list[PlayerIntegrationOut]
    total: int


class IntegrationPlaybookOut(BaseModel):
    segment_code: str
    segment_name: str
    recommended_protocol: str
    linked_domains: list[str]
    steps: list[str]
    example_players: list[str]
