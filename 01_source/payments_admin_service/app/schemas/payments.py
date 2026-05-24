from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- payment_transactions ---


class PaymentTransactionIn(BaseModel):
    id: str | None = None
    order_id: str
    gateway: str
    gateway_transaction_id: str | None = None
    amount_cents: int
    currency: str = "BRL"
    payment_method: str
    status: str = "INITIATED"
    reconciliation_status: str = "PENDING"
    reconciliation_batch_id: str | None = None


class PaymentTransactionUpdate(BaseModel):
    status: str | None = None
    reconciliation_status: str | None = None
    reconciliation_batch_id: str | None = None
    gateway_transaction_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class PaymentTransactionOut(_Orm):
    id: str
    order_id: str
    gateway: str
    gateway_transaction_id: str | None
    amount_cents: int
    currency: str
    payment_method: str
    status: str
    reconciliation_status: str
    reconciliation_batch_id: str | None
    gateway_fee_cents: int
    net_amount_cents: int | None
    created_at: datetime


class PaymentTransactionListOut(BaseModel):
    items: list[PaymentTransactionOut]
    total: int


# --- payment_instructions ---


class PaymentInstructionIn(BaseModel):
    id: str | None = None
    order_id: str
    instruction_type: str
    amount_cents: int
    currency: str = "BRL"
    status: str = "PENDING"
    provider_name: str | None = None


class PaymentInstructionUpdate(BaseModel):
    status: str | None = None
    provider_payment_id: str | None = None
    qr_code_text: str | None = None


class PaymentInstructionOut(_Orm):
    id: str
    order_id: str
    instruction_type: str
    amount_cents: int
    currency: str
    status: str
    provider_name: str | None
    created_at: datetime


class PaymentInstructionListOut(BaseModel):
    items: list[PaymentInstructionOut]
    total: int


# --- payment_splits ---


class PaymentSplitIn(BaseModel):
    id: str | None = None
    order_id: str
    recipient_type: str
    recipient_id: str
    amount_cents: int
    percentage: Decimal | None = None
    status: str = "PENDING"


class PaymentSplitUpdate(BaseModel):
    status: str | None = None


class PaymentSplitOut(_Orm):
    id: str
    order_id: str
    recipient_type: str
    recipient_id: str
    amount_cents: int
    percentage: Decimal | None
    status: str
    created_at: datetime


class PaymentSplitListOut(BaseModel):
    items: list[PaymentSplitOut]
    total: int


# --- payments ---


class PaymentIn(BaseModel):
    id: str | None = None
    order_id: str
    provider: str
    method: str
    status: str
    amount_cents: int
    currency: str = "EUR"
    provider_payment_id: str | None = None
    idempotency_key: str | None = None
    raw_json: dict[str, Any] = Field(default_factory=dict)


class PaymentUpdate(BaseModel):
    status: str | None = None
    provider_payment_id: str | None = None
    confirmed_at: int | None = None


class PaymentOut(_Orm):
    id: str
    order_id: str
    provider: str
    method: str
    status: str
    amount_cents: int
    currency: str
    created_at: int
    confirmed_at: int | None


class PaymentListOut(BaseModel):
    items: list[PaymentOut]
    total: int


# --- webhook_endpoints ---


class WebhookEndpointIn(BaseModel):
    id: str | None = None
    partner_type: str
    partner_id: str
    url: str
    events: str = '["payment.*"]'
    signing_algo: str = "HMAC_SHA256"
    active: bool = True


class WebhookEndpointUpdate(BaseModel):
    url: str | None = None
    events: str | None = None
    active: bool | None = None


class WebhookEndpointOut(_Orm):
    id: str
    partner_type: str
    partner_id: str
    url: str
    events: str
    secret_ref: str | None
    signing_algo: str
    active: bool
    created_at: datetime


class WebhookEndpointListOut(BaseModel):
    items: list[WebhookEndpointOut]
    total: int


class WebhookSecretRotateOut(BaseModel):
    endpoint_id: str
    secret: str
    secret_ref: str


# --- gateway_events ---


class GatewayEventIn(BaseModel):
    id: str | None = None
    gateway_id: str
    region: str
    locker_id: str
    event_type: str
    created_at: int | None = None
    order_id: str | None = None
    request_id: str | None = None
    porta: int | None = None
    payload_json: dict[str, Any] = Field(default_factory=dict)


class GatewayEventOut(_Orm):
    id: str
    gateway_id: str
    region: str
    locker_id: str
    event_type: str
    created_at: int
    order_id: str | None
    request_id: str | None


class GatewayEventListOut(BaseModel):
    items: list[GatewayEventOut]
    total: int
