from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BiDataQualityCheckOut(BaseModel):
    id: str
    check_code: str
    target_object: str
    rule_type: str
    severity: str
    last_status: str
    last_score: float | None = None
    last_run_at: datetime | None = None
    details: dict = Field(default_factory=dict)
    active: bool = True

    model_config = {"from_attributes": True}


class BiScheduledExportIn(BaseModel):
    schedule_code: str
    dataset_code: str
    cron_expr: str = "0 6 * * *"
    export_format: str = "CSV"
    partner_id: str | None = None
    active: bool = True


class BiScheduledExportOut(BaseModel):
    id: str
    schedule_code: str
    dataset_code: str
    cron_expr: str
    export_format: str
    partner_id: str | None = None
    active: bool
    last_run_at: datetime | None = None
    last_status: str
    next_run_at: datetime | None = None

    model_config = {"from_attributes": True}


class BiAnomalySignalOut(BaseModel):
    id: str
    signal_type: str
    kpi_code: str | None = None
    network_player_code: str | None = None
    observed_value: float | None = None
    baseline_value: float | None = None
    deviation_pct: float | None = None
    severity: str
    status: str
    summary: str
    detected_at: datetime

    model_config = {"from_attributes": True}


class BiOpsBookmarkIn(BaseModel):
    label: str
    route_path: str
    query_json: dict = Field(default_factory=dict)
    pinned: bool = False
    owner_id: str = "ops-default"


class BiOpsBookmarkOut(BaseModel):
    id: str
    owner_id: str
    label: str
    route_path: str
    query: dict = Field(default_factory=dict)
    pinned: bool
    sort_order: int

    model_config = {"from_attributes": True}


class BiPipelineSyncOut(BaseModel):
    pipeline_code: str
    source_object: str
    target_object: str
    lag_minutes: int
    rows_synced: int | None = None
    status: str
    last_sync_at: datetime | None = None


class BiEfficiencyScorecardOut(BaseModel):
    efficiency_score: float
    dq_pass_rate: float
    open_anomalies: int
    scheduled_exports_due: int
    pipeline_lag_max_minutes: int
    bookmarks_count: int
    recommendations: list[str] = Field(default_factory=list)
