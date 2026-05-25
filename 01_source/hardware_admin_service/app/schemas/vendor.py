from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HardwareVendorPartnerIn(BaseModel):
    id: str | None = None
    name: str
    code: str
    vendor_type: str
    region_code: str | None = None
    api_base_url: str | None = None
    country: str = "BR"
    active: bool = True


class HardwareVendorPartnerUpdate(BaseModel):
    name: str | None = None
    vendor_type: str | None = None
    region_code: str | None = None
    api_base_url: str | None = None
    country: str | None = None
    active: bool | None = None


class HardwareVendorPartnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    vendor_type: str
    region_code: str | None
    api_base_url: str | None
    country: str
    active: bool
    created_at: datetime
    updated_at: datetime


class HardwareVendorPartnerListOut(BaseModel):
    vendors: list[HardwareVendorPartnerOut]
    total: int


class WebhookConfigureIn(BaseModel):
    url: str
    secret: str | None = None
    events: list[str] | None = None


class WebhookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    vendor_id: str
    url: str
    events_json: str
    api_version: str
    active: bool
    created_at: datetime
    updated_at: datetime


class ApiKeyRotateOut(BaseModel):
    vendor_id: str
    api_key: str
    key_prefix: str
    created_at: datetime


class ApiKeyMetaOut(BaseModel):
    id: str
    key_prefix: str
    label: str | None
    revoked_at: datetime | None
    created_at: datetime


class ApiKeyListOut(BaseModel):
    vendor_id: str
    keys: list[ApiKeyMetaOut]
