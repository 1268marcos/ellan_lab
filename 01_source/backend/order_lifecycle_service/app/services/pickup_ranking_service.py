# 01_source/backend/order_lifecycle_service/app/services/pickup_ranking_service.py
# 19/04/2026 - datetime

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Numeric, func
from sqlalchemy.orm import Query, Session

from app.models.lifecycle import AnalyticsFact
from app.schemas.analytics_ranking import PickupRankingItem, PickupRankingResponse

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

_ALLOWED_CATEGORIES = {
    "exception",
    "efficiency",
    "volume",
    "risk",
    "trend",
    "positive",
    "saturation",
    "reliability",
}

_ALLOWED_METRICS = {
    "terminal_volume",
    "redeemed_volume",
    "expired_volume",
    "cancelled_volume",
    "redemption_rate",
    "expiration_rate",
    "cancellation_rate",
    "avg_minutes_created_to_ready",
    "avg_minutes_ready_to_redeemed",
    "avg_minutes_door_opened_to_redeemed",
    "avg_minutes_door_opened_to_door_closed",
}

_METRIC_TO_FACT = {
    "avg_minutes_created_to_ready": "pickup_sla_created_to_ready",
    "avg_minutes_ready_to_redeemed": "pickup_sla_ready_to_redeemed",
    "avg_minutes_door_opened_to_redeemed": "pickup_sla_door_opened_to_redeemed",
    "avg_minutes_door_opened_to_door_closed": "pickup_sla_door_opened_to_door_closed",
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


def _grouped_terminal_counts(
    db: Session,
    *,
    dimension: str,
    terminal_state: str | None,
    **filters: Any,
) -> dict[str | None, int]:
    dim = _dimension_expr(dimension)

    query = db.query(
        dim.label("dimension_value"),
        func.count(AnalyticsFact.id).label("count_value"),
    ).filter(
        AnalyticsFact.fact_name == "pickup_terminal_state",
    )

    if terminal_state is not None:
        query = query.filter(
            AnalyticsFact.payload["terminal_state"].astext == terminal_state
        )

    query = _apply_filters(query, **filters)
    query = query.group_by(dim)

    return {row.dimension_value: int(row.count_value) for row in query.all()}


def _grouped_avg_minutes(
    db: Session,
    *,
    dimension: str,
    fact_name: str,
    **filters: Any,
) -> dict[str | None, float | None]:
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


def _rate(value: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((value / total) * 100.0, 3)


def _default_direction_for_metric(metric: str) -> str:
    if metric in {
        "terminal_volume",
        "redeemed_volume",
        "expired_volume",
        "cancelled_volume",
        "expiration_rate",
        "cancellation_rate",
        "avg_minutes_created_to_ready",
        "avg_minutes_ready_to_redeemed",
        "avg_minutes_door_opened_to_redeemed",
        "avg_minutes_door_opened_to_door_closed",
    }:
        return "desc"

    if metric in {
        "redemption_rate",
    }:
        return "asc"

    return "desc"


def build_pickup_ranking(
    db: Session,
    *,
    category: str,
    metric: str,
    dimension: str,
    limit: int = 10,
    direction: str | None = None,
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
) -> PickupRankingResponse:
    if category not in _ALLOWED_CATEGORIES:
        raise ValueError(f"unsupported category: {category}")

    if metric not in _ALLOWED_METRICS:
        raise ValueError(f"unsupported metric: {metric}")

    if dimension not in _ALLOWED_DIMENSIONS:
        raise ValueError(f"unsupported dimension: {dimension}")

    if limit <= 0:
        raise ValueError("limit must be greater than zero")

    if direction is None:
        direction = _default_direction_for_metric(metric)

    if direction not in {"asc", "desc"}:
        raise ValueError("direction must be asc or desc")

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

    total_terminal = _grouped_terminal_counts(db, dimension=dimension, terminal_state=None, **filters)
    redeemed = _grouped_terminal_counts(db, dimension=dimension, terminal_state="redeemed", **filters)
    expired = _grouped_terminal_counts(db, dimension=dimension, terminal_state="expired", **filters)
    cancelled = _grouped_terminal_counts(db, dimension=dimension, terminal_state="cancelled", **filters)

    created_to_ready = _grouped_avg_minutes(
        db,
        dimension=dimension,
        fact_name=_METRIC_TO_FACT["avg_minutes_created_to_ready"],
        **filters,
    )
    ready_to_redeemed = _grouped_avg_minutes(
        db,
        dimension=dimension,
        fact_name=_METRIC_TO_FACT["avg_minutes_ready_to_redeemed"],
        **filters,
    )
    door_opened_to_redeemed = _grouped_avg_minutes(
        db,
        dimension=dimension,
        fact_name=_METRIC_TO_FACT["avg_minutes_door_opened_to_redeemed"],
        **filters,
    )
    door_opened_to_door_closed = _grouped_avg_minutes(
        db,
        dimension=dimension,
        fact_name=_METRIC_TO_FACT["avg_minutes_door_opened_to_door_closed"],
        **filters,
    )

    keys = set()
    keys.update(total_terminal.keys())
    keys.update(redeemed.keys())
    keys.update(expired.keys())
    keys.update(cancelled.keys())
    keys.update(created_to_ready.keys())
    keys.update(ready_to_redeemed.keys())
    keys.update(door_opened_to_redeemed.keys())
    keys.update(door_opened_to_door_closed.keys())

    items: list[PickupRankingItem] = []

    for key in keys:
        total = int(total_terminal.get(key, 0))
        redeemed_count = int(redeemed.get(key, 0))
        expired_count = int(expired.get(key, 0))
        cancelled_count = int(cancelled.get(key, 0))

        redemption_rate = _rate(redeemed_count, total)
        expiration_rate = _rate(expired_count, total)
        cancellation_rate = _rate(cancelled_count, total)

        avg_created_to_ready = created_to_ready.get(key)
        avg_ready_to_redeemed = ready_to_redeemed.get(key)
        avg_door_opened_to_redeemed = door_opened_to_redeemed.get(key)
        avg_door_opened_to_door_closed = door_opened_to_door_closed.get(key)

        metric_value_map = {
            "terminal_volume": float(total),
            "redeemed_volume": float(redeemed_count),
            "expired_volume": float(expired_count),
            "cancelled_volume": float(cancelled_count),
            "redemption_rate": float(redemption_rate),
            "expiration_rate": float(expiration_rate),
            "cancellation_rate": float(cancellation_rate),
            "avg_minutes_created_to_ready": float(avg_created_to_ready or 0.0),
            "avg_minutes_ready_to_redeemed": float(avg_ready_to_redeemed or 0.0),
            "avg_minutes_door_opened_to_redeemed": float(avg_door_opened_to_redeemed or 0.0),
            "avg_minutes_door_opened_to_door_closed": float(avg_door_opened_to_door_closed or 0.0),
        }

        metric_value = round(metric_value_map[metric], 3)

        if metric.startswith("avg_minutes_"):
            source_avg = {
                "avg_minutes_created_to_ready": avg_created_to_ready,
                "avg_minutes_ready_to_redeemed": avg_ready_to_redeemed,
                "avg_minutes_door_opened_to_redeemed": avg_door_opened_to_redeemed,
                "avg_minutes_door_opened_to_door_closed": avg_door_opened_to_door_closed,
            }[metric]
            if source_avg is None:
                continue

        items.append(
            PickupRankingItem(
                rank=0,
                dimension_value=key,
                metric=metric,
                metric_value=metric_value,
                total_terminal_pickups=total,
                redeemed_pickups=redeemed_count,
                expired_pickups=expired_count,
                cancelled_pickups=cancelled_count,
                redemption_rate=redemption_rate,
                expiration_rate=expiration_rate,
                cancellation_rate=cancellation_rate,
                avg_minutes_created_to_ready=avg_created_to_ready,
                avg_minutes_ready_to_redeemed=avg_ready_to_redeemed,
                avg_minutes_door_opened_to_redeemed=avg_door_opened_to_redeemed,
                avg_minutes_door_opened_to_door_closed=avg_door_opened_to_door_closed,
            )
        )

    reverse = direction == "desc"
    items.sort(
        key=lambda item: (
            item.metric_value,
            item.total_terminal_pickups,
            item.dimension_value or "",
        ),
        reverse=reverse,
    )

    items = items[:limit]

    ranked_items: list[PickupRankingItem] = []
    for idx, item in enumerate(items, start=1):
        item.rank = idx
        ranked_items.append(item)

    return PickupRankingResponse(
        category=category,
        metric=metric,
        dimension=dimension,
        direction=direction,
        limit=limit,
        window_start=to_iso_utc(start_at),
        window_end=to_iso_utc(end_at),
        items=ranked_items,
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


def resolve_equipment_bundle_for_slot(
    db: Session,
    *,
    slot_id: str,
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
) -> dict[str, str | None]:
    """
    Para ranking por slot_id: retorna o trio (locker_id, machine_id, site_id) mais frequente
    nos fatos pickup_terminal_state do periodo (mesmos filtros do ranking).
    """
    if not slot_id:
        return {"locker_id": None, "machine_id": None, "site_id": None}

    locker_expr = AnalyticsFact.payload["locker_id"].astext
    machine_expr = AnalyticsFact.payload["machine_id"].astext
    site_expr = AnalyticsFact.payload["site_id"].astext
    cnt = func.count(AnalyticsFact.id).label("cnt")

    query = (
        db.query(
            locker_expr.label("locker_id"),
            machine_expr.label("machine_id"),
            site_expr.label("site_id"),
            cnt,
        )
        .filter(AnalyticsFact.fact_name == "pickup_terminal_state")
        .filter(AnalyticsFact.slot_id == slot_id)
    )

    query = _apply_filters(
        query,
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

    query = query.group_by(locker_expr, machine_expr, site_expr).order_by(cnt.desc())

    row = query.first()
    if row is None:
        return {"locker_id": None, "machine_id": None, "site_id": None}

    return {
        "locker_id": (str(row.locker_id).strip() if row.locker_id else None) or None,
        "machine_id": (str(row.machine_id).strip() if row.machine_id else None) or None,
        "site_id": (str(row.site_id).strip() if row.site_id else None) or None,
    }

