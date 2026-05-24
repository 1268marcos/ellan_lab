from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field


class EcosystemInsightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    catalog_code: str
    insight_type: str
    severity: str
    title: str
    detail_json: str
    suggested_action: str | None
    status: str
    detected_at: datetime


class EcosystemInsightListOut(BaseModel):
    items: list[EcosystemInsightOut]
    total: int
    open_count: int
    by_severity: dict[str, int] = Field(default_factory=dict)


class PlayerBenchmarkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    catalog_code: str
    segment_code: str
    readiness_score: int
    readiness_rank: int | None
    readiness_percentile: float | None
    relation_count: int
    capability_count: int
    coverage_count: int
    estimated_locker_count: int | None
    integration_status: str | None
    composite_score: int
    computed_at: datetime


class BenchmarkListOut(BaseModel):
    items: list[PlayerBenchmarkOut]
    total: int
    top_global: list[PlayerBenchmarkOut] = Field(default_factory=list)


class HealthCheckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    catalog_code: str
    check_type: str
    status: str
    latency_ms: int | None
    http_status: int | None
    message: str | None
    checked_at: datetime


class HealthCheckListOut(BaseModel):
    items: list[HealthCheckOut]
    total: int
    healthy_count: int
    degraded_count: int


class RecommendationOut(BaseModel):
    catalog_code: str
    recommendation_type: str
    target_code: str | None
    title: str
    rationale: str
    priority: int


class RecommendationListOut(BaseModel):
    catalog_code: str
    items: list[RecommendationOut]
    total: int


class IntelligenceAnalyzeOut(BaseModel):
    insights_created: int
    insights_updated: int
    benchmarks_computed: int
    health_checks_run: int
    milestones_generated: int


class IntelligenceDashboardOut(BaseModel):
    open_insights: int
    critical_insights: int
    players_analyzed: int
    avg_readiness: float
    avg_composite_score: float
    top_benchmarks: list[PlayerBenchmarkOut]
    recent_insights: list[EcosystemInsightOut]
    health_summary: dict[str, int]
