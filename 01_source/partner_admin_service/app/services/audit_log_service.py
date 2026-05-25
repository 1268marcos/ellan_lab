from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.services.critical_table_security_service import enforce
from app.services.crypto_util import new_id
from shared.security.critical_table_guard import ActorContext


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def write_public_audit(
    db: Session,
    *,
    actor: ActorContext,
    action: str,
    target_type: str,
    target_id: str,
    actor_role: str | None = None,
    old_state: dict | None = None,
    new_state: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    enforce(db, table_name="audit_logs", operation="INSERT", actor=actor)
    row = AuditLog(
        id=new_id(),
        actor_id=actor.actor_id,
        actor_role=actor_role,
        action=action,
        target_type=target_type,
        target_id=target_id,
        old_state=old_state,
        new_state=new_state,
        ip_address=ip_address,
        user_agent=user_agent,
        occurred_at=_utcnow(),
        source_service=actor.service_name or "partner_admin_service",
        immutable=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_public_audit_logs(db: Session, *, actor: ActorContext, limit: int = 100) -> list[AuditLog]:
    enforce(db, table_name="audit_logs", operation="SELECT", actor=actor)
    return db.query(AuditLog).order_by(AuditLog.occurred_at.desc()).limit(limit).all()
