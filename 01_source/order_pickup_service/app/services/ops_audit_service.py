from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.ops_action_audit import OpsActionAudit

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def record_ops_action_audit(
    *,
    db: Session,
    action: str,
    result: str,
    correlation_id: str,
    user_id: str | None = None,
    role: str | None = None,
    order_id: str | None = None,
    error_message: str | None = None,
    details: dict | None = None,
) -> OpsActionAudit:
    row = OpsActionAudit(
        id=f"oaa_{uuid4().hex}",
        action=str(action or "").strip() or "UNKNOWN_ACTION",
        result=str(result or "").strip().upper() or "UNKNOWN",
        correlation_id=str(correlation_id or "").strip() or f"corr-{uuid4().hex}",
        user_id=str(user_id).strip() if user_id else None,
        role=str(role).strip() if role else None,
        order_id=str(order_id).strip() if order_id else None,
        error_message=(str(error_message)[:4000] if error_message else None),
        details_json=details or {},
        created_at=_utc_now(),
    )
    db.add(row)
    db.flush()
    return row


def list_ops_action_audit(
    *,
    db: Session,
    limit: int = 50,
    offset: int = 0,
    order_id: str | None = None,
    action: str | None = None,
    result: str | None = None,
) -> list[OpsActionAudit]:
    q = db.query(OpsActionAudit)
    if order_id:
        q = q.filter(OpsActionAudit.order_id == str(order_id).strip())
    if action:
        q = q.filter(OpsActionAudit.action == str(action).strip())
    if result:
        q = q.filter(OpsActionAudit.result == str(result).strip().upper())
    return (
        q.order_by(OpsActionAudit.created_at.desc(), OpsActionAudit.id.desc())
        .offset(max(int(offset or 0), 0))
        .limit(max(min(int(limit or 50), 200), 1))
        .all()
    )
