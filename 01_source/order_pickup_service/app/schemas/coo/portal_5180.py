"""Schemas da API COO (portal 5180)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    horizon_days: int
    as_of: str
    orders_in_window: int
    active_allocations: int
    pending_pickup_allocations: int
    error_allocations: int
    lockers_total: int
    lockers_active: int
    # Retiradas (tabela `pickups`) no mesmo horizonte — complementa alocações/pedidos
    pickups_created_in_window: int = 0
    pickups_redeemed_in_window: int = 0
    pickup_completion_rate_pct: float = 0.0
    avg_pickup_cycle_min: float | None = None


class OperationsHealth(BaseModel):
    region: str | None = None
    pending_pickup: int
    opened_for_pickup: int
    errors: int
    health_score: float = Field(description="0–100, heurística operacional")
    as_of: str


class LogisticsManifest(BaseModel):
    id: str
    logistics_partner_id: str
    locker_id: str
    status: str
    manifest_date: str
    expected_parcel_count: int
    actual_parcel_count: int
    carrier_route_code: str | None = None


class LogisticsRoutingRow(BaseModel):
    region: str | None
    locker_id: str
    active_manifests: int
    in_transit: int


class DepotInventoryRow(BaseModel):
    locker_id: str
    region: str | None
    total_slots: int
    reserved_hint: int


class SLASupplierRow(BaseModel):
    supplier_id: str
    supplier_label: str
    on_time_pct: float
    breach_count: int


class SLAViolations(BaseModel):
    period: str
    as_of: str
    suppliers: list[SLASupplierRow] = Field(default_factory=list)


class PenaltyRecord(BaseModel):
    supplier_id: str
    penalty_cents: int
    applied_at: str | None = None
    reason: str | None = None


class ComplianceReportRow(BaseModel):
    supplier_id: str
    compliance_score: float
    audit_notes: str | None = None


class OperationalKPIs(BaseModel):
    metric_key: str
    value: float
    unit: str
    window_days: int | None = None
    as_of: str
    # Dados opcionais para drill-down (clientes podem ignorar)
    historical: list[dict[str, Any]] | None = Field(default=None)
    breakdown: list[dict[str, Any]] | None = Field(default=None)


class ApprovalRequest(BaseModel):
    approval_type: str | None = None
    subject: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ApprovalAck(BaseModel):
    status: str
    approval_id: str
    message: str | None = None


class CooWidgetsSummary(BaseModel):
    sla_violated_24h: int
    avg_pickup_time_min: float | None
    deliveries_today: int
    lockers_offline: int
    cost_per_delivery: float | None
