from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IssuerIn(BaseModel):
    id: str | None = None
    name: str
    code: str
    issuer_type: str = "SEFAZ"
    country: str = "BR"
    region_code: str | None = None
    api_base_url: str | None = None
    credentials_secret_ref: str | None = None
    webhook_secret_ref: str | None = None
    active: bool = True


class IssuerUpdate(BaseModel):
    name: str | None = None
    issuer_type: str | None = None
    country: str | None = None
    region_code: str | None = None
    api_base_url: str | None = None
    credentials_secret_ref: str | None = None
    webhook_secret_ref: str | None = None
    active: bool | None = None


class IssuerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    issuer_type: str
    country: str
    region_code: str | None
    api_base_url: str | None
    active: bool
    created_at: datetime
    updated_at: datetime


class IssuerListOut(BaseModel):
    issuers: list[IssuerOut]
    total: int


class WebhookConfigureIn(BaseModel):
    url: str
    secret: str | None = None
    events: list[str] | None = None


class WebhookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    issuer_id: str
    url: str
    events_json: str
    active: bool
    updated_at: datetime


class ApiKeyRotateOut(BaseModel):
    issuer_id: str
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
    issuer_id: str
    keys: list[ApiKeyMetaOut]


class FiscalDocumentIn(BaseModel):
    id: str | None = None
    order_id: str
    receipt_code: str
    document_type: str = "NFC_E_65"
    channel: str | None = None
    region: str | None = "BR"
    amount_cents: int
    currency: str = "BRL"
    delivery_mode: str | None = None
    send_status: str | None = None
    payload_json: str = "{}"
    tenant_id: str | None = None


class FiscalDocumentUpdate(BaseModel):
    send_status: str | None = None
    print_status: str | None = None
    send_target: str | None = None


class FiscalDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    receipt_code: str
    document_type: str
    channel: str | None
    region: str | None
    amount_cents: int
    currency: str
    send_status: str | None
    issued_at: datetime
    tenant_id: str | None
    attempt: int


class FiscalDocumentListOut(BaseModel):
    items: list[FiscalDocumentOut]
    total: int


class GapIn(BaseModel):
    id: str | None = None
    dedupe_key: str
    gap_type: str
    severity: str = "MEDIUM"
    status: str = "OPEN"
    order_id: str | None = None
    invoice_id: str | None = None
    details_json: dict[str, Any] | None = None


class GapUpdate(BaseModel):
    status: str | None = None
    severity: str | None = None


class GapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    dedupe_key: str
    gap_type: str
    severity: str
    status: str
    order_id: str | None
    invoice_id: str | None
    first_detected_at: datetime
    last_detected_at: datetime
    resolved_at: datetime | None


class GapListOut(BaseModel):
    items: list[GapOut]
    total: int


class UnifiedGapOut(BaseModel):
    id: str
    source: str
    dedupe_key: str | None = None
    gap_type: str
    severity: str
    status: str
    order_id: str | None = None
    invoice_id: str | None = None
    details: dict[str, Any] | None = None
    first_detected_at: str | None = None
    last_detected_at: str | None = None
    resolved_at: str | None = None


class GapWorkbenchSummary(BaseModel):
    admin_count: int
    billing_count: int
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_gap_type: dict[str, int] = Field(default_factory=dict)


class GapWorkbenchOut(BaseModel):
    items: list[UnifiedGapOut]
    total: int
    summary: GapWorkbenchSummary
    billing_available: bool
    billing_error: str | None = None
    billing_scan: dict[str, Any] | None = None
    snapshot: dict[str, Any] | None = None


class ProviderHealthIn(BaseModel):
    country: str
    provider_name: str
    mode: str = "STUB"
    enabled: bool = True
    base_url: str | None = None
    last_status: str = "UNKNOWN"


class ProviderHealthOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    country: str
    provider_name: str
    mode: str
    enabled: bool
    last_status: str
    last_http_status: int | None
    last_latency_ms: int | None
    checked_at: datetime


class ProviderHealthListOut(BaseModel):
    items: list[ProviderHealthOut]
    total: int


class TenantFiscalIn(BaseModel):
    tenant_id: str
    cnpj: str
    razao_social: str
    ie: str | None = None
    regime: str = "SIMPLES"
    crt: str = "1"
    cert_a1_ref: str | None = None
    is_active: bool = True


class TenantFiscalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tenant_id: str
    cnpj: str
    razao_social: str
    regime: str
    crt: str
    is_active: bool


class TenantFiscalListOut(BaseModel):
    items: list[TenantFiscalOut]
    total: int


class ProductFiscalIn(BaseModel):
    sku_id: str
    ncm_code: str | None = None
    icms_cst: str | None = None
    pis_cst: str | None = None
    cofins_cst: str | None = None
    cfop: str | None = None
    is_active: bool = True


class ProductFiscalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sku_id: str
    ncm_code: str | None
    icms_cst: str | None
    cfop: str | None
    is_active: bool


class ProductFiscalListOut(BaseModel):
    items: list[ProductFiscalOut]
    total: int


class ApprovalIn(BaseModel):
    id: str | None = None
    owner: str
    status: str = "PENDING"
    eta: datetime | None = None
    payload_json: dict[str, Any] = Field(default_factory=dict)


class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner: str
    status: str
    eta: datetime | None
    created_at: datetime


class ApprovalListOut(BaseModel):
    items: list[ApprovalOut]
    total: int


class CallbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_id: str
    authority: str
    event_type: str | None
    status: str | None
    received_at: datetime


class CallbackListOut(BaseModel):
    items: list[CallbackOut]
    total: int
