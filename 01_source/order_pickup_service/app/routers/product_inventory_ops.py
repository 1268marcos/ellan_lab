from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dep import require_user_roles
from app.core.db import get_db
from pydantic import BaseModel, Field

router = APIRouter(
    tags=["product-inventory-ops"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao", "auditoria"}))],
)


def _to_iso(value: object) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


class ProductInventoryRowOut(BaseModel):
    id: str
    product_id: str
    locker_id: str
    slot_size: str
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    reorder_point: int
    reorder_quantity: int
    updated_at: str


class ProductInventoryListOut(BaseModel):
    ok: bool
    total: int
    items: list[ProductInventoryRowOut]


class ReservationHealthItemOut(BaseModel):
    status: str
    count: int


class ReservationHealthOut(BaseModel):
    ok: bool
    period_from: str | None = None
    period_to: str | None = None
    total: int
    by_status: list[ReservationHealthItemOut]
    items: list[dict]


@router.get("/ops/products/inventory", response_model=ProductInventoryListOut)
def list_product_inventory_ops(
    product_id: str | None = None,
    locker_id: str | None = None,
    low_stock_only: bool = False,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    cond, params = ["1=1"], {"limit": limit, "offset": offset}
    if product_id:
        cond.append("product_id = :product_id")
        params["product_id"] = product_id.strip()
    if locker_id:
        cond.append("locker_id = :locker_id")
        params["locker_id"] = locker_id.strip()
    if low_stock_only:
        cond.append("quantity_available <= reorder_point")
    total = int(
        db.execute(text(f"SELECT COUNT(*) FROM product_inventory WHERE {' AND '.join(cond)}"), params).scalar() or 0
    )
    rows = db.execute(
        text(
            f"""
            SELECT id, product_id, locker_id, slot_size,
                   quantity_on_hand, quantity_reserved, quantity_available,
                   reorder_point, reorder_quantity, updated_at
            FROM product_inventory
            WHERE {' AND '.join(cond)}
            ORDER BY quantity_available ASC, updated_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    items = [
        ProductInventoryRowOut(
            id=str(r["id"]),
            product_id=str(r["product_id"]),
            locker_id=str(r["locker_id"]),
            slot_size=str(r["slot_size"]),
            quantity_on_hand=int(r.get("quantity_on_hand") or 0),
            quantity_reserved=int(r.get("quantity_reserved") or 0),
            quantity_available=int(r.get("quantity_available") or 0),
            reorder_point=int(r.get("reorder_point") or 0),
            reorder_quantity=int(r.get("reorder_quantity") or 0),
            updated_at=_to_iso(r.get("updated_at")),
        )
        for r in rows
    ]
    return ProductInventoryListOut(ok=True, total=total, items=items)


@router.get("/ops/inventory/reservation-health", response_model=ReservationHealthOut)
def reservation_health_ops(
    period_from: str | None = None,
    period_to: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    cond, params = ["1=1"], {"limit": limit}
    if period_from:
        cond.append("created_at >= :period_from")
        params["period_from"] = period_from
    if period_to:
        cond.append("created_at <= :period_to")
        params["period_to"] = period_to
    try:
        status_rows = db.execute(
            text(
                f"""
                SELECT status, COUNT(*) AS cnt
                FROM inventory_reservations
                WHERE {' AND '.join(cond)}
                GROUP BY status
                ORDER BY cnt DESC
                """
            ),
            params,
        ).mappings().all()
    except Exception:
        status_rows = []

    by_status = [{"status": str(r["status"]), "count": int(r["cnt"])} for r in status_rows]
    total = sum(x["count"] for x in by_status)

    try:
        detail_rows = db.execute(
            text(
                f"""
                SELECT id, order_id, product_id, locker_id, quantity, status, expires_at, created_at
                FROM inventory_reservations
                WHERE {' AND '.join(cond)}
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            params,
        ).mappings().all()
        items = [
            {
                "id": str(r["id"]),
                "order_id": str(r.get("order_id") or ""),
                "product_id": str(r.get("product_id") or ""),
                "locker_id": str(r.get("locker_id") or ""),
                "quantity": int(r.get("quantity") or 0),
                "status": str(r.get("status") or ""),
                "expires_at": _to_iso(r.get("expires_at")),
                "created_at": _to_iso(r.get("created_at")),
            }
            for r in detail_rows
        ]
    except Exception:
        items = []

    return ReservationHealthOut(
        ok=True,
        period_from=period_from,
        period_to=period_to,
        total=total,
        by_status=[ReservationHealthItemOut(status=x["status"], count=x["count"]) for x in by_status],
        items=items,
    )
