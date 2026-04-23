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
    pending_open_count: int
    pending_due_retry_count: int
    pending_processing_stale_count: int
    pending_failed_final_count: int
    avg_open_pending_age_min: float


class DevOpsMetricsOut(BaseModel):
    ok: bool
    window: DevOpsMetricsWindowOut
    kpis: DevOpsMetricsKpisOut
    alerts: list[DevOpsMetricAlertOut]