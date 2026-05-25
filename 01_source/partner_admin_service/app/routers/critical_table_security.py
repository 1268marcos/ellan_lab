from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.critical_table_context import get_actor_context
from app.core.database import get_db
from app.models.critical_table_security import (
    AppCriticalTableAccessLog,
    AppCriticalTablePolicy,
    AppCriticalTableRegistry,
)
from app.services.critical_table_security_service import enforce
from shared.security.critical_table_guard import ActorContext

router = APIRouter(prefix="/critical-table-security", tags=["critical-table-security"])


class RegistryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    table_name: str
    schema_name: str
    rls_enabled: bool
    enforcement_layer: str
    description: str | None


class PolicyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    table_name: str
    operation: str
    role: str
    scope_type: str
    allowed: bool
    priority: int


class AccessLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    table_name: str
    operation: str
    actor_id: str | None
    target_user_id: str | None
    decision: str
    reason: str | None
    service_name: str | None
    occurred_at: object


class RegistryListOut(BaseModel):
    items: list[RegistryOut]
    total: int


class PolicyListOut(BaseModel):
    items: list[PolicyOut]
    total: int


class AccessLogListOut(BaseModel):
    items: list[AccessLogOut]
    total: int


@router.get("/registry", response_model=RegistryListOut)
def list_registry(
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
) -> RegistryListOut:
    enforce(db, table_name="users", operation="SELECT", actor=actor)
    rows = db.query(AppCriticalTableRegistry).order_by(AppCriticalTableRegistry.table_name).all()
    items = [RegistryOut.model_validate(r) for r in rows]
    return RegistryListOut(items=items, total=len(items))


@router.get("/policies", response_model=PolicyListOut)
def list_policies(
    table_name: str | None = Query(None),
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
) -> PolicyListOut:
    enforce(db, table_name="users", operation="SELECT", actor=actor)
    q = db.query(AppCriticalTablePolicy).filter(AppCriticalTablePolicy.is_active.is_(True))
    if table_name:
        q = q.filter(AppCriticalTablePolicy.table_name == table_name)
    rows = q.order_by(
        AppCriticalTablePolicy.table_name,
        AppCriticalTablePolicy.operation,
        AppCriticalTablePolicy.priority,
    ).all()
    items = [PolicyOut.model_validate(r) for r in rows]
    return PolicyListOut(items=items, total=len(items))


@router.get("/access-log", response_model=AccessLogListOut)
def list_access_log(
    table_name: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: ActorContext = Depends(get_actor_context),
) -> AccessLogListOut:
    enforce(db, table_name="audit_logs", operation="SELECT", actor=actor)
    q = db.query(AppCriticalTableAccessLog)
    if table_name:
        q = q.filter(AppCriticalTableAccessLog.table_name == table_name)
    rows = q.order_by(AppCriticalTableAccessLog.occurred_at.desc()).limit(limit).all()
    items = [AccessLogOut.model_validate(r) for r in rows]
    return AccessLogListOut(items=items, total=len(items))
