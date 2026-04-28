from __future__ import annotations

from pydantic import BaseModel, Field


class PartnerBillingCycleOut(BaseModel):
    id: str
    partner_id: str
    status: str
    currency: str
    country_code: str | None = None
    jurisdiction_code: str | None = None
    period_timezone: str
    period_start: str
    period_end: str
    total_amount_cents: int
    dedupe_key: str | None = None
    computed_at: str | None = None


class PartnerBillingLineItemOut(BaseModel):
    id: int
    cycle_id: str
    partner_id: str
    line_type: str
    description: str
    quantity: str
    unit_price_cents: int
    total_cents: int
    currency: str
    country_code: str | None = None
    jurisdiction_code: str | None = None
    dedupe_key: str | None = None
    created_at: str


class PartnerB2BInvoiceOut(BaseModel):
    id: str
    cycle_id: str
    partner_id: str
    status: str
    document_type: str
    amount_cents: int
    tax_cents: int
    currency: str
    country_code: str | None = None
    jurisdiction_code: str | None = None
    timezone: str
    due_date: str | None = None
    dedupe_key: str | None = None
    created_at: str


class PartnerCreditNoteOut(BaseModel):
    id: str
    partner_id: str
    original_invoice_id: str | None = None
    cycle_id: str | None = None
    reason_code: str
    amount_cents: int
    currency: str
    country_code: str | None = None
    jurisdiction_code: str | None = None
    timezone: str
    status: str
    dispute_ref: str | None = None
    dedupe_key: str | None = None
    created_at: str


class PartnerDisputeHistoryOut(BaseModel):
    cycle_id: str
    partner_id: str
    dispute_scope: str
    dispute_reason: str
    status: str
    country_code: str | None = None
    jurisdiction_code: str | None = None
    opened_at: str
    metadata: dict | None = None


class PartnerBillingDisputeIn(BaseModel):
    reason: str = Field(..., min_length=3, max_length=2000)
