from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PaymentTermsIn(BaseModel):
    partner_id: str
    net_days: int = 30
    grace_days: int = 0
    early_payment_discount_pct: Decimal | None = None
    currency: str = "BRL"
    is_default: bool = True


class PaymentTermsOut(PaymentTermsIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class PaymentTermsListOut(BaseModel):
    items: list[PaymentTermsOut]
    total: int


class FxRateIn(BaseModel):
    base_currency: str
    quote_currency: str
    rate_date: date
    rate: Decimal
    source: str = "MANUAL"


class FxRateOut(FxRateIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class FxRateListOut(BaseModel):
    items: list[FxRateOut]
    total: int


class FxConvertOut(BaseModel):
    amount_cents: int
    from_currency: str
    to_currency: str
    converted_cents: int
    rate: Decimal
    rate_date: date


class CommercialTierIn(BaseModel):
    tier_code: str
    name: str
    min_monthly_orders: int = 0
    min_gmv_cents: int = 0
    default_revenue_share_pct: Decimal | None = None
    sort_order: int = 100


class CommercialTierOut(CommercialTierIn):
    model_config = ConfigDict(from_attributes=True)


class CommercialTierListOut(BaseModel):
    items: list[CommercialTierOut]
    total: int


class TierAssignmentIn(BaseModel):
    partner_id: str
    tier_code: str
    effective_from: date
    effective_until: date | None = None
    assigned_by: str = "finance-ops"


class TierAssignmentOut(TierAssignmentIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class TierAssignmentListOut(BaseModel):
    items: list[TierAssignmentOut]
    total: int


class DunningPolicyIn(BaseModel):
    partner_id: str | None = None
    stage: int
    days_overdue: int
    action: str
    notify_channel: str = "EMAIL"
    active: bool = True


class DunningPolicyOut(DunningPolicyIn):
    model_config = ConfigDict(from_attributes=True)
    id: str


class DunningPolicyListOut(BaseModel):
    items: list[DunningPolicyOut]
    total: int


class DunningCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    invoice_id: str
    partner_id: str
    stage: int
    amount_due_cents: int
    status: str
    next_action_at: datetime | None
    created_at: datetime


class DunningCaseListOut(BaseModel):
    items: list[DunningCaseOut]
    total: int


class DunningScanOut(BaseModel):
    cases_opened: int
    invoices_scanned: int


class TaxCorridorIn(BaseModel):
    partner_id: str
    origin_country: str
    destination_country: str
    document_type: str = "NF_B2B"
    tax_regime: str
    withholding_pct: Decimal = Decimal("0")
    active: bool = True


class TaxCorridorOut(TaxCorridorIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class TaxCorridorListOut(BaseModel):
    items: list[TaxCorridorOut]
    total: int


class InvoiceDocumentIn(BaseModel):
    invoice_id: str
    document_kind: str
    storage_uri: str | None = None
    access_key: str | None = None
    fiscal_invoice_id: str | None = None
    country: str
    invoice_type: str = "B2B"
    issued_at: datetime | None = None


class InvoiceDocumentOut(InvoiceDocumentIn):
    model_config = ConfigDict(from_attributes=True)
    id: str
    created_at: datetime


class InvoiceDocumentListOut(BaseModel):
    items: list[InvoiceDocumentOut]
    total: int


class ReconciliationRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    batch_id: str
    run_at: datetime
    status: str
    matched_count: int
    unmatched_count: int
    variance_cents: int


class ReconciliationMatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    run_id: str
    order_id: str
    match_status: str
    variance_cents: int


class ReconciliationResultOut(BaseModel):
    run: ReconciliationRunOut
    matches: list[ReconciliationMatchOut] = Field(default_factory=list)


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    before_json: str
    after_json: str
    created_at: datetime


class AuditLogListOut(BaseModel):
    items: list[AuditLogOut]
    total: int
