# 01_source/order_pickup_service/app/routers/notifications.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth_dep import require_user_roles
from app.core.db import get_db
from app.models.notification_log import NotificationLog

_OPS = {"admin_operacao", "auditoria", "suporte"}

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    dependencies=[Depends(require_user_roles(allowed_roles=_OPS))],
)

# Filtro OPS: PENDING ≈ fila+processamento; SENT = enviado; FAILED = falha (incl. DEAD para diagnóstico)
_STATUS_FILTER = {
    "PENDING": ("QUEUED", "PROCESSING"),
    "SENT": ("SENT",),
    "FAILED": ("FAILED", "DEAD"),
}


def _parse_range_date(raw: str | None, *, end_of_day: bool) -> datetime | None:
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip()
    try:
        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
            if end_of_day:
                return datetime(y, m, d, 23, 59, 59)
            return datetime(y, m, d, 0, 0, 0)
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except ValueError:
        raise HTTPException(422, "date_from/date_to inválido (use YYYY-MM-DD ou ISO-8601)")


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _row_out(r: NotificationLog) -> dict[str, Any]:
    return {
        "id": r.id,
        "user_id": r.user_id,
        "order_id": r.order_id,
        "channel": r.channel,
        "template_key": r.template_key,
        "status": r.status,
        "attempt_count": r.attempt_count,
        "error_message": r.error_message,
        "sent_at": _iso(r.sent_at),
        "delivered_at": _iso(r.delivered_at),
        "provider_message_id": r.provider_message_id,
        "provider_status": r.provider_status,
        "created_at": _iso(r.created_at),
        "destination_masked": r.destination_masked,
    }


@router.get("/logs")
def list_notification_logs(
    db: Session = Depends(get_db),
    status: str | None = Query(None, description="PENDING | SENT | FAILED"),
    channel: str | None = Query(None, description="EMAIL | SMS | PUSH"),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    q = db.query(NotificationLog)
    if status:
        key = status.strip().upper()
        bucket = _STATUS_FILTER.get(key)
        if not bucket:
            raise HTTPException(400, "status deve ser PENDING, SENT ou FAILED")
        q = q.filter(NotificationLog.status.in_(bucket))
    if channel:
        q = q.filter(NotificationLog.channel == channel.strip().upper())
    if date_from:
        q = q.filter(NotificationLog.created_at >= _parse_range_date(date_from, end_of_day=False))
    if date_to:
        q = q.filter(NotificationLog.created_at <= _parse_range_date(date_to, end_of_day=True))
    total = q.count()
    rows = (
        q.order_by(NotificationLog.created_at.desc(), NotificationLog.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"total": total, "limit": limit, "offset": offset, "items": [_row_out(r) for r in rows]}


@router.post("/logs/{log_id}/retry")
def retry_notification_log(log_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    item = db.get(NotificationLog, log_id)
    if item is None:
        raise HTTPException(404, "notification log não encontrado")
    if item.status != "FAILED":
        raise HTTPException(400, "reenvio manual permitido apenas para status FAILED")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    item.status = "QUEUED"
    item.next_attempt_at = now
    item.processing_started_at = None
    item.error_message = None
    item.failed_at = None
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"ok": True, "id": item.id, "status": item.status, "next_attempt_at": _iso(item.next_attempt_at)}
