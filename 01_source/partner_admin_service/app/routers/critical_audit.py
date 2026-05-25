from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.critical_table_context import get_actor_context
from app.core.database import get_db
from app.services import audit_log_service
from shared.security.critical_table_guard import ActorContext

router = APIRouter(prefix="/critical-audit-logs", tags=["critical-audit-logs"])


class PublicAuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_id: str | None
    actor_role: str | None
    action: str
    target_type: str
    target_id: str
    occurred_at: object
    source_service: str | None


class PublicAuditLogListOut(BaseModel):
    items: list[PublicAuditLogOut]
    total: int


@router.get("", response_model=PublicAuditLogListOut)
def list_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
) -> PublicAuditLogListOut:
    rows = audit_log_service.list_public_audit_logs(db, actor=actor, limit=limit)
    items = [PublicAuditLogOut.model_validate(r) for r in rows]
    return PublicAuditLogListOut(items=items, total=len(items))
