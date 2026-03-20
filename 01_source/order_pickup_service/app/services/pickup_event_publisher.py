# 01_source/order_pickup_service/app/services/pickup_event_publisher.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.lifecycle_events_client import LifecycleEventsClient


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _event_key(event_type: str, pickup_id: str) -> str:
    return f"{event_type}:{pickup_id}"


class PickupEventPublisher:
    def __init__(self) -> None:
        self.client = LifecycleEventsClient()

    def publish(
        self,
        *,
        event_type: str,
        order_id: str,
        pickup_id: str,
        channel: str | None = None,
        region: str | None = None,
        locker_id: str | None = None,
        machine_id: str | None = None,
        slot: str | None = None,
        operator_id: str | None = None,
        tenant_id: str | None = None,
        site_id: str | None = None,
        correlation_id: str | None = None,
        payload: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
    ) -> dict:
        return self.client.publish_pickup_event(
            event_key=_event_key(event_type, pickup_id),
            event_type=event_type,
            occurred_at=occurred_at or _utc_now(),
            order_id=order_id,
            pickup_id=pickup_id,
            channel=channel,
            region=region,
            locker_id=locker_id,
            machine_id=machine_id,
            slot=slot,
            operator_id=operator_id,
            tenant_id=tenant_id,
            site_id=site_id,
            correlation_id=correlation_id,
            payload=payload or {},
        )


publisher = PickupEventPublisher()


def publish_pickup_created(**kwargs):
    return publisher.publish(event_type="pickup.created", **kwargs)


def publish_pickup_ready(**kwargs):
    return publisher.publish(event_type="pickup.ready_for_pickup", **kwargs)


def publish_pickup_door_opened(**kwargs):
    return publisher.publish(event_type="pickup.door_opened", **kwargs)


def publish_pickup_item_removed(**kwargs):
    return publisher.publish(event_type="pickup.item_removed", **kwargs)


def publish_pickup_door_closed(**kwargs):
    return publisher.publish(event_type="pickup.door_closed", **kwargs)


def publish_pickup_redeemed(**kwargs):
    return publisher.publish(event_type="pickup.redeemed", **kwargs)


def publish_pickup_expired(**kwargs):
    return publisher.publish(event_type="pickup.expired", **kwargs)


def publish_pickup_cancelled(**kwargs):
    return publisher.publish(event_type="pickup.cancelled", **kwargs)