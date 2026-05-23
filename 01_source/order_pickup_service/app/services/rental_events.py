"""Auditoria de eventos do ciclo de vida de contratos de aluguel."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def log_rental_contract_event(
    db: Session,
    *,
    contract_id: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
    actor: str = "system",
) -> None:
    db.execute(
        text(
            """
            INSERT INTO rental_contract_events (id, contract_id, event_type, payload_json, actor, created_at)
            VALUES (:id, :contract_id, :event_type, :payload_json, :actor, :created_at)
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "contract_id": contract_id,
            "event_type": event_type,
            "payload_json": json.dumps(payload or {}),
            "actor": actor,
            "created_at": datetime.now(timezone.utc),
        },
    )
