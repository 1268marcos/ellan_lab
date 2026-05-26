from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BiReadinessOut(BaseModel):
    id: str
    network_player_code: str
    segment_code: str
    score_total: float
    score_data_quality: float
    score_mart_freshness: float
    score_api_coverage: float
    readiness_band: str
    blockers: list[str] = Field(default_factory=list)
    factors: dict[str, Any] = Field(default_factory=dict)
    computed_at: datetime

    model_config = {"from_attributes": True}


class BiReadinessListOut(BaseModel):
    rows: list[BiReadinessOut]
    total: int
    bands: dict[str, int] = Field(default_factory=dict)
    avg_score: float = 0


class BiMartRefreshJobIn(BaseModel):
    mart_name: str
    target_schema: str = "analytics_analytics"
    triggered_by: str | None = None


class BiMartRefreshJobOut(BaseModel):
    id: str
    mart_name: str
    target_schema: str
    status: str
    rows_affected: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    triggered_by: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BiMartRefreshJobListOut(BaseModel):
    jobs: list[BiMartRefreshJobOut]
    total: int


class BiKpiAlertRuleIn(BaseModel):
    kpi_code: str
    comparator: str = "LT"
    threshold_value: float
    severity: str = "WARNING"


class BiKpiAlertRuleOut(BiKpiAlertRuleIn):
    id: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BiKpiAlertEventOut(BaseModel):
    id: str
    rule_id: str
    kpi_code: str
    observed_value: float
    status: str
    network_player_code: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}


class BiLineageEdgeIn(BaseModel):
    source_object: str
    target_object: str
    transform_type: str = "DBT_MODEL"
    owner_team: str = "data-platform"
    notes: str | None = None


class BiLineageEdgeOut(BiLineageEdgeIn):
    id: str
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BiExportJobIn(BaseModel):
    dataset_code: str
    export_format: str = "CSV"
    partner_id: str | None = None


class BiExportJobOut(BaseModel):
    id: str
    partner_id: str | None = None
    export_format: str
    dataset_code: str
    status: str
    file_url: str | None = None
    row_count: int | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class BiTaxonomyOut(BaseModel):
    code: str
    label: str
    description: str | None = None
    sort_order: int
    active: bool

    model_config = {"from_attributes": True}


class BiMarketPresenceOut(BaseModel):
    id: str
    network_player_code: str
    country_code: str
    region_code: str | None = None
    locker_count_est: int | None = None
    parcel_volume_est_monthly: int | None = None
    market_share_pct: float | None = None
    active: bool

    model_config = {"from_attributes": True}


class BiOpsIntelligenceSummaryOut(BaseModel):
    readiness_rows: int
    avg_readiness_score: float
    go_live_count: int
    open_kpi_alerts: int
    pending_mart_jobs: int
    lineage_edges: int
    export_jobs_24h: int
    market_presence_rows: int
