from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaymentProviderPartnerIn(BaseModel):
    id: str | None = None
    name: str
    code: str
    provider_type: str = Field(description="STRIPE | MERCADOPAGO | OTHER")
    region_code: str | None = None
    api_base_url: str | None = None
    credentials_secret_ref: str | None = None
    webhook_secret_ref: str | None = None
    currency: str = "BRL"
    country: str = "BR"
    active: bool = True


class PaymentProviderPartnerUpdate(BaseModel):
    name: str | None = None
    provider_type: str | None = None
    region_code: str | None = None
    api_base_url: str | None = None
    credentials_secret_ref: str | None = None
    webhook_secret_ref: str | None = None
    currency: str | None = None
    country: str | None = None
    active: bool | None = None


class PaymentProviderPartnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    provider_type: str
    region_code: str | None
    api_base_url: str | None
    credentials_secret_ref: str | None
    webhook_secret_ref: str | None
    currency: str
    country: str
    active: bool
    created_at: datetime
    updated_at: datetime


class PaymentProviderPartnerListOut(BaseModel):
    partners: list[PaymentProviderPartnerOut]
    total: int


class WebhookConfigureIn(BaseModel):
    url: str
    secret: str | None = None
    events: list[str] | None = None


class WebhookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_id: str
    url: str
    events_json: str
    active: bool
    created_at: datetime
    updated_at: datetime


class ApiKeyRotateOut(BaseModel):
    provider_id: str
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
    provider_id: str
    keys: list[ApiKeyMetaOut]
