# 01_source/backend/order_lifecycle_service/app/schemas/analytics_ranking.py
from __future__ import annotations

from pydantic import BaseModel, Field


class PickupRankingItem(BaseModel):
    rank: int
    dimension_value: str | None = None
    metric: str
    metric_value: float

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


class PickupRankingResponse(BaseModel):
    category: str
    metric: str
    dimension: str
    direction: str
    limit: int

    window_start: str | None = None
    window_end: str | None = None

    items: list[PickupRankingItem] = Field(default_factory=list)
    filters: dict = Field(default_factory=dict)