from __future__ import annotations

import logging
from datetime import datetime

from app.core.lifecycle_client import LifecycleClient, LifecycleClientError

logger = logging.getLogger(__name__)


def register_prepayment_timeout_deadline(
    *,
    order_id: str,
    order_channel: str,
    region_code: str | None,
    slot_id: str | None,
    machine_id: str | None,
    created_at: datetime | None,
) -> None:
    client = LifecycleClient()

    try:
        result = client.create_prepayment_deadline(
            order_id=order_id,
            order_channel=order_channel,
            region_code=region_code,
            slot_id=slot_id,
            machine_id=machine_id,
            created_at=created_at,
        )
        logger.info(
            "lifecycle_deadline_registered",
            extra={
                "order_id": order_id,
                "order_channel": order_channel,
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