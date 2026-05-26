from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BiDataPartnerIn(BaseModel):
    id: str | None = None
    name: str
    code: str
    partner_type: str = "WAREHOUSE"
    region_code: str | None = None
    api_base_url: str | None = None
    active: bool = True


class BiDataPartnerUpdate(BaseModel):
    name: str | None = None
    partner_type: str | None = None
    region_code: str | None = None
    api_base_url: str | None = None
    active: bool | None = None


class BiDataPartnerOut(BaseModel):
    id: str
    name: str
    code: str
    partner_type: str
    region_code: str | None = None
    api_base_url: str | None = None
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BiDataPartnerListOut(BaseModel):
    partners: list[BiDataPartnerOut]
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


class ApiKeyMetaOut(BaseModel):
    id: str
    key_prefix: str
    label: str | None = None
    scopes: list[str]
    created_at: datetime
    revoked_at: datetime | None = None


class ApiKeyListOut(BaseModel):
    keys: list[ApiKeyMetaOut]


class ApiKeyRotateOut(BaseModel):
    api_key: str
    key_prefix: str
    partner_id: str
