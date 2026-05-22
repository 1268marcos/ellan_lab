from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MlDataPartnerIn(BaseModel):
    id: str | None = None
    name: str
    code: str
    partner_type: str = Field(default="TELEMETRY", description="TELEMETRY | SCORING | EXTERNAL")
    region_code: str | None = None
    network_player_code: str | None = None
    api_base_url: str | None = None
    active: bool = True


class MlDataPartnerUpdate(BaseModel):
    name: str | None = None
    partner_type: str | None = None
    region_code: str | None = None
    network_player_code: str | None = None
    api_base_url: str | None = None
    active: bool | None = None


class MlDataPartnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    partner_type: str
    region_code: str | None
    network_player_code: str | None = None
    api_base_url: str | None
    active: bool
    created_at: datetime
    updated_at: datetime


class MlDataPartnerListOut(BaseModel):
    partners: list[MlDataPartnerOut]
    total: int


class WebhookConfigureIn(BaseModel):
    url: str
    secret: str | None = None
    events: list[str] | None = None


class WebhookOut(BaseModel):
    partner_id: str
    url: str
    events: list[str]
    active: bool
    api_version: str


class ApiKeyRotateOut(BaseModel):
    api_key: str
    key_prefix: str


class ApiKeyMetaOut(BaseModel):
    id: str
    key_prefix: str
    label: str | None
    revoked_at: datetime | None
    created_at: datetime


class ApiKeyListOut(BaseModel):
    keys: list[ApiKeyMetaOut]
    total: int
