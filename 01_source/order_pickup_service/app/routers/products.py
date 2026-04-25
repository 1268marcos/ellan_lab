from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_user, require_user_roles
from app.core.db import get_db
from app.models.product_status_history import ProductStatusHistory
from app.models.user import User
from app.schemas.products import (
    ProductStatusHistoryItemOut,
    ProductStatusHistoryListOut,
    ProductStatusOut,
    ProductStatusTransitionIn,
)

router = APIRouter(
    prefix="/products",
    tags=["products"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao", "auditoria"}))],
)

_PRODUCT_STATUSES = {"DRAFT", "ACTIVE", "INACTIVE", "DISCONTINUED"}
_ALLOWED_PRODUCT_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"ACTIVE", "DISCONTINUED"},
    "ACTIVE": {"INACTIVE", "DISCONTINUED"},
    "INACTIVE": {"ACTIVE", "DISCONTINUED"},
    "DISCONTINUED": set(),
}


def _to_iso_utc(value: datetime | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _load_product_status(db: Session, product_id: str) -> str:
    row = db.execute(
        text("SELECT id, COALESCE(status, 'DRAFT') AS status FROM products WHERE id = :id"),
        {"id": product_id},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "PRODUCT_NOT_FOUND",
                "message": "Produto não encontrado.",
                "product_id": product_id,
            },
        )
    return str(row.get("status") or "DRAFT").strip().upper()


@router.patch("/{product_id}/status", response_model=ProductStatusOut)
def patch_product_status(
    product_id: str,
    payload: ProductStatusTransitionIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    to_status = str(payload.to_status or "").strip().upper()
    if to_status not in _PRODUCT_STATUSES:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_PRODUCT_STATUS",
                "message": "Status inválido para produto.",
                "allowed_statuses": sorted(_PRODUCT_STATUSES),
            },
        )

    from_status = _load_product_status(db, product_id=product_id)
    if from_status == to_status:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "STATUS_UNCHANGED",
                "message": "O produto já está nesse status.",
                "status": to_status,
            },
        )

    allowed_targets = _ALLOWED_PRODUCT_TRANSITIONS.get(from_status, set())
    if to_status not in allowed_targets:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_STATUS_TRANSITION",
                "message": "Transição de status não permitida para produto.",
                "from_status": from_status,
                "to_status": to_status,
                "allowed_targets": sorted(allowed_targets),
            },
        )

    db.execute(
        text(
            """
            UPDATE products
            SET status = :status,
                updated_at = NOW()
            WHERE id = :id
            """
        ),
        {"id": product_id, "status": to_status},
    )

    changed_at = datetime.now(timezone.utc)
    history_row = ProductStatusHistory(
        id=str(uuid4()),
        product_id=product_id,
        from_status=from_status,
        to_status=to_status,
        reason=(payload.reason.strip() if payload.reason else None),
        changed_by=str(current_user.id) if current_user and current_user.id else None,
        changed_at=changed_at,
    )
    db.add(history_row)
    db.commit()

    return ProductStatusOut(
        ok=True,
        product_id=product_id,
        from_status=from_status,
        to_status=to_status,
        changed_by=history_row.changed_by,
        changed_at=_to_iso_utc(changed_at),
    )


@router.get("/{product_id}/status-history", response_model=ProductStatusHistoryListOut)
def get_product_status_history(
    product_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    _load_product_status(db, product_id=product_id)

    rows = (
        db.query(ProductStatusHistory)
        .filter(ProductStatusHistory.product_id == product_id)
        .order_by(ProductStatusHistory.changed_at.desc(), ProductStatusHistory.id.desc())
        .limit(limit)
        .all()
    )

    items = [
        ProductStatusHistoryItemOut(
            id=row.id,
            product_id=row.product_id,
            from_status=row.from_status,
            to_status=row.to_status,
            reason=row.reason,
            changed_by=row.changed_by,
            changed_at=_to_iso_utc(row.changed_at),
        )
        for row in rows
    ]
    return ProductStatusHistoryListOut(ok=True, total=len(items), items=items)
