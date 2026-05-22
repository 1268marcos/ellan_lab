from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MlModelMetadataIn(BaseModel):
    model_version: str
    metrics: dict = Field(default_factory=dict)
    status: str = "ACTIVE"


class MlModelMetadataUpdate(BaseModel):
    metrics: dict | None = None
    status: str | None = None


class MlModelMetadataOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_version: str
    trained_at: datetime
    metrics_json: str
    status: str


class MlModelMetadataListOut(BaseModel):
    items: list[MlModelMetadataOut]
    total: int


class MlFeaturesDailyIn(BaseModel):
    locker_id: str
    feature_date: date
    temperature_mean: float | None = None
    humidity_mean: float | None = None
    battery_min: float | None = None
    door_failures_7d: int = 0
    usage_events_7d: int = 0
    uptime_hours_7d: float = 0
    failure_label_7d: int = 0


class MlFeaturesDailyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    locker_id: str
    feature_date: date
    temperature_mean: float | None
    humidity_mean: float | None
    battery_min: float | None
    door_failures_7d: int
    usage_events_7d: int
    uptime_hours_7d: float
    failure_label_7d: int
    created_at: datetime


class MlFeaturesDailyListOut(BaseModel):
    items: list[MlFeaturesDailyOut]
    total: int


class MlPredictionsLogIn(BaseModel):
    locker_id: str
    failure_probability: float = Field(ge=0, le=1)
    health_score: float = Field(ge=0, le=100)
    model_version: str


class MlPredictionsLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    locker_id: str
    predicted_at: datetime
    failure_probability: float
    health_score: float
    model_version: str


class MlPredictionsLogListOut(BaseModel):
    items: list[MlPredictionsLogOut]
    total: int


class MlPredictionFeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    prediction_id: int | None
    actual_value: float | None
    error_pct: float | None
    feedback_at: datetime | None
    model_performance_status: str | None
    created_at: datetime


class MlPredictionFeedbackListOut(BaseModel):
    items: list[MlPredictionFeedbackOut]
    total: int


class MlDashboardOut(BaseModel):
    active_models: int
    predictions_24h: int
    features_rows: int
    feedback_rows: int
    partners: int
    use_cases: int = 0
    registry_production: int = 0
    training_running: int = 0
    drift_critical: int = 0
    feature_definitions: int = 0
    alert_rules: int = 0
    deployments_7d: int = 0
    locker_network_players: int = 0
    locker_network_priority: int = 0
    network_ml_profiles: int = 0
    player_capabilities: int = 0
    player_relations: int = 0
    market_presence_rows: int = 0
    tier1_players: int = 0
    ml_readiness_rows: int = 0
    ml_readiness_go_live: int = 0
    ml_readiness_avg_score: float = 0.0
    ml_readiness_alerts_open: int = 0
