from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class MlInferenceUsageOut(BaseModel):
    id: str
    usage_date: date
    use_case_code: str
    network_player_code: str | None = None
    request_count: int
    p95_latency_ms: int | None = None
    error_rate_pct: float | None = None
    estimated_cost_usd: float | None = None

    model_config = {"from_attributes": True}


class MlFeatureFreshnessBreachOut(BaseModel):
    id: str
    feature_name: str
    source_table: str
    sla_hours: int
    lag_hours: float
    severity: str
    status: str
    summary: str
    detected_at: datetime

    model_config = {"from_attributes": True}


class MlOpsRecommendationOut(BaseModel):
    id: str
    recommendation_code: str
    category: str
    priority: str
    title: str
    action_hint: str
    related_entity: str | None = None
    status: str
    impact_score: float
    created_at: datetime

    model_config = {"from_attributes": True}


class MlEfficiencyScorecardOut(BaseModel):
    efficiency_score: float
    inference_requests_7d: int
    avg_p95_latency_ms: float | None = None
    open_freshness_breaches: int
    open_recommendations: int
    estimated_cost_7d_usd: float
    recommendations: list[str] = Field(default_factory=list)
