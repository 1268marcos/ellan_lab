# 01_source/order_pickup_service/app/core/lifecycle_integration.py
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.core.lifecycle_client import LifecycleClient, LifecycleClientError
from app.core.payment_timeout_policy import resolve_prepayment_timeout_seconds

from app.core.datetime_utils import to_iso_utc



logger = logging.getLogger(__name__)


def _as_utc_naive(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)

# existe outro def _resolve_deadline_at nesse código ????
def _resolve_deadline_at(
    *,
    created_at: datetime | None,
    region_code: str | None,
    order_channel: str,
    payment_method: str | None,
) -> str | None:
    base_created_at = _as_utc_naive(created_at)
    if base_created_at is None:
        return None

    timeout_sec = resolve_prepayment_timeout_seconds(
        region_code=region_code,
        order_channel=order_channel,
        payment_method=payment_method,
    )

    deadline_at = base_created_at + timedelta(seconds=int(timeout_sec))
    return deadline_at.isoformat()


def register_prepayment_timeout_deadline(
    *,
    order_id: str,
    order_channel: str,
    region_code: str | None,
    slot_id: str | None,
    machine_id: str | None,
    created_at: datetime | None,
    payment_method: str | None = None,
) -> None:
    client = LifecycleClient()

    deadline_at = _resolve_deadline_at(
        created_at=created_at,
        region_code=region_code,
        order_channel=order_channel,
        payment_method=payment_method,
    )

    try:
        result = client.create_prepayment_deadline(
            order_id=order_id,
            order_channel=order_channel,
            region_code=region_code,
            slot_id=slot_id,
            machine_id=machine_id,
            deadline_at=deadline_at,
            payment_method=payment_method,
        )
        logger.info(
            "lifecycle_deadline_registered",
            extra={
                "order_id": order_id,
                "order_channel": order_channel,
                "deadline_at": deadline_at,
                "result": result,
            },
        )
    except LifecycleClientError:
        logger.exception(
            "lifecycle_deadline_register_failed",
            extra={
                "order_id": order_id,
                "order_channel": order_channel,
                "region_code": region_code,
                "slot_id": slot_id,
                "machine_id": machine_id,
                "deadline_at": deadline_at,
                "payment_method": payment_method,
            },
        )
        raise


def cancel_prepayment_timeout_deadline(*, order_id: str) -> None:
    client = LifecycleClient()

    try:
        result = client.cancel_prepayment_deadline(order_id=order_id)
        logger.info(
            "lifecycle_deadline_cancelled",
            extra={
                "order_id": order_id,
                "result": result,
            },
        )
    except LifecycleClientError:
        logger.exception(
            "lifecycle_deadline_cancel_failed",
            extra={"order_id": order_id},
        )
        raise