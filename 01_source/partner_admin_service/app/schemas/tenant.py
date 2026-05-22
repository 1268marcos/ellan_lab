from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TenantCreateIn(BaseModel):
    tenant_id: str
    cnpj: str
    razao_social: str
    ie: str | None = None
    regime: str = "SIMPLES"
    crt: str = "1"
    cert_a1_ref: str | None = None
    is_active: bool = True
    brand_config: dict[str, Any] = Field(default_factory=dict)


class TenantUpdateIn(BaseModel):
    cnpj: str | None = None
    razao_social: str | None = None
    ie: str | None = None
    regime: str | None = None
    crt: str | None = None
    cert_a1_ref: str | None = None
    is_active: bool | None = None
    brand_config: dict[str, Any] | None = None


class TenantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    cnpj: str
    razao_social: str
    ie: str | None
    regime: str
    crt: str
    cert_a1_ref: str | None
    is_active: bool
    created_at: datetime
    brand_config: dict[str, Any]


class TenantListOut(BaseModel):
    tenants: list[TenantOut]
    total: int


class CustomDomainCreateIn(BaseModel):
    id: str | None = None
    domain: str
    verified: bool = False
    ssl_cert_ref: str | None = None


class CustomDomainOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    domain: str
    verified: bool | None
    ssl_cert_ref: str | None
    created_at: datetime
    verified_at: datetime | None


class CustomDomainListOut(BaseModel):
    domains: list[CustomDomainOut]
    total: int


class TenantPartnerLinkCreateIn(BaseModel):
    id: str | None = None
    partner_id: str
    partner_type: str
    is_default: bool = False


class TenantPartnerLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    partner_id: str
    partner_type: str
    is_default: bool
    created_at: datetime


class TenantPartnerLinkListOut(BaseModel):
    links: list[TenantPartnerLinkOut]
    total: int
