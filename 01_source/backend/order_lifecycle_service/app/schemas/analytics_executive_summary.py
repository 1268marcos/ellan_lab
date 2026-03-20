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


class PickupExecutiveSummaryResponse(BaseModel):
    window_start: str | None = None
    window_end: str | None = None

    overview: ExecutiveSummaryOverview
    worst_lockers: ExecutiveSummarySection
    best_sites: ExecutiveSummarySection
    critical_machines: ExecutiveSummarySection
    worst_regions_trend: list[ExecutiveSummaryTrendItem] = Field(default_factory=list)

    insights: list[str] = Field(default_factory=list)
    filters: dict = Field(default_factory=dict)