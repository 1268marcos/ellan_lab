from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import LifecycleDeadlineListOut, OrderOpsAuditListOut
from app.services import orders_domain_service

router = APIRouter(tags=["order-lifecycle-ops"])


@router.get("/lifecycle-deadlines", response_model=LifecycleDeadlineListOut)
def list_lifecycle_deadlines(
    order_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    deadline_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> LifecycleDeadlineListOut:
    items, total = orders_domain_service.list_deadlines_orm(
        db,
        order_id=order_id,
        status=status,
        deadline_type=deadline_type,
        limit=limit,
        offset=offset,
    )
    return LifecycleDeadlineListOut(items=items, total=total)


@router.get("/ops-audit", response_model=OrderOpsAuditListOut)
def list_ops_audit(
    order_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> OrderOpsAuditListOut:
    items, total = orders_domain_service.list_audit(db, order_id=order_id, limit=limit, offset=offset)
    return OrderOpsAuditListOut(items=items, total=total)
