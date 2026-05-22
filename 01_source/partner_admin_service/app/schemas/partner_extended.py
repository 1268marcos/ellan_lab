from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class WebhookDeliveryOut(BaseModel):
    id: str
    endpoint_id: str
    event_id: str
    event_type: str
    http_status: Optional[int] = None
    attempt_count: int
    status: str
    last_error: Optional[str] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookDeliveryListOut(BaseModel):
    partner_id: str
    items: list[WebhookDeliveryOut]
    total: int


class IntegrationHealthOut(BaseModel):
    id: int
    partner_id: str
    partner_type: str
    endpoint_url: Optional[str] = None
    checked_at: datetime
    status: str
    latency_ms: Optional[int] = None
    http_status: Optional[int] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class IntegrationHealthListOut(BaseModel):
    partner_id: str
    items: list[IntegrationHealthOut]
    total: int


class OutboxEventOut(BaseModel):
    id: str
    partner_id: str
    order_id: str
    event_type: str
    status: str
    attempt_count: int
    max_attempts: int
    last_error: Optional[str] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OutboxEventListOut(BaseModel):
    partner_id: str
    items: list[OutboxEventOut]
    total: int


class B2bInvoiceOut(BaseModel):
    id: str
    cycle_id: str
    partner_id: str
    invoice_number: Optional[str] = None
    document_type: str
    amount_cents: int
    tax_cents: int
    currency: str
    status: str
    due_date: Optional[date] = None
    taker_name: Optional[str] = None
    issued_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class B2bInvoiceListOut(BaseModel):
    partner_id: str
    items: list[B2bInvoiceOut]
    total: int


class BillingLineItemOut(BaseModel):
    id: int
    cycle_id: str
    partner_id: str
    line_type: str
    description: str
    quantity: float
    unit_price_cents: int
    total_cents: int
    currency: str

    model_config = {"from_attributes": True}


class BillingLineItemListOut(BaseModel):
    partner_id: str
    cycle_id: Optional[str] = None
    items: list[BillingLineItemOut]
    total: int


class CreditNoteOut(BaseModel):
    id: str
    partner_id: str
    reason_code: str
    description: str
    amount_cents: int
    currency: str
    status: str
    approved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CreditNoteListOut(BaseModel):
    partner_id: str
    items: list[CreditNoteOut]
    total: int


class PaymentHoldOut(BaseModel):
    id: str
    partner_id: str
    invoice_id: str
    hold_amount_cents: int
    release_schedule: str
    status: str
    released_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentHoldListOut(BaseModel):
    partner_id: str
    items: list[PaymentHoldOut]
    total: int


class CommissionOut(BaseModel):
    id: str
    partner_id: str
    commission_percentage: Optional[float] = None
    revenue_threshold_cents: Optional[int] = None
    effective_from: Optional[date] = None

    model_config = {"from_attributes": True}


class CommissionListOut(BaseModel):
    partner_id: str
    items: list[CommissionOut]
    total: int


class OnboardingMilestoneOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    milestone_code: str
    milestone_label: str
    status: str
    sort_order: int
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class OnboardingListOut(BaseModel):
    partner_id: str
    items: list[OnboardingMilestoneOut]
    progress_pct: float
    total: int


class OnboardingPatchIn(BaseModel):
    status: str = Field(..., description="PENDING|IN_PROGRESS|DONE|BLOCKED")
    notes: Optional[str] = None
    completed_by: Optional[str] = None


class Partner360Out(BaseModel):
    partner_id: str
    partner_type: str
    settlements_draft: int
    settlements_paid: int
    open_billing_cycles: int
    pending_invoices: int
    pending_outbox: int
    webhook_failures_24h: int
    integration_status: str
    onboarding_progress_pct: float
    sla_active: bool
    ecosystem_links: int = 0
    ecosystem_priority_links: int = 0
