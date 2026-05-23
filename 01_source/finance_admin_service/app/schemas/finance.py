from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PartnerAccountIn(BaseModel):
    id: str | None = None
    code: str
    name: str
    partner_type: str = "ECOMMERCE"
    country_code: str | None = None
    tax_id: str | None = None
    currency: str = "BRL"
    active: bool = True


class PartnerAccountUpdate(BaseModel):
    name: str | None = None
    partner_type: str | None = None
    country_code: str | None = None
    tax_id: str | None = None
    currency: str | None = None
    active: bool | None = None


class PartnerAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    partner_type: str
    country_code: str | None
    tax_id: str | None
    currency: str
    active: bool
    created_at: datetime
    updated_at: datetime


class PartnerListOut(BaseModel):
    items: list[PartnerAccountOut]
    total: int


class BillingPlanIn(BaseModel):
    partner_id: str
    partner_type: str = "ECOMMERCE"
    plan_name: str
    billing_model: str = "HYBRID"
    currency: str = "BRL"
    country_code: str | None = None
    monthly_fee_cents: int | None = None
    fee_per_delivery_cents: int | None = None
    fee_per_pickup_cents: int | None = None
    fee_per_day_stored_cents: int | None = None
    revenue_share_pct: Decimal | None = None
    valid_from: date
    valid_until: date | None = None
    is_active: bool = True


class BillingPlanUpdate(BaseModel):
    plan_name: str | None = None
    billing_model: str | None = None
    monthly_fee_cents: int | None = None
    fee_per_delivery_cents: int | None = None
    is_active: bool | None = None
    valid_until: date | None = None


class BillingPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    partner_id: str
    partner_type: str
    plan_name: str
    billing_model: str
    currency: str
    country_code: str | None
    monthly_fee_cents: int | None
    fee_per_delivery_cents: int | None
    fee_per_pickup_cents: int | None
    fee_per_day_stored_cents: int | None
    revenue_share_pct: Decimal | None
    valid_from: date
    valid_until: date | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class BillingPlanListOut(BaseModel):
    items: list[BillingPlanOut]
    total: int


class BillingCycleIn(BaseModel):
    partner_id: str
    partner_type: str = "ECOMMERCE"
    billing_plan_id: str
    locker_id: str | None = None
    currency: str = "BRL"
    period_start: date
    period_end: date
    total_amount_cents: int = 0
    status: str = "OPEN"
    notes: str | None = None


class BillingCycleUpdate(BaseModel):
    status: str | None = None
    total_amount_cents: int | None = None
    notes: str | None = None


class BillingCycleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    partner_id: str
    locker_id: str | None
    partner_type: str
    billing_plan_id: str
    currency: str
    period_start: date
    period_end: date
    total_amount_cents: int
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class BillingCycleListOut(BaseModel):
    items: list[BillingCycleOut]
    total: int


class B2bInvoiceIn(BaseModel):
    cycle_id: str
    partner_id: str
    invoice_number: str | None = None
    document_type: str = "INVOICE"
    amount_cents: int
    tax_cents: int = 0
    currency: str = "BRL"
    status: str = "DRAFT"
    due_date: date | None = None


class B2bInvoiceUpdate(BaseModel):
    status: str | None = None
    invoice_number: str | None = None
    due_date: date | None = None
    issued_at: datetime | None = None
    paid_at: datetime | None = None


class B2bInvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cycle_id: str
    partner_id: str
    invoice_number: str | None
    document_type: str
    amount_cents: int
    tax_cents: int
    currency: str
    status: str
    due_date: date | None
    issued_at: datetime | None
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime


class B2bInvoiceListOut(BaseModel):
    items: list[B2bInvoiceOut]
    total: int


class WebhookConfigureIn(BaseModel):
    url: str
    secret: str | None = None
    events: list[str] | None = None


class WebhookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    partner_id: str
    url: str
    events_json: str
    active: bool
    api_version: str
    updated_at: datetime


class ApiKeyRotateOut(BaseModel):
    api_key: str
    key_prefix: str
    partner_id: str


class ApiKeyMetaOut(BaseModel):
    id: str
    key_prefix: str
    label: str | None
    revoked_at: datetime | None
    created_at: datetime


class ApiKeyListOut(BaseModel):
    items: list[ApiKeyMetaOut]


class WalletProviderIn(BaseModel):
    code: str
    name: str
    is_active: bool = True


class WalletProviderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class WalletProviderListOut(BaseModel):
    items: list[WalletProviderOut]
    total: int


class WalletTransactionIn(BaseModel):
    wallet_id: str
    order_id: str | None = None
    type: str
    amount_cents: int
    balance_after_cents: int
    status: str = "PENDING"
    external_reference: str | None = None
    description: str | None = None


class WalletTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    wallet_id: str
    order_id: str | None
    type: str
    amount_cents: int
    balance_after_cents: int
    status: str
    external_reference: str | None
    description: str | None
    created_at: datetime


class WalletTransactionListOut(BaseModel):
    items: list[WalletTransactionOut]
    total: int


class OpsInvoiceIn(BaseModel):
    id: str | None = None
    order_id: str
    country: str
    invoice_type: str = "NFC_E"
    status: str = "PENDING"
    amount_cents: int | None = None
    currency: str | None = "BRL"
    locker_id: str | None = None


class OpsInvoiceUpdate(BaseModel):
    status: str | None = None
    error_message: str | None = None
    amount_cents: int | None = None


class OpsInvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    country: str
    invoice_type: str
    status: str
    amount_cents: int | None
    currency: str | None
    locker_id: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class OpsInvoiceListOut(BaseModel):
    items: list[OpsInvoiceOut]
    total: int


class BillingEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_id: str
    order_id: str | None
    event_type: str
    processed_at: datetime


class BillingEventListOut(BaseModel):
    items: list[BillingEventOut]
    total: int
