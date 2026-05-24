from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PlayerReadinessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_code: str
    readiness_score: int
    grade: str
    fx_linked: bool
    fiscal_linked: bool
    compliance_ok: bool
    relation_count: int
    corridor_count: int
    detail_json: dict
    computed_at: datetime


class PlayerReadinessListOut(BaseModel):
    items: list[PlayerReadinessOut]
    total: int
    avg_score: float


class EcosystemInsightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    player_code: str | None
    corridor_code: str | None
    insight_type: str
    severity: str
    title: str
    detail_json: dict
    suggested_action: str | None
    status: str
    detected_at: datetime
    resolved_at: datetime | None


class EcosystemInsightListOut(BaseModel):
    items: list[EcosystemInsightOut]
    total: int
    open_by_severity: dict[str, int] = Field(default_factory=dict)


class FxAlertRuleIn(BaseModel):
    name: str
    base_currency: str
    quote_currency: str
    threshold_bps: int = Field(ge=1, le=5000)
    direction: str = "BOTH"
    is_active: bool = True


class FxAlertRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    base_currency: str
    quote_currency: str
    threshold_bps: int
    direction: str
    is_active: bool
    created_at: datetime


class FxAlertRuleListOut(BaseModel):
    items: list[FxAlertRuleOut]
    total: int


class FxAlertEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    rule_id: str
    base_currency: str
    quote_currency: str
    previous_rate: Decimal | None
    current_rate: Decimal
    change_bps: int
    status: str
    triggered_at: datetime
    acknowledged_at: datetime | None


class FxAlertEventListOut(BaseModel):
    items: list[FxAlertEventOut]
    total: int


class SettlementScheduleIn(BaseModel):
    scope_type: str
    scope_code: str
    country_code: str
    settlement_currency: str
    settlement_days: int = 2
    cut_off_time_utc: str = "17:00"
    weekend_policy: str = "SKIP_WEEKEND"
    notes: str | None = None
    is_active: bool = True


class SettlementScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    scope_type: str
    scope_code: str
    country_code: str
    settlement_currency: str
    settlement_days: int
    cut_off_time_utc: str
    weekend_policy: str
    notes: str | None
    is_active: bool
    created_at: datetime


class SettlementScheduleListOut(BaseModel):
    items: list[SettlementScheduleOut]
    total: int


class IntelligenceAnalyzeOut(BaseModel):
    players_scored: int
    insights_created: int
    insights_updated: int
    fx_events_triggered: int
    avg_readiness: float


class IntelligenceDashboardOut(BaseModel):
    players_total: int
    avg_readiness: float
    grade_distribution: dict[str, int]
    open_insights: int
    insights_by_severity: dict[str, int]
    open_fx_alerts: int
    settlement_schedules: int
    corridors_active: int
    fx_rates_count: int
    top_gaps: list[str]
