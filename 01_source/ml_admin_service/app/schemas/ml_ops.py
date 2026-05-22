from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MlUseCaseIn(BaseModel):
    code: str
    name: str
    domain: str = "LOCKER"
    description: str | None = None
    owner_team: str | None = None
    tier: str = "STANDARD"
    active: bool = True


class MlUseCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    domain: str
    description: str | None
    owner_team: str | None
    tier: str
    active: bool
    created_at: datetime
    updated_at: datetime


class MlUseCaseListOut(BaseModel):
    items: list[MlUseCaseOut]
    total: int


class MlModelRegistryIn(BaseModel):
    use_case_id: str
    model_version: str
    algorithm: str = "RandomForest"
    framework: str | None = "sklearn"
    artifact_uri: str | None = None
    stage: str = "DEV"
    status_note: str | None = None
    registry_metadata: dict = Field(default_factory=dict)


class MlModelRegistryPromoteIn(BaseModel):
    actor_id: str | None = None
    notes: str | None = None


class MlModelRegistryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    use_case_id: str
    model_version: str
    algorithm: str
    framework: str | None
    artifact_uri: str | None
    stage: str
    status_note: str | None
    registry_metadata_json: str
    promoted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class MlModelRegistryListOut(BaseModel):
    items: list[MlModelRegistryOut]
    total: int


class MlTrainingRunIn(BaseModel):
    use_case_id: str
    run_name: str
    triggered_by: str | None = None
    dataset_ref: str | None = None
    hyperparams: dict = Field(default_factory=dict)


class MlTrainingRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    use_case_id: str
    run_name: str
    model_version: str | None
    status: str
    triggered_by: str | None
    dataset_ref: str | None
    hyperparams_json: str
    metrics_json: str
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class MlTrainingRunListOut(BaseModel):
    items: list[MlTrainingRunOut]
    total: int


class MlFeatureDefinitionIn(BaseModel):
    use_case_id: str | None = None
    feature_name: str
    feature_group: str = "telemetry"
    data_type: str = "float"
    source_table: str | None = None
    freshness_hours: int = 24
    is_nullable: bool = True
    description: str | None = None


class MlFeatureDefinitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    use_case_id: str | None
    feature_name: str
    feature_group: str
    data_type: str
    source_table: str | None
    freshness_hours: int
    is_nullable: bool
    description: str | None
    active: bool
    created_at: datetime


class MlFeatureDefinitionListOut(BaseModel):
    items: list[MlFeatureDefinitionOut]
    total: int


class MlDriftReportIn(BaseModel):
    use_case_id: str
    model_version: str
    report_date: date | None = None
    drift_type: str = "DATA"
    psi_score: float | None = None
    status: str = "OK"
    details: dict = Field(default_factory=dict)


class MlDriftReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    use_case_id: str
    model_version: str
    report_date: date
    drift_type: str
    psi_score: float | None
    status: str
    details_json: str
    created_at: datetime


class MlDriftReportListOut(BaseModel):
    items: list[MlDriftReportOut]
    total: int


class MlInferenceSloIn(BaseModel):
    use_case_id: str
    p95_latency_ms: int = 500
    min_availability_pct: float = 99.5
    max_error_rate_pct: float = 1.0
    min_predictions_per_day: int = 100


class MlInferenceSloOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    use_case_id: str
    p95_latency_ms: int
    min_availability_pct: float
    max_error_rate_pct: float
    min_predictions_per_day: int
    active: bool
    updated_at: datetime


class MlInferenceSloListOut(BaseModel):
    items: list[MlInferenceSloOut]
    total: int


class MlAlertRuleIn(BaseModel):
    use_case_id: str
    rule_code: str
    metric: str
    operator: str = "GT"
    threshold: float
    severity: str = "WARNING"
    notify_webhook: bool = True


class MlAlertRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    use_case_id: str
    rule_code: str
    metric: str
    operator: str
    threshold: float
    severity: str
    notify_webhook: bool
    active: bool
    created_at: datetime


class MlAlertRuleListOut(BaseModel):
    items: list[MlAlertRuleOut]
    total: int


class MlDeploymentEventIn(BaseModel):
    use_case_id: str
    from_version: str | None = None
    to_version: str
    event_type: str = "PROMOTE"
    actor_id: str | None = None
    notes: str | None = None


class MlDeploymentEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    use_case_id: str
    from_version: str | None
    to_version: str
    event_type: str
    actor_id: str | None
    notes: str | None
    created_at: datetime


class MlDeploymentEventListOut(BaseModel):
    items: list[MlDeploymentEventOut]
    total: int


class MlPartnerGrantIn(BaseModel):
    partner_id: str
    use_case_id: str
    scopes: list[str] | None = None


class MlPartnerGrantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    partner_id: str
    use_case_id: str
    scopes_json: str
    created_at: datetime


class MlPartnerGrantListOut(BaseModel):
    items: list[MlPartnerGrantOut]
    total: int
