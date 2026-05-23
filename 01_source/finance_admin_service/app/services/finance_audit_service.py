from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.finance_advanced import FinanceAuditLog
from app.services.crypto_util import new_id


def log_audit(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: str,
    before: Any = None,
    after: Any = None,
    actor_id: str = "system",
) -> FinanceAuditLog:
    row = FinanceAuditLog(
        id=new_id(),
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=json.dumps(before or {}, default=str),
        after_json=json.dumps(after or {}, default=str),
    )
    db.add(row)
    return row


def list_audit_log(
    db: Session,
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
    limit: int = 200,
) -> list[FinanceAuditLog]:
    q = db.query(FinanceAuditLog).order_by(FinanceAuditLog.created_at.desc())
    if entity_type:
        q = q.filter(FinanceAuditLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(FinanceAuditLog.entity_id == entity_id)
    return q.limit(limit).all()
