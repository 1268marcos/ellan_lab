# 01_source/backend/order_lifecycle_service/app/schemas/analytics_executive_summary.py
from __future__ import annotations

from pydantic import BaseModel, Field


class ExecutiveSummaryOverview(BaseModel):
    total_terminal_pickups: int = 0
    redeemed_pickups: int = 0
    expired_pickups: int = 0
    cancelled_pickups: int = 0

    redemption_rate: float = 0.0
    expiration_rate: float = 0.0
    cancellation_rate: float = 0.0

    avg_minutes_created_to_ready: float | None = None
    avg_minutes_ready_to_redeemed: float | None = None
    avg_minutes_door_opened_to_redeemed: float | None = None
    avg_minutes_door_opened_to_door_closed: float | None = None


class ExecutiveSummaryItem(BaseModel):
    rank: int
    dimension_value: str | None = None
    metric: str
    metric_value: float
    label: str

    severity: str = "LOW"
    recommended_action: str = "monitor"

    total_terminal_pickups: int = 0
    redeemed_pickups: int = 0
    expired_pickups: int = 0
    cancelled_pickups: int = 0

    redemption_rate: float = 0.0
    expiration_rate: float = 0.0
    cancellation_rate: float = 0.0

    avg_minutes_created_to_ready: float | None = None
    avg_minutes_ready_to_redeemed: float | None = None
    avg_minutes_door_opened_to_redeemed: float | None = None
    avg_minutes_door_opened_to_door_closed: float | None = None

    stddev_minutes_ready_to_redeemed: float | None = None


class ExecutiveSummarySection(BaseModel):
    title: str
    dimension: str
    metric: str
    direction: str
    items: list[ExecutiveSummaryItem] = Field(default_factory=list)


class ExecutiveSummaryTrendItem(BaseModel):
    region: str | None = None
    previous_redemption_rate: float = 0.0
    current_redemption_rate: float = 0.0
    delta_redemption_rate: float = 0.0
    previous_terminal_pickups: int = 0
    current_terminal_pickups: int = 0
    label: str = ""

    severity: str = "LOW"
    recommended_action: str = "monitor"


class ExecutiveActionItem(BaseModel):
    title: str
    severity: str
    recommended_action: str
    dimension: str
    dimension_value: str | None = None
    reason: str


class PickupExecutiveSummaryResponse(BaseModel):
    window_start: str | None = None
    window_end: str | None = None

    overview: ExecutiveSummaryOverview

    worst_lockers: ExecutiveSummarySection
    best_sites: ExecutiveSummarySection
    critical_machines: ExecutiveSummarySection

    positive_highlights: list[ExecutiveSummarySection] = Field(default_factory=list)
    saturation: list[ExecutiveSummarySection] = Field(default_factory=list)
    reliability: list[ExecutiveSummarySection] = Field(default_factory=list)

    worsening_regions_trend: list[ExecutiveSummaryTrendItem] = Field(default_factory=list)
    improving_regions_trend: list[ExecutiveSummaryTrendItem] = Field(default_factory=list)
    stable_regions_trend: list[ExecutiveSummaryTrendItem] = Field(default_factory=list)

    actions: list[ExecutiveActionItem] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    filters: dict = Field(default_factory=dict)