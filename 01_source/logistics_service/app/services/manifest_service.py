from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.integrations import backend_runtime, order_lifecycle
from app.kafka_events import emit_manifest_created
from app.services import logistics_service


def create_manifest_with_events(
    db: Session,
    shipments: list[dict[str, Any]],
    locker_id: str,
    status: str = "draft",
    *,
    http_client: httpx.Client | None = None,
) -> tuple[Any, dict[str, Any], dict[str, Any]]:
    locker = backend_runtime.get_locker_status(locker_id, http_client)
    if not locker.get("ok"):
        raise ValueError("locker_unreachable")
    sla = order_lifecycle.fetch_sla_deadlines(http_client)
    m = logistics_service.create_manifest(db, shipments, locker_id, status)
    emit_manifest_created(m.id, locker_id, m.status)
    return m, locker, sla
