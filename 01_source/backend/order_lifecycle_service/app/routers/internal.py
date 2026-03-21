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

from app.services.pickup_health_service import (
    build_entity_context,
    build_health_signals_from_ranking_item,
    compute_health,
    compute_historical_baseline_from_ranking,
    compute_trend_from_ranking,
    detect_anomalies,
    resolve_dimension_for_entity_type,
    supported_entity_types,
)

from app.services.pickup_metrics_service import build_pickup_metrics
from app.services.pickup_ranking_service import build_pickup_ranking

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


@router.get("/analytics/pickup-health")
def get_pickup_health(
    entity_type: str = Query(default="all"),
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
    entity_type = (entity_type or "all").strip().lower()

    if entity_type not in supported_entity_types():
        raise HTTPException(
            status_code=400,
            detail=(
                f"invalid entity_type={entity_type}. "
                f"supported={', '.join(supported_entity_types())}"
            ),
        )

    entity_types = ["locker", "machine", "site", "region"] if entity_type == "all" else [entity_type]

    ranking_by_entity: dict[str, list[dict]] = {}
    all_results: list[dict] = []

    for current_entity_type in entity_types:
        dimension = resolve_dimension_for_entity_type(current_entity_type)

        ranking = build_pickup_ranking(
            db,
            category="efficiency",
            metric="redemption_rate",
            dimension=dimension,
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

        trend_map = compute_trend_from_ranking(
            db=db,
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
            days_window=trend_days_window,
            limit=ranking_limit,
        )

        baseline_map = compute_historical_baseline_from_ranking(
            db=db,
            dimension=dimension,
            end_at=end_at,
            region=region,
            channel=channel,
            slot=slot,
            locker_id=locker_id,
            machine_id=machine_id,
            operator_id=operator_id,
            tenant_id=tenant_id,
            site_id=site_id,
            history_windows=6,
            window_days=trend_days_window,
            limit=ranking_limit,
        )

        entity_results: list[dict] = []

        for item in ranking.items:
            signals = build_health_signals_from_ranking_item(item)

            trend = trend_map.get(item.dimension_value)
            if trend:
                signals["trend_direction"] = trend["direction"]
                signals["trend_delta"] = trend["delta"]
                signals["trend_previous_rate"] = trend["previous_rate"]
                signals["trend_current_rate"] = trend["current_rate"]

            baseline = baseline_map.get(item.dimension_value)
            anomaly = detect_anomalies(
                signals=signals,
                trend=trend,
                baseline=baseline,
            )

            health = compute_health(signals)

            row = build_entity_context(
                entity_type=current_entity_type,
                entity_id=item.dimension_value,
                tenant_id=tenant_id,
                operator_id=operator_id,
                region=region,
                site_id=site_id,
                machine_id=machine_id,
                locker_id=locker_id,
            )

            row.update(
                {
                    "health_score": health["health_score"],
                    "classification": health["classification"],
                    "recommended_action": health["recommended_action"],
                    "components": health["components"],
                    "signals": signals,
                    "metrics": {
                        "total_terminal_pickups": item.total_terminal_pickups,
                        "redeemed_pickups": item.redeemed_pickups,
                        "expired_pickups": item.expired_pickups,
                        "cancelled_pickups": item.cancelled_pickups,
                        "redemption_rate": item.redemption_rate,
                        "expiration_rate": item.expiration_rate,
                        "cancellation_rate": item.cancellation_rate,
                        "avg_minutes_created_to_ready": item.avg_minutes_created_to_ready,
                        "avg_minutes_ready_to_redeemed": item.avg_minutes_ready_to_redeemed,
                        "avg_minutes_door_opened_to_redeemed": item.avg_minutes_door_opened_to_redeemed,
                        "avg_minutes_door_opened_to_door_closed": item.avg_minutes_door_opened_to_door_closed,
                    },
                    "trend": trend,
                    "anomaly": anomaly,
                    "baseline": baseline,
                }
            )

            if include_alerts:
                merged_alerts = list(health["alerts"])
                for alert in anomaly["alerts"]:
                    if alert not in merged_alerts:
                        merged_alerts.append(alert)
                row["alerts"] = merged_alerts

            entity_results.append(row)
            all_results.append(row)

        entity_results.sort(
            key=lambda x: (
                x["health_score"],
                -int((x["metrics"]["total_terminal_pickups"] or 0)),
            )
        )
        ranking_by_entity[current_entity_type] = entity_results

    all_results.sort(key=lambda x: (x["health_score"], -(x["metrics"]["total_terminal_pickups"] or 0)))

    summary = {
        "total_entities": len(all_results),
        "healthy_count": sum(1 for r in all_results if r["classification"] == "healthy"),
        "attention_count": sum(1 for r in all_results if r["classification"] == "attention"),
        "warning_count": sum(1 for r in all_results if r["classification"] == "warning"),
        "critical_count": sum(1 for r in all_results if r["classification"] == "critical"),
        "collapsed_count": sum(1 for r in all_results if r["classification"] == "collapsed"),
    }

    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc),
        "filters": {
            "entity_type": entity_type,
            "start_at": start_at,
            "end_at": end_at,
            "region": region,
            "channel": channel,
            "slot": slot,
            "locker_id": locker_id,
            "machine_id": machine_id,
            "operator_id": operator_id,
            "tenant_id": tenant_id,
            "site_id": site_id,
            "ranking_limit": ranking_limit,
            "trend_days_window": trend_days_window,
            "include_alerts": include_alerts,
        },
        "summary": summary,
        "ranking": all_results if entity_type == "all" else ranking_by_entity[entity_types[0]],
        "ranking_by_entity": ranking_by_entity,
    }