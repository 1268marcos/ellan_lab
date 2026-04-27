# 01_source/order_pickup_service/app/schemas/dev_admin.py
from typing import Any

from pydantic import BaseModel, Field


class DevResetLockerIn(BaseModel):
    region: str = Field(..., description="SP ou PT")
    locker_id: str = Field(..., description="Locker físico a ser resetado")
    purge_local_data: bool = Field(
        default=True,
        description="Apaga Orders / Allocations / Pickups locais do locker",
    )
    release_known_allocations_first: bool = Field(
        default=True,
        description="Tenta soltar allocations locais antes de resetar os slots",
    )


class DevResetLockerOut(BaseModel):
    ok: bool
    region: str
    locker_id: str
    slots_total: int
    released_allocations: list[str]
    slot_reset_results: list[dict[str, Any]]
    deleted_pickups: int
    deleted_allocations: int
    deleted_orders: int
    message: str


class DevReleaseRegionalAllocationsIn(BaseModel):
    region: str = Field(..., description="SP ou PT")
    locker_id: str = Field(..., description="Locker físico do qual as allocations serão liberadas")
    allocation_ids: list[str] = Field(
        default_factory=list,
        description="Lista opcional de allocation_ids a serem liberados no backend regional",
    )
    auto_collect_from_local_db: bool = Field(
        default=True,
        description="Quando true, coleta allocations locais do locker caso allocation_ids não seja informado",
    )


class DevReleaseRegionalAllocationsOut(BaseModel):
    ok: bool
    region: str
    locker_id: str
    results: list[dict[str, Any]]
    released_count: int
    failed_count: int
    message: str


class DevReconcileOrderIn(BaseModel):
    order_id: str = Field(..., description="ID do pedido a reconciliar")


class DevReconcileOrderOut(BaseModel):
    ok: bool
    order_id: str
    status: str
    message: str
    compensation: dict[str, Any]


class DevReconciliationPendingItemOut(BaseModel):
    id: str
    order_id: str
    reason: str
    status: str
    attempt_count: int
    max_attempts: int
    next_retry_at: str | None = None
    last_error: str | None = None
    updated_at: str | None = None


class DevReconciliationPendingListOut(BaseModel):
    ok: bool
    total: int
    items: list[DevReconciliationPendingItemOut]


class DevOpsAuditItemOut(BaseModel):
    id: str
    action: str
    result: str
    correlation_id: str
    user_id: str | None = None
    role: str | None = None
    order_id: str | None = None
    error_message: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None


class DevOpsAuditListOut(BaseModel):
    ok: bool
    total: int
    items: list[DevOpsAuditItemOut]


class DevOpsMetricAlertOut(BaseModel):
    severity: str
    code: str
    message: str
    value: float | int
    threshold: float | int
    impact: str | None = None
    investigate_hint: str | None = None
    mitigation_hint: str | None = None
    investigate_url: str | None = None
    confidence_level: str | None = None
    data_quality_flag: str | None = None


class DevOpsMetricsWindowOut(BaseModel):
    lookback_hours: int
    from_: str = Field(..., alias="from")
    to: str


class DevOpsMetricsKpisOut(BaseModel):
    total_ops_actions: int
    success_actions: int
    error_actions: int
    error_rate: float
    reconciliation_actions: int
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_samples: int = 0
    pending_open_count: int
    pending_age_0_1h: int = 0
    pending_age_1_4h: int = 0
    pending_age_4_24h: int = 0
    pending_age_24h_plus: int = 0
    pending_due_retry_count: int
    pending_processing_stale_count: int
    pending_failed_final_count: int
    avg_open_pending_age_min: float
    reconciliation_auto_rate: float = 0.0
    avg_reconciliation_time_min: float = 0.0
    reconciliation_total_completed: int = 0
    reconciliation_done_count: int = 0
    reconciliation_failed_final_count_window: int = 0
    unresolved_exceptions_count: int = 0


class DevOpsMetricsActionKpisOut(BaseModel):
    total_ops_actions: int
    success_actions: int
    error_actions: int
    error_rate: float
    reconciliation_actions: int
    latency_p50_ms: float = 0.0
    latency_p95_ms: float = 0.0
    latency_samples: int = 0


class DevOpsMetricsComparisonWindowOut(BaseModel):
    lookback_hours: int
    from_: str = Field(..., alias="from")
    to: str


class DevOpsMetricsComparisonOut(BaseModel):
    window: DevOpsMetricsComparisonWindowOut
    kpis: DevOpsMetricsActionKpisOut


class DevOpsMetricsTrendPointOut(BaseModel):
    from_: str = Field(..., alias="from")
    to: str
    total_ops_actions: int
    error_rate: float
    latency_p95_ms: float


class DevOpsMetricsTrendsOut(BaseModel):
    bucket_minutes: int
    points: list[DevOpsMetricsTrendPointOut]


class DevOpsPredictiveMonitoringOut(BaseModel):
    window_days: int
    emitted_alerts: int
    confirmed_alerts: int
    false_positive_alerts: int
    false_positive_rate: float
    recommendation: str = "KEEP"


class DevOpsPredictiveThresholdsOut(BaseModel):
    predictive_min_volume: int
    predictive_error_min_rate: float
    predictive_error_accel_factor: float
    predictive_latency_min_ms: float
    predictive_latency_accel_factor: float


class DevOpsTopErrorOut(BaseModel):
    message: str
    count: int
    percentage: float
    category: str | None = None


class DevOpsErrorCategoryOut(BaseModel):
    category: str
    count: int
    percentage: float


class DevOpsErrorClassificationOut(BaseModel):
    total_error_actions: int
    categorized_actions: int
    categories: list[DevOpsErrorCategoryOut] = Field(default_factory=list)


class DevOpsErrorEvidenceOut(BaseModel):
    audit_id: str
    created_at: str | None = None
    correlation_id: str
    action: str
    message: str
    category: str


class DevOpsTopCauseOut(BaseModel):
    message: str
    category: str
    count: int
    percentage: float
    evidence: list[DevOpsErrorEvidenceOut] = Field(default_factory=list)


class DevOpsErrorInvestigationReportOut(BaseModel):
    ok: bool
    window: DevOpsMetricsWindowOut
    total_error_actions: int
    categories: list[DevOpsErrorCategoryOut] = Field(default_factory=list)
    top_causes: list[DevOpsTopCauseOut] = Field(default_factory=list)


class DevOpsPredictiveSnapshotIn(BaseModel):
    environment: str = "hml"
    decision: str = "KEEP"
    rationale: str | None = None
    predictive_min_volume: int | None = None
    predictive_error_min_rate: float | None = None
    predictive_error_accel_factor: float | None = None
    predictive_latency_min_ms: float | None = None
    predictive_latency_accel_factor: float | None = None


class DevOpsPredictiveSnapshotOut(BaseModel):
    id: str
    created_at: str | None = None
    environment: str
    decision: str
    rationale: str | None = None
    false_positive_rate: float = 0.0
    emitted_alerts: int = 0
    confirmed_alerts: int = 0
    false_positive_alerts: int = 0
    thresholds: DevOpsPredictiveThresholdsOut | None = None


class DevOpsMetricsOut(BaseModel):
    ok: bool
    window: DevOpsMetricsWindowOut
    kpis: DevOpsMetricsKpisOut
    alerts: list[DevOpsMetricAlertOut]
    comparison: DevOpsMetricsComparisonOut | None = None
    trends: DevOpsMetricsTrendsOut | None = None
    predictive_monitoring: DevOpsPredictiveMonitoringOut | None = None
    predictive_thresholds: DevOpsPredictiveThresholdsOut | None = None
    top_errors: list[DevOpsTopErrorOut] = Field(default_factory=list)
    error_classification: DevOpsErrorClassificationOut | None = None
    predictive_snapshots: list[DevOpsPredictiveSnapshotOut] = Field(default_factory=list)


class DevOrderStatusAuditItemOut(BaseModel):
    order_id: str
    order_status: str
    payment_status: str | None = None
    paid_at: str | None = None
    picked_up_at: str | None = None
    pickup_deadline_at: str | None = None
    pickup_status: str | None = None
    pickup_lifecycle_stage: str | None = None
    pickup_id: str | None = None
    reason: str


class DevOrderStatusAuditListOut(BaseModel):
    ok: bool
    total: int
    items: list[DevOrderStatusAuditItemOut]


class DevOrderStatusAuditPagedOut(BaseModel):
    ok: bool
    total: int
    limit: int
    offset: int
    has_more: bool
    from_: str = Field(..., alias="from")
    to: str
    items: list[DevOrderStatusAuditItemOut]