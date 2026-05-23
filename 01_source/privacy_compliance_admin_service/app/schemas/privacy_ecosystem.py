from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EcosystemPlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    player_segment: str
    network_type: str
    region_group: str
    countries: list[str] = Field(default_factory=list)
    regulation_codes: list[str] = Field(default_factory=list)
    privacy_roles: list[str] = Field(default_factory=list)
    data_shared: list[str] = Field(default_factory=list)
    hardware_vendor: str | None = None
    global_player_code: str | None = None
    website_url: str | None = None
    privacy_contact_email: str | None = None
    rental_network_id: str | None = None
    active: bool = True


class EcosystemPlayerListOut(BaseModel):
    items: list[EcosystemPlayerOut]
    total: int
    regulation_code: str | None = None
    player_segment: str | None = None
    region_group: str | None = None
    summary: str | None = None


class EcosystemRelationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    from_player_code: str
    from_player_name: str
    to_player_code: str
    to_player_name: str
    relation_type: str
    integration_mode: str
    description: str | None = None
    active: bool = True


class EcosystemRelationListOut(BaseModel):
    items: list[EcosystemRelationOut]
    total: int


class EcosystemMetaOut(BaseModel):
    player_segments: list[str]
    relation_types: list[str]
    regulation_summaries: dict[str, str]
    player_count: int
    relation_count: int


class LockerNetworkPlayerOut(BaseModel):
    """Compatível com endpoint /locker-networks legado."""

    id: str
    code: str
    name: str
    network_type: str
    player_segment: str | None = None
    region_group: str
    countries: list[str] = Field(default_factory=list)
    regulation_codes: list[str] = Field(default_factory=list)
    privacy_role: str | None = None
    data_shared: list[str] = Field(default_factory=list)
    website_url: str | None = None


class LockerNetworkPlayerListOut(BaseModel):
    items: list[LockerNetworkPlayerOut]
    total: int
    regulation_code: str | None = None
    summary: str | None = None
