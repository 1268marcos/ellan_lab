from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.ecosystem import CapabilityProfileAuditLog
from app.services.crypto_util import new_id


def log_audit(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    profile_id: int | None = None,
    actor: str | None = None,
    payload: dict | None = None,
) -> CapabilityProfileAuditLog:
    row = CapabilityProfileAuditLog(
        id=new_id(),
        profile_id=profile_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor=actor,
        payload_json=payload or {},
    )
    db.add(row)
    db.flush()
    return row
