from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class LineItemIn(BaseModel):
    cycle_id: str
    partner_id: str
    locker_id: str | None = None
    line_type: str = "DELIVERY_FEE"
    description: str
    quantity: Decimal = Decimal("1")
    unit_price_cents: int
    total_cents: int | None = None
    currency: str = "BRL"


class LineItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cycle_id: str
    partner_id: str
    locker_id: str | None
    line_type: str
    description: str
    quantity: Decimal
    unit_price_cents: int
    total_cents: int
    currency: str
    created_at: datetime


class LineItemListOut(BaseModel):
    items: list[LineItemOut]
    total: int


class SettlementBatchIn(BaseModel):
    partner_id: str
    partner_type: str = "ECOMMERCE"
    period_start: date
    period_end: date
    currency: str = "BRL"
    total_orders: int = 0
    gross_revenue_cents: int = 0
    revenue_share_pct: Decimal
    revenue_share_cents: int = 0
    fees_cents: int = 0
    net_amount_cents: int | None = None
    status: str = "DRAFT"
    notes: str | None = None


class SettlementBatchUpdate(BaseModel):
    status: str | None = None
    settlement_ref: str | None = None
    settled_at: datetime | None = None
    notes: str | None = None


class SettlementBatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    partner_id: str
    partner_type: str
    period_start: date
    period_end: date
    currency: str
    total_orders: int
    gross_revenue_cents: int
    revenue_share_pct: Decimal
    revenue_share_cents: int
    fees_cents: int
    net_amount_cents: int
    status: str
    settlement_ref: str | None
    settled_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SettlementBatchListOut(BaseModel):
    items: list[SettlementBatchOut]
    total: int


class SettlementItemIn(BaseModel):
    batch_id: str
    order_id: str
    order_date: datetime
    gross_cents: int
    share_pct: Decimal
    share_cents: int | None = None
    currency: str = "BRL"


class SettlementItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: str
    order_id: str
    order_date: datetime
    gross_cents: int
    share_pct: Decimal
    share_cents: int
    currency: str


class SettlementItemListOut(BaseModel):
    items: list[SettlementItemOut]
    total: int


class CreditNoteIn(BaseModel):
    partner_id: str
    reason_code: str = "SLA_BREACH"
    description: str
    amount_cents: int
    original_invoice_id: str | None = None
    cycle_id: str | None = None
    currency: str = "BRL"


class CreditNoteUpdate(BaseModel):
    status: str | None = None


class CreditNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    partner_id: str
    reason_code: str
    description: str
    amount_cents: int
    currency: str
    status: str
    original_invoice_id: str | None
    cycle_id: str | None
    created_at: datetime
    updated_at: datetime


class CreditNoteListOut(BaseModel):
    items: list[CreditNoteOut]
    total: int


class PaymentHoldIn(BaseModel):
    partner_id: str
    invoice_id: str
    hold_amount_cents: int
    release_schedule: str = "AFTER_15_DAYS"


class PaymentHoldUpdate(BaseModel):
    status: str | None = None
    released_at: datetime | None = None


class PaymentHoldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    partner_id: str
    invoice_id: str
    hold_amount_cents: int
    release_schedule: str
    status: str
    released_at: datetime | None
    created_at: datetime


class PaymentHoldListOut(BaseModel):
    items: list[PaymentHoldOut]
    total: int


class CommissionIn(BaseModel):
    partner_id: str
    commission_percentage: Decimal
    revenue_threshold_cents: int | None = None
    effective_from: date
    effective_until: date | None = None


class CommissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    partner_id: str
    commission_percentage: Decimal
    revenue_threshold_cents: int | None
    effective_from: date
    effective_until: date | None
    created_at: datetime


class CommissionListOut(BaseModel):
    items: list[CommissionOut]
    total: int


class CostCenterIn(BaseModel):
    locker_id: str
    region_code: str | None = None
    network_code: str | None = None
    operational_cost_monthly_cents: int = 0


class CostCenterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    locker_id: str
    region_code: str | None
    network_code: str | None
    operational_cost_monthly_cents: int
    created_at: datetime
    updated_at: datetime


class CostCenterListOut(BaseModel):
    items: list[CostCenterOut]
    total: int


class CostCenterMonthlyIn(BaseModel):
    locker_id: str
    month: date
    rent_cents: int = 0
    maintenance_preventive_cents: int = 0
    maintenance_corrective_cents: int = 0
    connectivity_cents: int = 0
    energy_cents: int = 0
    insurance_cents: int = 0
    payment_gateway_fee_cents: int = 0
    depreciation_cents: int = 0
    cleaning_cents: int = 0
    security_cents: int = 0
    marketing_cents: int = 0
    other_cents: int = 0
    notes: str | None = None


class CostCenterMonthlyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    locker_id: str
    month: date
    rent_cents: int
    maintenance_preventive_cents: int
    maintenance_corrective_cents: int
    connectivity_cents: int
    energy_cents: int
    insurance_cents: int
    payment_gateway_fee_cents: int
    depreciation_cents: int
    cleaning_cents: int
    security_cents: int
    marketing_cents: int
    other_cents: int
    notes: str | None
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_opex_cents(self) -> int:
        return (
            self.rent_cents
            + self.maintenance_preventive_cents
            + self.maintenance_corrective_cents
            + self.connectivity_cents
            + self.energy_cents
            + self.insurance_cents
            + self.payment_gateway_fee_cents
            + self.cleaning_cents
            + self.security_cents
            + self.marketing_cents
            + self.other_cents
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_costs_cents(self) -> int:
        return self.total_opex_cents + self.depreciation_cents


class CostCenterMonthlyListOut(BaseModel):
    items: list[CostCenterMonthlyOut]
    total: int


class FiscalGapIn(BaseModel):
    dedupe_key: str
    gap_type: str
    severity: str = "MEDIUM"
    status: str = "OPEN"
    order_id: str | None = None
    invoice_id: str | None = None
    details_json: str = "{}"


class FiscalGapUpdate(BaseModel):
    status: str | None = None
    resolved_at: datetime | None = None


class FiscalGapOut(BaseModel):
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


class FiscalGapListOut(BaseModel):
    items: list[FiscalGapOut]
    total: int


class WebhookDeliveryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    endpoint_id: str
    event_id: str
    event_type: str
    http_status: int | None
    attempt_count: int
    status: str
    last_error: str | None
    delivered_at: datetime | None
    created_at: datetime


class WebhookDeliveryListOut(BaseModel):
    items: list[WebhookDeliveryOut]
    total: int
