# 01_source/backend/order_lifecycle_service/app/services/analytics_breakdown_service.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Numeric, func
from sqlalchemy.orm import Query, Session

from app.models.lifecycle import AnalyticsFact
from app.schemas.analytics_breakdown import (
    PickupBreakdownItem,
    PickupBreakdownResponse,
)

from app.core.datetime_utils import to_iso_utc


_ALLOWED_DIMENSIONS = {
    "region",
    "channel",
    "slot",
    "locker_id",
    "machine_id",
    "operator_id",
    "tenant_id",
    "site_id",
}


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


def _dimension_expr(dimension: str):
    if dimension == "region":
        return AnalyticsFact.region_code
    if dimension == "channel":
        return AnalyticsFact.order_channel
    if dimension == "slot":
        return AnalyticsFact.slot_id
    if dimension == "locker_id":
        return AnalyticsFact.payload["locker_id"].astext
    if dimension == "machine_id":
        return AnalyticsFact.payload["machine_id"].astext
    if dimension == "operator_id":
        return AnalyticsFact.payload["operator_id"].astext
    if dimension == "tenant_id":
        return AnalyticsFact.payload["tenant_id"].astext
    if dimension == "site_id":
        return AnalyticsFact.payload["site_id"].astext
    raise ValueError(f"unsupported dimension: {dimension}")


def _grouped_terminal_counts(db: Session, *, dimension: str, terminal_state: str, **filters: Any) -> dict[str | None, int]:
    dim = _dimension_expr(dimension)

    query = db.query(
        dim.label("dimension_value"),
        func.count(AnalyticsFact.id).label("count_value"),
    ).filter(
        AnalyticsFact.fact_name == "pickup_terminal_state",
        AnalyticsFact.payload["terminal_state"].astext == terminal_state,
    )

    query = _apply_filters(query, **filters)
    query = query.group_by(dim)

    return {row.dimension_value: int(row.count_value) for row in query.all()}


def _grouped_avg_minutes(db: Session, *, dimension: str, fact_name: str, **filters: Any) -> dict[str | None, float | None]:
    dim = _dimension_expr(dimension)

    query = db.query(
        dim.label("dimension_value"),
        func.avg(AnalyticsFact.payload["minutes"].astext.cast(Numeric)).label("avg_value"),
    ).filter(
        AnalyticsFact.fact_name == fact_name,
    )

    query = _apply_filters(query, **filters)
    query = query.group_by(dim)

    result: dict[str | None, float | None] = {}
    for row in query.all():
        result[row.dimension_value] = round(float(row.avg_value), 3) if row.avg_value is not None else None
    return result


def build_pickup_breakdown(
    db: Session,
    *,
    dimension: str,
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
) -> PickupBreakdownResponse:
    if dimension not in _ALLOWED_DIMENSIONS:
        raise ValueError(f"unsupported dimension: {dimension}")

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

    redeemed = _grouped_terminal_counts(db, dimension=dimension, terminal_state="redeemed", **filters)
    expired = _grouped_terminal_counts(db, dimension=dimension, terminal_state="expired", **filters)
    cancelled = _grouped_terminal_counts(db, dimension=dimension, terminal_state="cancelled", **filters)

    created_to_ready = _grouped_avg_minutes(db, dimension=dimension, fact_name="pickup_sla_created_to_ready", **filters)
    ready_to_redeemed = _grouped_avg_minutes(db, dimension=dimension, fact_name="pickup_sla_ready_to_redeemed", **filters)
    door_opened_to_redeemed = _grouped_avg_minutes(db, dimension=dimension, fact_name="pickup_sla_door_opened_to_redeemed", **filters)
    door_opened_to_door_closed = _grouped_avg_minutes(db, dimension=dimension, fact_name="pickup_sla_door_opened_to_door_closed", **filters)

    keys = set()
    keys.update(redeemed.keys())
    keys.update(expired.keys())
    keys.update(cancelled.keys())
    keys.update(created_to_ready.keys())
    keys.update(ready_to_redeemed.keys())
    keys.update(door_opened_to_redeemed.keys())
    keys.update(door_opened_to_door_closed.keys())

    def _rate(value: int, total: int) -> float:
        if total <= 0:
            return 0.0
        return round((value / total) * 100.0, 3)

    items: list[PickupBreakdownItem] = []
    for key in sorted(keys, key=lambda v: (v is None, str(v))):
        redeemed_count = int(redeemed.get(key, 0))
        expired_count = int(expired.get(key, 0))
        cancelled_count = int(cancelled.get(key, 0))
        total = redeemed_count + expired_count + cancelled_count

        items.append(
            PickupBreakdownItem(
                dimension_value=key,
                total_terminal_pickups=total,
                redeemed_pickups=redeemed_count,
                expired_pickups=expired_count,
                cancelled_pickups=cancelled_count,
                redemption_rate=_rate(redeemed_count, total),
                expiration_rate=_rate(expired_count, total),
                cancellation_rate=_rate(cancelled_count, total),
                avg_minutes_created_to_ready=created_to_ready.get(key),
                avg_minutes_ready_to_redeemed=ready_to_redeemed.get(key),
                avg_minutes_door_opened_to_redeemed=door_opened_to_redeemed.get(key),
                avg_minutes_door_opened_to_door_closed=door_opened_to_door_closed.get(key),
            )
        )

    items.sort(key=lambda item: (-item.total_terminal_pickups, item.dimension_value or ""))

    return PickupBreakdownResponse(
        dimension=dimension,
        window_start=start_at.isoformat() if start_at else None,
        window_end=end_at.isoformat() if end_at else None,
        items=items,
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