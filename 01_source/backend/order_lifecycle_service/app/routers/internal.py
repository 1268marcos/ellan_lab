# 01_source/backend/order_lifecycle_service/app/routers/internal.py
# AVISO: Contém todo o Analytics
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.internal_auth import require_internal_token
from app.models.lifecycle import (
    DeadlineStatus,
    DeadlineType,
    DomainEvent,
    EventStatus,
    LifecycleDeadline,
)
from app.schemas.analytics import PickupMetricsResponse
from app.schemas.analytics_breakdown import PickupBreakdownResponse
from app.schemas.analytics_executive_summary import PickupExecutiveSummaryResponse
from app.schemas.analytics_ranking import PickupRankingResponse
from app.schemas.internal import (
    AckEventRequest,
    AckEventResponse,
    CancelDeadlineRequest,
    CancelDeadlineResponse,
    CreateDeadlineRequest,
    CreateDeadlineResponse,
    PendingEventItem,
    PendingEventsResponse,
)
from app.schemas.pickup_events import PickupEventIn, PickupEventResponse
from app.services.pickup_analytics_projector import project_pickup_event_facts
from app.services.pickup_breakdown_service import build_pickup_breakdown
from app.services.pickup_executive_summary_service import build_pickup_executive_summary
from app.services.pickup_metrics_service import build_pickup_metrics
from app.services.pickup_ranking_service import build_pickup_ranking

from app.services.pickup_health_service import compute_health

router = APIRouter(prefix="/internal", tags=["internal"])


def utc_now():
    return datetime.now(timezone.utc)


@router.post("/deadlines", response_model=CreateDeadlineResponse)
def create_deadline(
    payload: CreateDeadlineRequest,
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    try:
        deadline_type = DeadlineType(payload.deadline_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid deadline_type",
        )

    existing = (
        db.query(LifecycleDeadline)
        .filter(LifecycleDeadline.deadline_key == payload.deadline_key)
        .first()
    )
    if existing:
        return CreateDeadlineResponse(
            id=str(existing.id),
            deadline_key=existing.deadline_key,
            status=existing.status.value,
            order_id=existing.order_id,
            deadline_type=existing.deadline_type.value,
            due_at=existing.due_at,
        )

    now = utc_now()

    deadline = LifecycleDeadline(
        deadline_key=payload.deadline_key,
        order_id=payload.order_id,
        order_channel=payload.order_channel,
        deadline_type=deadline_type,
        status=DeadlineStatus.PENDING,
        due_at=payload.due_at,
        payload=payload.payload,
        created_at=now,
        updated_at=now,
    )
    db.add(deadline)
    db.commit()
    db.refresh(deadline)

    return CreateDeadlineResponse(
        id=str(deadline.id),
        deadline_key=deadline.deadline_key,
        status=deadline.status.value,
        order_id=deadline.order_id,
        deadline_type=deadline.deadline_type.value,
        due_at=deadline.due_at,
    )


@router.post("/deadlines/cancel", response_model=CancelDeadlineResponse)
def cancel_deadline(
    payload: CancelDeadlineRequest,
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    deadline = (
        db.query(LifecycleDeadline)
        .filter(LifecycleDeadline.deadline_key == payload.deadline_key)
        .first()
    )

    if deadline is None:
        return CancelDeadlineResponse(
            deadline_key=payload.deadline_key,
            status="NOT_FOUND",
            cancelled=False,
        )

    if deadline.status in {DeadlineStatus.EXECUTED, DeadlineStatus.CANCELLED}:
        return CancelDeadlineResponse(
            deadline_key=deadline.deadline_key,
            status=deadline.status.value,
            cancelled=False,
        )

    now = utc_now()
    deadline.status = DeadlineStatus.CANCELLED
    deadline.cancelled_at = now
    deadline.updated_at = now
    db.commit()

    return CancelDeadlineResponse(
        deadline_key=deadline.deadline_key,
        status=deadline.status.value,
        cancelled=True,
    )


@router.get("/events/pending", response_model=PendingEventsResponse)
def list_pending_events(
    limit: int = Query(default=100, ge=1, le=500),
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    events = (
        db.query(DomainEvent)
        .filter(DomainEvent.status == EventStatus.PENDING)
        .order_by(DomainEvent.created_at.asc())
        .limit(limit)
        .all()
    )

    return PendingEventsResponse(
        items=[
            PendingEventItem(
                id=str(event.id),
                event_key=event.event_key,
                aggregate_type=event.aggregate_type,
                aggregate_id=event.aggregate_id,
                event_name=event.event_name,
                event_version=event.event_version,
                status=event.status.value,
                payload=event.payload or {},
                occurred_at=event.occurred_at,
                created_at=event.created_at,
            )
            for event in events
        ]
    )


@router.post("/events/ack", response_model=AckEventResponse)
def ack_event(
    payload: AckEventRequest,
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    event = (
        db.query(DomainEvent)
        .filter(DomainEvent.event_key == payload.event_key)
        .first()
    )

    if event is None:
        return AckEventResponse(
            event_key=payload.event_key,
            status="NOT_FOUND",
            acknowledged=False,
        )

    if event.status == EventStatus.PUBLISHED:
        return AckEventResponse(
            event_key=event.event_key,
            status=event.status.value,
            acknowledged=False,
        )

    now = utc_now()
    event.status = EventStatus.PUBLISHED
    event.published_at = now
    db.commit()

    return AckEventResponse(
        event_key=event.event_key,
        status=event.status.value,
        acknowledged=True,
    )


@router.post("/pickup-events", response_model=PickupEventResponse)
def ingest_pickup_event(
    payload: PickupEventIn,
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(DomainEvent)
        .filter(DomainEvent.event_key == payload.event_key)
        .first()
    )
    if existing:
        return PickupEventResponse(
            ok=True,
            event_key=existing.event_key,
            stored=False,
        )

    now = utc_now()

    event = DomainEvent(
        event_key=payload.event_key,
        aggregate_type="pickup",
        aggregate_id=payload.pickup_id,
        event_name=payload.event_type,
        event_version=1,
        status=EventStatus.PENDING,
        payload={
            "order_id": payload.order_id,
            "pickup_id": payload.pickup_id,
            "channel": payload.channel,
            "region": payload.region,
            "locker_id": payload.locker_id,
            "machine_id": payload.machine_id,
            "slot": payload.slot,
            "operator_id": payload.operator_id,
            "tenant_id": payload.tenant_id,
            "site_id": payload.site_id,
            "correlation_id": payload.correlation_id,
            "source_service": payload.source_service,
            **(payload.payload or {}),
        },
        occurred_at=payload.occurred_at,
        created_at=now,
    )
    db.add(event)
    db.flush()

    project_pickup_event_facts(db, event=event)

    db.commit()

    return PickupEventResponse(
        ok=True,
        event_key=event.event_key,
        stored=True,
    )


@router.get("/analytics/pickup-metrics", response_model=PickupMetricsResponse)
def get_pickup_metrics(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    region: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    slot: str | None = Query(default=None),
    locker_id: str | None = Query(default=None),
    machine_id: str | None = Query(default=None),
    operator_id: str | None = Query(default=None),
    tenant_id: str | None = Query(default=None),
    site_id: str | None = Query(default=None),
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    return build_pickup_metrics(
        db,
        start_at=start_at,
        end_at=end_at,
        region=region,
        channel=channel,
        slot=slot,
        locker_id=locker_id,
        machine_id=machine_id,
        operator_id=operator_id,
        tenant_id=tenant_id,
        site_id=site_id,
    )


@router.get("/analytics/pickup-breakdown", response_model=PickupBreakdownResponse)
def get_pickup_breakdown(
    dimension: str = Query(...),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    region: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    slot: str | None = Query(default=None),
    locker_id: str | None = Query(default=None),
    machine_id: str | None = Query(default=None),
    operator_id: str | None = Query(default=None),
    tenant_id: str | None = Query(default=None),
    site_id: str | None = Query(default=None),
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    try:
        return build_pickup_breakdown(
            db,
            dimension=dimension,
            start_at=start_at,
            end_at=end_at,
            region=region,
            channel=channel,
            slot=slot,
            locker_id=locker_id,
            machine_id=machine_id,
            operator_id=operator_id,
            tenant_id=tenant_id,
            site_id=site_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/analytics/pickup-ranking", response_model=PickupRankingResponse)
def get_pickup_ranking(
    category: str = Query(...),
    metric: str = Query(...),
    dimension: str = Query(...),
    limit: int = Query(default=10, ge=1, le=100),
    direction: str | None = Query(default=None),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    region: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    slot: str | None = Query(default=None),
    locker_id: str | None = Query(default=None),
    machine_id: str | None = Query(default=None),
    operator_id: str | None = Query(default=None),
    tenant_id: str | None = Query(default=None),
    site_id: str | None = Query(default=None),
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    try:
        return build_pickup_ranking(
            db,
            category=category,
            metric=metric,
            dimension=dimension,
            limit=limit,
            direction=direction,
            start_at=start_at,
            end_at=end_at,
            region=region,
            channel=channel,
            slot=slot,
            locker_id=locker_id,
            machine_id=machine_id,
            operator_id=operator_id,
            tenant_id=tenant_id,
            site_id=site_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/analytics/pickup-executive-summary",
    response_model=PickupExecutiveSummaryResponse,
)
def get_pickup_executive_summary(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    region: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    slot: str | None = Query(default=None),
    locker_id: str | None = Query(default=None),
    machine_id: str | None = Query(default=None),
    operator_id: str | None = Query(default=None),
    tenant_id: str | None = Query(default=None),
    site_id: str | None = Query(default=None),
    ranking_limit: int = Query(default=5, ge=1, le=20),
    trend_days_window: int = Query(default=7, ge=1, le=90),
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    return build_pickup_executive_summary(
        db,
        start_at=start_at,
        end_at=end_at,
        region=region,
        channel=channel,
        slot=slot,
        locker_id=locker_id,
        machine_id=machine_id,
        operator_id=operator_id,
        tenant_id=tenant_id,
        site_id=site_id,
        ranking_limit=ranking_limit,
        trend_days_window=trend_days_window,
    )


# =========================================================
# PICKUP HEALTH (NOVO ENDPOINT)
# =========================================================


@router.get("/analytics/pickup-health")
def get_pickup_health(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    region: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    slot: str | None = Query(default=None),
    locker_id: str | None = Query(default=None),
    machine_id: str | None = Query(default=None),
    operator_id: str | None = Query(default=None),
    tenant_id: str | None = Query(default=None),
    site_id: str | None = Query(default=None),
    ranking_limit: int = Query(default=20, ge=1, le=100),
    trend_days_window: int = Query(default=7, ge=1, le=90),
    include_alerts: bool = Query(default=True),
    _: None = Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    """
    🔥 CAMADA FINAL DE PRODUTO
    Consolida ranking + health score em score operacional único
    """

    ranking = build_pickup_ranking(
        db,
        category="efficiency",
        metric="redemption_rate",
        dimension="locker_id",  # pode evoluir depois
        direction="desc",
        limit=ranking_limit,
        start_at=start_at,
        end_at=end_at,
        region=region,
        channel=channel,
        slot=slot,
        locker_id=locker_id,
        machine_id=machine_id,
        operator_id=operator_id,
        tenant_id=tenant_id,
        site_id=site_id,
    )

    results = []

    for item in ranking.items:
        signals = {
            "pickup_success_rate": item.redemption_rate / 100.0 if item.redemption_rate else 0.0,
            "expiration_rate": item.expiration_rate / 100.0 if item.expiration_rate else 0.0,
            "cancel_rate": item.cancellation_rate / 100.0 if item.cancellation_rate else 0.0,
            "avg_pickup_minutes": item.avg_minutes_ready_to_redeemed or 0.0,
            "trend_direction": "stable",  # 🔥 depois evoluímos
            "saturation_level": (
                "high" if item.total_terminal_pickups > 300
                else "medium" if item.total_terminal_pickups > 100
                else "low"
            ),
            "sample_size": item.total_terminal_pickups,
        }

        health = compute_health(signals)

        row = {
            "entity_type": "locker",
            "entity_id": item.dimension_value,
            "tenant_id": tenant_id,
            "operator_id": operator_id,
            "region": region,
            "site_id": site_id,
            "machine_id": machine_id,
            "locker_id": item.dimension_value,
            "health_score": health["health_score"],
            "classification": health["classification"],
            "recommended_action": health["recommended_action"],
            "components": health["components"],
            "signals": signals,
        }

        if include_alerts:
            row["alerts"] = health["alerts"]

        results.append(row)

    # ordenar por pior primeiro
    results.sort(key=lambda x: x["health_score"])

    summary_counts = {
        "total_entities": len(results),
        "healthy_count": sum(1 for r in results if r["classification"] == "healthy"),
        "attention_count": sum(1 for r in results if r["classification"] == "attention"),
        "warning_count": sum(1 for r in results if r["classification"] == "warning"),
        "critical_count": sum(1 for r in results if r["classification"] == "critical"),
        "collapsed_count": sum(1 for r in results if r["classification"] == "collapsed"),
    }

    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc),
        "filters": {
            "tenant_id": tenant_id,
            "operator_id": operator_id,
            "region": region,
            "site_id": site_id,
            "machine_id": machine_id,
            "locker_id": locker_id,
        },
        "summary": summary_counts,
        "ranking": results,
    }
    """
    🔥 CAMADA FINAL DE PRODUTO
    Consolida executive summary + ranking em score operacional único
    """

    summary = build_pickup_executive_summary(
        db,
        start_at=start_at,
        end_at=end_at,
        region=region,
        channel=channel,
        slot=slot,
        locker_id=locker_id,
        machine_id=machine_id,
        operator_id=operator_id,
        tenant_id=tenant_id,
        site_id=site_id,
        ranking_limit=ranking_limit,
        trend_days_window=trend_days_window,
    )

    results = []

    # 🔥 CRÍTICO: usar ranking que já existe
    for item in summary.ranking.items:
        signals = {
            "pickup_success_rate": item.metrics.pickup_success_rate,
            "expiration_rate": item.metrics.expiration_rate,
            "cancel_rate": item.metrics.cancel_rate,
            "avg_pickup_minutes": item.metrics.avg_pickup_minutes,
            "trend_direction": item.trend.direction,
            "saturation_level": item.saturation.level,
            "sample_size": item.metrics.total_pickups,
        }

        health = compute_health(signals)

        row = {
            "entity_type": summary.ranking.dimension,
            "entity_id": item.dimension_value,
            "tenant_id": tenant_id,
            "operator_id": operator_id,
            "region": region,
            "site_id": site_id,
            "machine_id": machine_id,
            "locker_id": locker_id,
            "health_score": health["health_score"],
            "classification": health["classification"],
            "recommended_action": health["recommended_action"],
            "components": health["components"],
            "signals": signals,
        }

        if include_alerts:
            row["alerts"] = health["alerts"]

        results.append(row)

    # ordenar por pior primeiro
    results.sort(key=lambda x: x["health_score"])

    summary_counts = {
        "total_entities": len(results),
        "healthy_count": sum(1 for r in results if r["classification"] == "healthy"),
        "attention_count": sum(1 for r in results if r["classification"] == "attention"),
        "warning_count": sum(1 for r in results if r["classification"] == "warning"),
        "critical_count": sum(1 for r in results if r["classification"] == "critical"),
        "collapsed_count": sum(1 for r in results if r["classification"] == "collapsed"),
    }

    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc),
        "filters": {
            "tenant_id": tenant_id,
            "operator_id": operator_id,
            "region": region,
            "site_id": site_id,
            "machine_id": machine_id,
            "locker_id": locker_id,
        },
        "summary": summary_counts,
        "ranking": results,
    }