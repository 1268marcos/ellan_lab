from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IntegrationPartnerIn(BaseModel):
    id: str | None = None
    name: str
    code: str
    partner_type: str
    region_code: str | None = None
    api_base_url: str | None = None
    default_currency: str = "BRL"
    country: str = "BR"
    active: bool = True


class IntegrationPartnerUpdate(BaseModel):
    name: str | None = None
    partner_type: str | None = None
    region_code: str | None = None
    api_base_url: str | None = None
    default_currency: str | None = None
    country: str | None = None
    active: bool | None = None


class IntegrationPartnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    partner_type: str
    region_code: str | None
    api_base_url: str | None
    default_currency: str
    country: str
    active: bool
    created_at: datetime
    updated_at: datetime


class IntegrationPartnerListOut(BaseModel):
    partners: list[IntegrationPartnerOut]
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
    configured: bool = True


class ApiKeyRotateOut(BaseModel):
    api_key: str
    key_prefix: str
    partner_id: str


class ApiKeyMetaOut(BaseModel):
    id: str
    key_prefix: str
    label: str | None
    created_at: datetime
    revoked_at: datetime | None


class ApiKeyListOut(BaseModel):
    keys: list[ApiKeyMetaOut]
