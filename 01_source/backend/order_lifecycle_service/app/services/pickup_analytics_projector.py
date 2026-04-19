# 01_source/backend/order_lifecycle_service/app/services/pickup_analytics_projector.py
# 19/04/2026 - datetime

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.lifecycle import AnalyticsFact, DomainEvent

from app.core.datetime_utils import to_iso_utc



def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _minutes_between(start: datetime | None, end: datetime | None) -> float | None:
    start = _as_utc(start)
    end = _as_utc(end)
    if start is None or end is None:
        return None
    seconds = (end - start).total_seconds()
    if seconds < 0:
        return None
    return round(seconds / 60.0, 3)


def _safe_payload_value(payload: dict, key: str):
    return (payload or {}).get(key)


def _insert_fact_if_missing(
    db: Session,
    *,
    fact_key: str,
    fact_name: str,
    order_id: str,
    order_channel: str | None,
    region_code: str | None,
    slot_id: str | None,
    occurred_at: datetime,
    payload: dict,
) -> bool:
    existing = (
        db.query(AnalyticsFact)
        .filter(AnalyticsFact.fact_key == fact_key)
        .first()
    )
    if existing:
        return False

    now = datetime.now(timezone.utc)

    fact = AnalyticsFact(
        fact_key=fact_key,
        fact_name=fact_name,
        order_id=order_id,
        order_channel=order_channel,
        region_code=region_code,
        slot_id=slot_id,
        payload=payload,
        occurred_at=occurred_at,
        created_at=now,
    )
    db.add(fact)
    return True


def _load_pickup_event_map(db: Session, *, pickup_id: str) -> dict[str, DomainEvent]:
    rows = (
        db.query(DomainEvent)
        .filter(DomainEvent.aggregate_type == "pickup")
        .filter(DomainEvent.aggregate_id == pickup_id)
        .order_by(DomainEvent.occurred_at.asc())
        .all()
    )

    event_map: dict[str, DomainEvent] = {}
    for row in rows:
        event_map.setdefault(row.event_name, row)
    return event_map


def project_pickup_event_facts(
    db: Session,
    *,
    event: DomainEvent,
) -> None:
    payload = event.payload or {}

    order_id = str(payload.get("order_id") or "")
    pickup_id = str(payload.get("pickup_id") or event.aggregate_id or "")
    channel = payload.get("channel")
    region = payload.get("region")
    slot = payload.get("slot")

    base_payload = {
        "event_key": event.event_key,
        "event_name": event.event_name,
        "order_id": order_id,
        "pickup_id": pickup_id,
        "channel": channel,
        "region": region,
        "locker_id": payload.get("locker_id"),
        "machine_id": payload.get("machine_id"),
        "slot": slot,
        "operator_id": payload.get("operator_id"),
        "tenant_id": payload.get("tenant_id"),
        "site_id": payload.get("site_id"),
        "correlation_id": payload.get("correlation_id"),
        "source_service": payload.get("source_service"),
    }

    _insert_fact_if_missing(
        db,
        fact_key=f"pickup_event:{event.event_key}",
        fact_name="pickup_event",
        order_id=order_id,
        order_channel=channel,
        region_code=region,
        slot_id=slot,
        occurred_at=event.occurred_at,
        payload={
            **base_payload,
            "occurred_at": to_iso_utc(event.occurred_at),
        },
    )

    if event.event_name in {"pickup.redeemed", "pickup.expired", "pickup.cancelled"}:
        terminal_state = event.event_name.removeprefix("pickup.")

        _insert_fact_if_missing(
            db,
            fact_key=f"pickup_terminal_state:{event.event_key}",
            fact_name="pickup_terminal_state",
            order_id=order_id,
            order_channel=channel,
            region_code=region,
            slot_id=slot,
            occurred_at=event.occurred_at,
            payload={
                **base_payload,
                "terminal_state": terminal_state,
                "occurred_at": to_iso_utc(event.occurred_at),
            },
        )

    event_map = _load_pickup_event_map(db, pickup_id=pickup_id)

    created_at = getattr(event_map.get("pickup.created"), "occurred_at", None)
    ready_at = getattr(event_map.get("pickup.ready_for_pickup"), "occurred_at", None)
    door_opened_at = getattr(event_map.get("pickup.door_opened"), "occurred_at", None)
    door_closed_at = getattr(event_map.get("pickup.door_closed"), "occurred_at", None)
    redeemed_at = getattr(event_map.get("pickup.redeemed"), "occurred_at", None)

    created_to_ready = _minutes_between(created_at, ready_at)
    if created_to_ready is not None:
        _insert_fact_if_missing(
            db,
            fact_key=f"pickup_sla_created_to_ready:{pickup_id}",
            fact_name="pickup_sla_created_to_ready",
            order_id=order_id,
            order_channel=channel,
            region_code=region,
            slot_id=slot,
            occurred_at=ready_at,
            payload={
                **base_payload,
                "pickup_id": pickup_id,
                "minutes": created_to_ready,
                "started_at": to_iso_utc(created_at),
                "ended_at": to_iso_utc(ready_at),
            },
        )

    ready_to_redeemed = _minutes_between(ready_at, redeemed_at)
    if ready_to_redeemed is not None:
        _insert_fact_if_missing(
            db,
            fact_key=f"pickup_sla_ready_to_redeemed:{pickup_id}",
            fact_name="pickup_sla_ready_to_redeemed",
            order_id=order_id,
            order_channel=channel,
            region_code=region,
            slot_id=slot,
            occurred_at=redeemed_at,
            payload={
                **base_payload,
                "pickup_id": pickup_id,
                "minutes": ready_to_redeemed,
                "started_at": to_iso_utc(ready_at),
                "ended_at": to_iso_utc(redeemed_at),
            },
        )

    door_opened_to_redeemed = _minutes_between(door_opened_at, redeemed_at)
    if door_opened_to_redeemed is not None:
        _insert_fact_if_missing(
            db,
            fact_key=f"pickup_sla_door_opened_to_redeemed:{pickup_id}",
            fact_name="pickup_sla_door_opened_to_redeemed",
            order_id=order_id,
            order_channel=channel,
            region_code=region,
            slot_id=slot,
            occurred_at=redeemed_at,
            payload={
                **base_payload,
                "pickup_id": pickup_id,
                "minutes": door_opened_to_redeemed,
                "started_at": to_iso_utc(door_opened_at),
                "ended_at": to_iso_utc(redeemed_at),
            },
        )

    door_opened_to_door_closed = _minutes_between(door_opened_at, door_closed_at)
    if door_opened_to_door_closed is not None:
        _insert_fact_if_missing(
            db,
            fact_key=f"pickup_sla_door_opened_to_door_closed:{pickup_id}",
            fact_name="pickup_sla_door_opened_to_door_closed",
            order_id=order_id,
            order_channel=channel,
            region_code=region,
            slot_id=slot,
            occurred_at=door_closed_at,
            payload={
                **base_payload,
                "pickup_id": pickup_id,
                "minutes": door_opened_to_door_closed,
                "started_at": to_iso_utc(door_opened_at),
                "ended_at": to_iso_utc(door_closed_at),
            },
        )