from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class SettlementBatchOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    period_start: date
    period_end: date
    currency: str
    total_orders: int
    gross_revenue_cents: int
    revenue_share_pct: float
    revenue_share_cents: int
    fees_cents: int
    net_amount_cents: int
    status: str
    settled_at: Optional[datetime] = None
    settlement_ref: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SettlementBatchListOut(BaseModel):
    partner_id: str
    items: list[SettlementBatchOut]
    total: int


class SettlementGenerateIn(BaseModel):
    period_start: date
    period_end: date
    revenue_share_pct: float = Field(ge=0, le=1)
    fees_cents: int = 0
    currency: str = "BRL"
    notes: Optional[str] = None
    partner_type: str = "ECOMMERCE"
    total_orders: int = 0
    gross_revenue_cents: int = 0


class SettlementApproveIn(BaseModel):
    settlement_ref: Optional[str] = None
    notes: Optional[str] = None


class SettlementItemOut(BaseModel):
    id: int
    batch_id: str
    order_id: str
    order_date: datetime
    gross_cents: int
    share_pct: float
    share_cents: int
    currency: str

    model_config = {"from_attributes": True}


class SettlementItemListOut(BaseModel):
    batch_id: str
    partner_id: str
    items: list[SettlementItemOut]
    total: int


class ServiceAreaCreateIn(BaseModel):
    locker_id: str
    priority: int = 100
    exclusive: bool = False
    valid_from: date
    valid_until: Optional[date] = None
    is_active: bool = True
    partner_type: str = "ECOMMERCE"


class ServiceAreaOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    locker_id: str
    priority: int
    exclusive: bool
    valid_from: date
    valid_until: Optional[date] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ServiceAreaListOut(BaseModel):
    partner_id: str
    items: list[ServiceAreaOut]
    total: int


class PerformanceMetricOut(BaseModel):
    id: str
    partner_id: str
    period_month: str
    total_orders: int
    on_time_pickup_pct: Optional[float] = None
    return_rate_pct: Optional[float] = None
    avg_pickup_hours: Optional[float] = None
    sla_compliance_pct: Optional[float] = None
    webhook_success_rate: Optional[float] = None
    generated_at: datetime

    model_config = {"from_attributes": True}


class PerformanceListOut(BaseModel):
    partner_id: str
    items: list[PerformanceMetricOut]
    total: int


class BillingPlanOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    plan_name: str
    billing_model: str
    currency: str
    monthly_fee_cents: Optional[int] = None
    is_active: bool
    valid_from: date
    valid_until: Optional[date] = None

    model_config = {"from_attributes": True}


class BillingPlanListOut(BaseModel):
    partner_id: str
    items: list[BillingPlanOut]
    total: int


class BillingCycleOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    billing_plan_id: str
    period_start: date
    period_end: date
    total_amount_cents: int
    status: str
    currency: str

    model_config = {"from_attributes": True}


class BillingCycleListOut(BaseModel):
    partner_id: str
    items: list[BillingCycleOut]
    total: int


class PartnerStoreCreateIn(BaseModel):
    id: Optional[str] = None
    name: str
    address_line: str
    city: str
    state: str
    postal_code: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    commission_pct: Optional[float] = 5.0
    active: bool = True


class PartnerStoreOut(BaseModel):
    id: str
    name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    address_line: str
    city: str
    state: str
    postal_code: str
    phone: Optional[str] = None
    email: Optional[str] = None
    commission_pct: Optional[float] = None
    active: Optional[bool] = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PartnerStoreListOut(BaseModel):
    items: list[PartnerStoreOut]
    total: int


class SlaAgreementCreateIn(BaseModel):
    country: str = "BR"
    sla_pickup_hours: int = 72
    sla_return_hours: int = 24
    penalty_pct: float = 0
    valid_from: date
    valid_until: Optional[date] = None
    partner_type: str = "ECOMMERCE"


class SlaAgreementOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    country: str
    sla_pickup_hours: int
    sla_return_hours: int
    penalty_pct: Optional[float] = None
    valid_from: date
    valid_until: Optional[date] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SlaAgreementListOut(BaseModel):
    partner_id: str
    items: list[SlaAgreementOut]
    total: int


class StatusHistoryOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    from_status: Optional[str] = None
    to_status: str
    reason: Optional[str] = None
    changed_by: Optional[str] = None
    changed_at: datetime

    model_config = {"from_attributes": True}


class StatusHistoryListOut(BaseModel):
    partner_id: str
    items: list[StatusHistoryOut]
    total: int


class PartnerDashboardOut(BaseModel):
    from_: Optional[datetime] = Field(None, alias="from")
    to: Optional[datetime] = None
    partner_id: Optional[str] = None
    kpis: dict
    compare: dict
    changes_series: list[dict] = []

    model_config = {"populate_by_name": True}
