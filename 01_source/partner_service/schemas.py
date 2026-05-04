from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PartnerCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    partner_type: str = Field(default="ECOMMERCE", max_length=20)
    legal_name: str | None = Field(default=None, max_length=255)
    contact_email: EmailStr | None = None
    status: str = Field(default="ACTIVE", max_length=32)


class PartnerUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    contact_email: EmailStr | None = None
    status: str | None = Field(default=None, max_length=32)


class PartnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    partner_type: str
    name: str
    legal_name: str | None
    status: str
    contact_email: str | None
    webhook_url: str | None
    webhook_events_json: str
    webhook_api_version: str
    created_at: datetime
    updated_at: datetime


class PartnerWebhookPatchIn(BaseModel):
    webhook_url: str | None = Field(default=None, max_length=500)
    webhook_secret: str | None = Field(default=None, min_length=8, max_length=256)
    webhook_events_json: str | None = None
    webhook_api_version: str | None = Field(default=None, max_length=10)


class PartnerApiKeyRotateIn(BaseModel):
    label: str | None = Field(default=None, max_length=64)


class PartnerApiKeyRotateOut(BaseModel):
    id: str
    key_prefix: str
    api_key: str
    partner_id: str
