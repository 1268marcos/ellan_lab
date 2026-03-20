# 01_source/backend/order_lifecycle_service/app/services/pickup_metrics_service.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Numeric, func
from sqlalchemy.orm import Query, Session

from app.models.lifecycle import AnalyticsFact
from app.schemas.analytics import PickupMetricsResponse


def _apply_filters(
    query: Query,
    *,
    start_at: datetime | None,
    end_at: datetime | None,
    region: str | None,
    channel: str | None,
    slot: str | None,
    locker_id: str | None,
    machine_id: str | None,
    operator_id: str | None,
    tenant_id: str | None,
    site_id: str | None,
) -> Query:
    if start_at is not None:
        query = query.filter(AnalyticsFact.occurred_at >= start_at)

    if end_at is not None:
        query = query.filter(AnalyticsFact.occurred_at <= end_at)

    if region:
        query = query.filter(AnalyticsFact.region_code == region)

    if channel:
        query = query.filter(AnalyticsFact.order_channel == channel)

    if slot:
        query = query.filter(AnalyticsFact.slot_id == slot)

    if locker_id:
        query = query.filter(AnalyticsFact.payload["locker_id"].astext == locker_id)

    if machine_id:
        query = query.filter(AnalyticsFact.payload["machine_id"].astext == machine_id)

    if operator_id:
        query = query.filter(AnalyticsFact.payload["operator_id"].astext == operator_id)

    if tenant_id:
        query = query.filter(AnalyticsFact.payload["tenant_id"].astext == tenant_id)

    if site_id:
        query = query.filter(AnalyticsFact.payload["site_id"].astext == site_id)

    return query


def _avg_minutes(db: Session, fact_name: str, **filters: Any) -> float | None:
    query = db.query(
        func.avg(
            AnalyticsFact.payload["minutes"].astext.cast(Numeric)
        )
    ).filter(
        AnalyticsFact.fact_name == fact_name
    )

    query = _apply_filters(query, **filters)
    value = query.scalar()

    if value is None:
        return None

    return round(float(value), 3)


def _count_terminal_state(db: Session, terminal_state: str, **filters: Any) -> int:
    query = db.query(AnalyticsFact).filter(
        AnalyticsFact.fact_name == "pickup_terminal_state",
        AnalyticsFact.payload["terminal_state"].astext == terminal_state,
    )
    query = _apply_filters(query, **filters)
    return query.count()


def build_pickup_metrics(
    db: Session,
    *,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    region: str | None = None,
    channel: str | None = None,
    slot: str | None = None,
    locker_id: str | None = None,
    machine_id: str | None = None,
    operator_id: str | None = None,
    tenant_id: str | None = None,
    site_id: str | None = None,
) -> PickupMetricsResponse:
    filters = dict(
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

    redeemed_pickups = _count_terminal_state(db, "redeemed", **filters)
    expired_pickups = _count_terminal_state(db, "expired", **filters)
    cancelled_pickups = _count_terminal_state(db, "cancelled", **filters)

    total_terminal_pickups = redeemed_pickups + expired_pickups + cancelled_pickups

    def _rate(value: int, total: int) -> float:
        if total <= 0:
            return 0.0
        return round((value / total) * 100.0, 3)

    return PickupMetricsResponse(
        window_start=start_at.isoformat() if start_at else None,
        window_end=end_at.isoformat() if end_at else None,
        total_terminal_pickups=total_terminal_pickups,
        redeemed_pickups=redeemed_pickups,
        expired_pickups=expired_pickups,
        cancelled_pickups=cancelled_pickups,
        redemption_rate=_rate(redeemed_pickups, total_terminal_pickups),
        expiration_rate=_rate(expired_pickups, total_terminal_pickups),
        cancellation_rate=_rate(cancelled_pickups, total_terminal_pickups),
        avg_minutes_created_to_ready=_avg_minutes(
            db, "pickup_sla_created_to_ready", **filters
        ),
        avg_minutes_ready_to_redeemed=_avg_minutes(
            db, "pickup_sla_ready_to_redeemed", **filters
        ),
        avg_minutes_door_opened_to_redeemed=_avg_minutes(
            db, "pickup_sla_door_opened_to_redeemed", **filters
        ),
        avg_minutes_door_opened_to_door_closed=_avg_minutes(
            db, "pickup_sla_door_opened_to_door_closed", **filters
        ),
        filters={
            "region": region,
            "channel": channel,
            "slot": slot,
            "locker_id": locker_id,
            "machine_id": machine_id,
            "operator_id": operator_id,
            "tenant_id": tenant_id,
            "site_id": site_id,
        },
    )