"""Rotas COO (5180): operações, logística, SLA, KPIs e aprovações."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.coo import (
    ApprovalAck,
    ApprovalRequest,
    CooWidgetsSummary,
    DashboardSummary,
    LogisticsManifest,
    OperationalKPIs,
    OperationsHealth,
    SLAViolations,
)
from app.services.coo.kpis_service import KPIsService
from app.services.coo.logistics_service import LogisticsService
from app.services.coo.operations_service import OperationsService
from app.services.coo.sla_service import SLAService

from .deps import require_coo_access

router = APIRouter(
    prefix="/api/v1/coo",
    tags=["COO Portal 5180"],
    dependencies=[Depends(require_coo_access)],
)


@router.get("/dashboard/consolidated", response_model=DashboardSummary)
async def get_consolidated_dashboard(
    db: Session = Depends(get_db),
    days: int = Query(7, description="Dias de histórico"),
) -> DashboardSummary:
    """Dashboard OPS consolidado."""
    return OperationsService(db).get_consolidated_dashboard(days)


@router.get("/health/pickups", response_model=OperationsHealth)
async def get_pickup_health(
    db: Session = Depends(get_db),
    region: str | None = None,
) -> OperationsHealth:
    """Saúde de pickups por região."""
    return OperationsService(db).get_pickup_health(region)


@router.get("/deadlines/urgent")
async def get_urgent_deadlines(
    db: Session = Depends(get_db),
    limit: int = Query(50, description="Limite de registros"),
):
    """Deadlines urgentes (próximas 2 horas)."""
    return OperationsService(db).get_urgent_deadlines(limit)


@router.get("/logistics/manifests/active", response_model=list[LogisticsManifest])
async def get_active_manifests(
    db: Session = Depends(get_db),
    depot_id: str | None = None,
) -> list[LogisticsManifest]:
    """Manifestos ativos por depot (locker)."""
    return LogisticsService(db).get_active_manifests(depot_id)


@router.get("/logistics/routing/realtime")
async def get_realtime_routing(
    db: Session = Depends(get_db),
    region: str | None = None,
):
    """Roteirização em tempo real (manifestos ativos por locker/região)."""
    return LogisticsService(db).get_realtime_routing(region)


@router.get("/logistics/inventory/by-depot")
async def get_inventory_by_depot(
    db: Session = Depends(get_db),
    depot_id: str | None = None,
):
    """Inventário por depot."""
    return LogisticsService(db).get_inventory_by_depot(depot_id)


@router.get("/suppliers/sla", response_model=SLAViolations)
async def get_sla_by_supplier(
    db: Session = Depends(get_db),
    period: str = Query("month", description="week/month/quarter"),
) -> SLAViolations:
    """SLA por fornecedor (parceiros logísticos + violações registradas)."""
    return SLAService(db).get_sla_by_supplier(period)


@router.get("/suppliers/penalties")
async def get_applied_penalties(
    db: Session = Depends(get_db),
    supplier_id: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    """Penalidades aplicadas (stub — retorno vazio até persistência dedicada)."""
    return SLAService(db).get_applied_penalties(supplier_id, start_date, end_date)


@router.get("/suppliers/compliance")
async def get_compliance_reports(
    db: Session = Depends(get_db),
    period: str = Query("month"),
):
    """Compliance reports por fornecedor."""
    return SLAService(db).get_compliance_reports(period)


@router.get("/kpis/network/uptime", response_model=OperationalKPIs)
async def get_network_uptime(
    db: Session = Depends(get_db),
    days: int = Query(30, description="Últimos N dias"),
) -> OperationalKPIs:
    """Uptime da rede (lockers ativos / total)."""
    return KPIsService(db).get_network_uptime(days)


@router.get("/kpis/mttr", response_model=OperationalKPIs)
async def get_mean_time_to_resolve(
    db: Session = Depends(get_db),
    incident_type: str | None = None,
) -> OperationalKPIs:
    """Tempo médio de resolução (amostra a partir de auditoria OPS)."""
    return KPIsService(db).get_mttr(incident_type)


@router.get("/kpis/fleet/efficiency", response_model=OperationalKPIs)
async def get_fleet_efficiency(
    db: Session = Depends(get_db),
    days: int = Query(30),
) -> OperationalKPIs:
    """Eficiência de frota (entregas por locker ativo por dia, proxy)."""
    return KPIsService(db).get_fleet_efficiency(days)


@router.get("/approvals/pending")
async def get_pending_procedures(
    db: Session = Depends(get_db),
    approval_type: str | None = None,
):
    """Procedimentos pendentes de aprovação."""
    return OperationsService(db).get_pending_approvals(approval_type)


@router.post("/approvals/sla/adjust", response_model=ApprovalAck)
async def adjust_regional_sla(
    approval: ApprovalRequest,
    db: Session = Depends(get_db),
) -> ApprovalAck:
    """Ajustes de SLA regional (stub de fila)."""
    return OperationsService(db).submit_sla_adjustment(approval)


@router.post("/approvals/expansion", response_model=ApprovalAck)
async def request_expansion(
    approval: ApprovalRequest,
    db: Session = Depends(get_db),
) -> ApprovalAck:
    """Solicitações de expansão (stub de fila)."""
    return OperationsService(db).submit_expansion_request(approval)


@router.get("/widgets/summary", response_model=CooWidgetsSummary)
async def get_widgets_summary(db: Session = Depends(get_db)) -> CooWidgetsSummary:
    """Widgets principais do dashboard."""
    return KPIsService(db).get_widgets_summary()
