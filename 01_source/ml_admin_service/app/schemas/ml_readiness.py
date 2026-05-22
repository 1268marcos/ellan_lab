from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MlReadinessOut(BaseModel):
    id: str
    network_player_id: str
    network_player_code: str
    marketplace_channel_id: str | None = None
    score_total: float
    score_capabilities: float
    score_telemetry: float
    score_ml_ops: float
    readiness_band: str
    blockers: list[str] = Field(default_factory=list)
    factors: dict = Field(default_factory=dict)
    computed_at: datetime


class MlReadinessListOut(BaseModel):
    items: list[MlReadinessOut]
    total: int


class MlReadinessHubOut(BaseModel):
    readiness_rows: int
    avg_score: float
    bands: dict[str, int]
    audit_log_rows: int
    open_readiness_alerts: int = 0


class MlReadinessAlertOut(BaseModel):
    id: str
    network_player_code: str
    alert_type: str
    severity: str
    score_delta: float
    previous_score: float | None
    new_score: float
    status: str
    webhook_dispatched: bool
    created_at: datetime
