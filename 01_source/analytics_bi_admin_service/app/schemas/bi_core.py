from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AnalyticsFactIn(BaseModel):
    fact_key: str
    fact_name: str
    order_id: str
    order_channel: str | None = None
    region_code: str | None = None
    slot_id: str | None = None
    payload: dict[str, Any]
    occurred_at: datetime


class AnalyticsFactOut(BaseModel):
    id: UUID
    fact_key: str
    fact_name: str
    order_id: str
    order_channel: str | None = None
    region_code: str | None = None
    slot_id: str | None = None
    payload: dict[str, Any] | str
    occurred_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalyticsFactListOut(BaseModel):
    items: list[AnalyticsFactOut]
    total: int


class BiKpiDefinitionIn(BaseModel):
    code: str
    name: str
    domain: str = "LOCKER"
    grain: str = "DAILY"
    source_table: str
    formula_hint: str | None = None
    owner_team: str = "data-platform"


class BiKpiDefinitionOut(BiKpiDefinitionIn):
    id: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BiKpiDefinitionListOut(BaseModel):
    items: list[BiKpiDefinitionOut]
    total: int


class BiReportCatalogIn(BaseModel):
    code: str
    name: str
    report_type: str = "DASHBOARD"
    metabase_dashboard_id: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=lambda: ["ops", "locker"])


class BiReportCatalogOut(BaseModel):
    id: str
    code: str
    name: str
    report_type: str
    metabase_dashboard_id: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BiReportCatalogListOut(BaseModel):
    items: list[BiReportCatalogOut]
    total: int


class BiDashboardOut(BaseModel):
    facts_count: int
    facts_24h: int
    partners: int
    kpi_definitions: int
    report_catalog: int
    network_players: int
    player_relations: int
    mrr_rows: int
    locker_pnl_rows: int
    partner_revenue_rows: int
    capability_webhooks: int
    open_marts_months: int
    readiness_rows: int = 0
    readiness_go_live: int = 0
    readiness_avg_score: float = 0
    open_kpi_alerts: int = 0
    mart_jobs_pending: int = 0
    lineage_edges: int = 0
    market_presence_rows: int = 0
    export_jobs_24h: int = 0


class CompanyMrrTrendOut(BaseModel):
    month_ref: date
    currency: str
    mrr_cents: float | None = None
    company_deferred_cents: float | None = None
    active_partner_count: int | None = None
    active_locker_count: int | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class LockerPnlOut(BaseModel):
    month_ref: date
    partner_id: str
    locker_id: str
    currency: str
    country_code: str | None = None
    revenue_cents: int | None = None
    gross_profit_cents: int | None = None
    gross_margin_pct: float | None = None
    net_income_cents: int | None = None

    model_config = {"from_attributes": True}


class PartnerRevenueMonthlyOut(BaseModel):
    month_ref: date
    partner_id: str
    locker_id: str
    currency: str
    revenue_recognized_cents: float | None = None
    deferred_amount_cents: float | None = None

    model_config = {"from_attributes": True}


class MartListOut(BaseModel):
    mrr: list[CompanyMrrTrendOut] = Field(default_factory=list)
    locker_pnl: list[LockerPnlOut] = Field(default_factory=list)
    partner_revenue: list[PartnerRevenueMonthlyOut] = Field(default_factory=list)
