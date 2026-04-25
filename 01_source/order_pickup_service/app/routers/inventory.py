from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_user, require_user_roles
from app.core.db import get_db
from app.models.ops_action_audit import OpsActionAudit
from app.models.user import User
from app.schemas.inventory import (
    InventoryReservationHealthOut,
    InventoryReservationHealthRankItemOut,
    InventoryReservationActionOut,
    InventoryReservationReconciliationItemOut,
    InventoryReservationReconciliationOut,
    InventoryReservationOut,
    InventoryReserveIn,
    InventoryReserveOut,
    InventoryRestockIn,
    InventoryRestockOut,
    ProductInventoryItemOut,
    ProductInventoryListOut,
)
from app.jobs.inventory_reserved_reconciliation import run_inventory_reserved_reconciliation_once
from app.services.ops_audit_service import record_ops_action_audit

router = APIRouter(
    tags=["inventory"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao", "auditoria"}))],
)


def _to_iso_utc(value: datetime | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _parse_iso_datetime_utc_optional(raw_value: str | None, *, field_name: str) -> datetime | None:
    if raw_value is not None and not isinstance(raw_value, str):
        raw_value = getattr(raw_value, "default", raw_value)
    value = str(raw_value or "").strip()
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_DATE_RANGE", "message": f"{field_name} inválido. Use ISO-8601."},
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _to_inventory_item(row: dict) -> ProductInventoryItemOut:
    return ProductInventoryItemOut(
        id=str(row.get("id") or ""),
        product_id=str(row.get("product_id") or ""),
        locker_id=str(row.get("locker_id") or ""),
        slot_size=str(row.get("slot_size") or ""),
        quantity_on_hand=int(row.get("quantity_on_hand") or 0),
        quantity_reserved=int(row.get("quantity_reserved") or 0),
        quantity_available=int(row.get("quantity_available") or 0),
        reorder_point=int(row.get("reorder_point") or 0),
        reorder_quantity=int(row.get("reorder_quantity") or 0),
        last_counted_at=(_to_iso_utc(row.get("last_counted_at")) if row.get("last_counted_at") else None),
        updated_at=_to_iso_utc(row.get("updated_at")),
    )


def _audit_inventory(
    *,
    db: Session,
    action: str,
    result: str,
    user_id: str | None,
    details: dict | None = None,
) -> None:
    try:
        record_ops_action_audit(
            db=db,
            action=action,
            result=result,
            correlation_id=str(uuid4()),
            user_id=user_id,
            role="ops_user",
            details=details or {},
        )
    except Exception:
        pass


def _to_reservation_item(row: dict) -> InventoryReservationOut:
    return InventoryReservationOut(
        id=str(row.get("id") or ""),
        order_id=str(row.get("order_id") or ""),
        product_id=str(row.get("product_id") or ""),
        locker_id=str(row.get("locker_id") or ""),
        slot_size=str(row.get("slot_size") or ""),
        quantity=int(row.get("quantity") or 0),
        status=str(row.get("status") or ""),
        expires_at=_to_iso_utc(row.get("expires_at")),
        updated_at=_to_iso_utc(row.get("updated_at")),
    )


def _load_inventory_row(*, db: Session, product_id: str, locker_id: str, slot_size: str) -> dict:
    row = db.execute(
        text(
            """
            SELECT
                id, product_id, locker_id, slot_size, quantity_on_hand, quantity_reserved,
                quantity_available, reorder_point, reorder_quantity, last_counted_at, updated_at
            FROM product_inventory
            WHERE product_id = :product_id AND locker_id = :locker_id AND slot_size = :slot_size
            """
        ),
        {"product_id": product_id, "locker_id": locker_id, "slot_size": slot_size},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "INVENTORY_NOT_FOUND",
                "message": "Inventário não encontrado para produto/locker/slot informado.",
            },
        )
    return dict(row)


def _inventory_to_audit_payload(row: dict) -> dict:
    return _to_inventory_item(row).model_dump()


def _json_load_dict(value: object) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {}
    return {}


def _safe_delta_pct(current: int, previous: int) -> float:
    if previous <= 0:
        if current <= 0:
            return 0.0
        return 100.0
    return round(((current - previous) / previous) * 100, 2)


def _to_int(value: object) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


@router.get("/products/{product_id}/inventory", response_model=ProductInventoryListOut)
def get_product_inventory(
    product_id: str,
    locker_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    exists = db.execute(text("SELECT id FROM products WHERE id = :id"), {"id": product_id}).mappings().first()
    if not exists:
        raise HTTPException(status_code=404, detail={"type": "PRODUCT_NOT_FOUND", "message": "Produto não encontrado."})

    where_parts = ["product_id = :product_id"]
    params: dict[str, object] = {"product_id": product_id, "limit": int(limit), "offset": int(offset)}
    if str(locker_id or "").strip():
        where_parts.append("locker_id = :locker_id")
        params["locker_id"] = str(locker_id).strip()

    where_sql = " AND ".join(where_parts)
    total_row = db.execute(text(f"SELECT COUNT(*) AS total FROM product_inventory WHERE {where_sql}"), params).mappings().first()
    total = int((total_row or {}).get("total") or 0)
    rows = db.execute(
        text(
            f"""
            SELECT
                id, product_id, locker_id, slot_size, quantity_on_hand, quantity_reserved,
                quantity_available, reorder_point, reorder_quantity, last_counted_at, updated_at
            FROM product_inventory
            WHERE {where_sql}
            ORDER BY updated_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    items = [_to_inventory_item(row) for row in rows]
    return ProductInventoryListOut(ok=True, total=total, limit=limit, offset=offset, items=items)


@router.get("/inventory/{locker_id}", response_model=ProductInventoryListOut)
def get_locker_inventory(
    locker_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    locker = db.execute(text("SELECT id FROM lockers WHERE id = :id"), {"id": locker_id}).mappings().first()
    if not locker:
        raise HTTPException(status_code=404, detail={"type": "LOCKER_NOT_FOUND", "message": "Locker não encontrado."})

    params = {"locker_id": locker_id, "limit": int(limit), "offset": int(offset)}
    total_row = db.execute(
        text("SELECT COUNT(*) AS total FROM product_inventory WHERE locker_id = :locker_id"),
        params,
    ).mappings().first()
    total = int((total_row or {}).get("total") or 0)
    rows = db.execute(
        text(
            """
            SELECT
                id, product_id, locker_id, slot_size, quantity_on_hand, quantity_reserved,
                quantity_available, reorder_point, reorder_quantity, last_counted_at, updated_at
            FROM product_inventory
            WHERE locker_id = :locker_id
            ORDER BY quantity_available ASC, updated_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    items = [_to_inventory_item(row) for row in rows]
    return ProductInventoryListOut(ok=True, total=total, limit=limit, offset=offset, items=items)


@router.post("/inventory/reserve", response_model=InventoryReserveOut)
def post_inventory_reserve(
    payload: InventoryReserveIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product_id = str(payload.product_id or "").strip()
    locker_id = str(payload.locker_id or "").strip()
    slot_size = str(payload.slot_size or "").strip().upper()
    order_id = str(payload.order_id or "").strip()
    if not product_id or not locker_id or not slot_size or not order_id:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_RESERVATION_PAYLOAD",
                "message": "order_id, product_id, locker_id e slot_size são obrigatórios.",
            },
        )

    product = db.execute(text("SELECT id FROM products WHERE id = :id"), {"id": product_id}).mappings().first()
    if not product:
        raise HTTPException(status_code=404, detail={"type": "PRODUCT_NOT_FOUND", "message": "Produto não encontrado."})
    locker = db.execute(text("SELECT id FROM lockers WHERE id = :id"), {"id": locker_id}).mappings().first()
    if not locker:
        raise HTTPException(status_code=404, detail={"type": "LOCKER_NOT_FOUND", "message": "Locker não encontrado."})

    existing = db.execute(
        text(
            """
            SELECT
                id, order_id, product_id, locker_id, slot_size, quantity, status, expires_at, updated_at
            FROM inventory_reservations
            WHERE order_id = :order_id
              AND product_id = :product_id
              AND locker_id = :locker_id
              AND slot_size = :slot_size
              AND status = 'ACTIVE'
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"order_id": order_id, "product_id": product_id, "locker_id": locker_id, "slot_size": slot_size},
    ).mappings().first()
    if existing:
        inventory = _load_inventory_row(db=db, product_id=product_id, locker_id=locker_id, slot_size=slot_size)
        return InventoryReserveOut(
            ok=True,
            idempotent=True,
            reservation=_to_reservation_item(dict(existing)),
            inventory=_to_inventory_item(inventory),
            movement_id="",
        )

    quantity = int(payload.quantity)
    now = datetime.now(timezone.utc)
    inventory_before_row = db.execute(
        text(
            """
            SELECT
                id, product_id, locker_id, slot_size, quantity_on_hand, quantity_reserved,
                quantity_available, reorder_point, reorder_quantity, last_counted_at, updated_at
            FROM product_inventory
            WHERE product_id = :product_id AND locker_id = :locker_id AND slot_size = :slot_size
            FOR UPDATE
            """
        ),
        {"product_id": product_id, "locker_id": locker_id, "slot_size": slot_size},
    ).mappings().first()
    if not inventory_before_row:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "INVENTORY_NOT_FOUND",
                "message": "Inventário não encontrado para produto/locker/slot informado.",
            },
        )
    inventory_before = dict(inventory_before_row)
    available_before = int(inventory_before.get("quantity_on_hand") or 0) - int(
        inventory_before.get("quantity_reserved") or 0
    )
    if available_before < quantity:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "INSUFFICIENT_INVENTORY",
                "message": "Estoque disponível insuficiente para reserva.",
                "available": available_before,
                "requested": quantity,
            },
        )

    try:
        reserve_update = db.execute(
            text(
                """
                UPDATE product_inventory
                SET quantity_reserved = quantity_reserved + :quantity,
                    updated_at = :updated_at
                WHERE id = :id
                  AND (quantity_on_hand - quantity_reserved) >= :quantity
                """
            ),
            {
                "id": str(inventory_before.get("id")),
                "quantity": quantity,
                "updated_at": now,
            },
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "type": "INSUFFICIENT_INVENTORY_CONCURRENT",
                "message": "Reserva concorrente sem saldo disponível no momento da confirmação.",
                "available": max(available_before, 0),
                "requested": quantity,
            },
        )
    if (reserve_update.rowcount or 0) != 1:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "type": "INSUFFICIENT_INVENTORY_CONCURRENT",
                "message": "Reserva concorrente sem saldo disponível no momento da confirmação.",
                "available": max(available_before, 0),
                "requested": quantity,
            },
        )

    reservation_id = str(uuid4())
    expires_at = now + timedelta(minutes=int(payload.expires_in_minutes))
    db.execute(
        text(
            """
            INSERT INTO inventory_reservations (
                id, order_id, product_id, locker_id, slot_size, quantity,
                expires_at, status, note, created_at, updated_at
            ) VALUES (
                :id, :order_id, :product_id, :locker_id, :slot_size, :quantity,
                :expires_at, 'ACTIVE', :note, :created_at, :updated_at
            )
            """
        ),
        {
            "id": reservation_id,
            "order_id": order_id,
            "product_id": product_id,
            "locker_id": locker_id,
            "slot_size": slot_size,
            "quantity": quantity,
            "expires_at": expires_at,
            "note": (payload.note.strip() if payload.note else None),
            "created_at": now,
            "updated_at": now,
        },
    )

    movement_id = str(uuid4())
    db.execute(
        text(
            """
            INSERT INTO inventory_movements (
                id, product_id, locker_id, movement_type, quantity_delta,
                reference_id, reference_type, note, occurred_at, created_by, created_at
            ) VALUES (
                :id, :product_id, :locker_id, 'RESERVATION', 0,
                :reference_id, 'ORDER', :note, :occurred_at, :created_by, :created_at
            )
            """
        ),
        {
            "id": movement_id,
            "product_id": product_id,
            "locker_id": locker_id,
            "reference_id": order_id,
            "note": "Reserva de estoque criada (idempotente por order+produto+locker+slot).",
            "occurred_at": now,
            "created_by": (str(current_user.id) if current_user and current_user.id else None),
            "created_at": now,
        },
    )

    reservation = db.execute(
        text(
            """
            SELECT
                id, order_id, product_id, locker_id, slot_size, quantity, status, expires_at, updated_at
            FROM inventory_reservations
            WHERE id = :id
            """
        ),
        {"id": reservation_id},
    ).mappings().first()
    inventory_after = _load_inventory_row(db=db, product_id=product_id, locker_id=locker_id, slot_size=slot_size)
    _audit_inventory(
        db=db,
        action="INVENTORY_RESERVE",
        result="SUCCESS",
        user_id=(str(current_user.id) if current_user and current_user.id else None),
        details={
            "order_id": order_id,
            "product_id": product_id,
            "locker_id": locker_id,
            "slot_size": slot_size,
            "quantity": quantity,
            "movement_id": movement_id,
            "reservation_id": reservation_id,
            "before": _inventory_to_audit_payload(inventory_before),
            "after": _inventory_to_audit_payload(inventory_after),
        },
    )
    db.commit()
    return InventoryReserveOut(
        ok=True,
        idempotent=False,
        reservation=_to_reservation_item(dict(reservation or {})),
        inventory=_to_inventory_item(inventory_after),
        movement_id=movement_id,
    )


@router.post("/inventory/{locker_id}/restock", response_model=InventoryRestockOut)
def post_inventory_restock(
    locker_id: str,
    payload: InventoryRestockIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product_id = str(payload.product_id or "").strip()
    slot_size = str(payload.slot_size or "").strip().upper()
    if not product_id or not slot_size:
        raise HTTPException(
            status_code=422,
            detail={"type": "INVALID_RESTOCK_PAYLOAD", "message": "product_id e slot_size são obrigatórios."},
        )

    product = db.execute(text("SELECT id FROM products WHERE id = :id"), {"id": product_id}).mappings().first()
    if not product:
        raise HTTPException(status_code=404, detail={"type": "PRODUCT_NOT_FOUND", "message": "Produto não encontrado."})
    locker = db.execute(text("SELECT id FROM lockers WHERE id = :id"), {"id": locker_id}).mappings().first()
    if not locker:
        raise HTTPException(status_code=404, detail={"type": "LOCKER_NOT_FOUND", "message": "Locker não encontrado."})

    now = datetime.now(timezone.utc)
    row = db.execute(
        text(
            """
            SELECT
                id, product_id, locker_id, slot_size, quantity_on_hand, quantity_reserved,
                quantity_available, reorder_point, reorder_quantity, last_counted_at, updated_at
            FROM product_inventory
            WHERE product_id = :product_id AND locker_id = :locker_id AND slot_size = :slot_size
            """
        ),
        {"product_id": product_id, "locker_id": locker_id, "slot_size": slot_size},
    ).mappings().first()

    if not row:
        inventory_id = str(uuid4())
        db.execute(
            text(
                """
                INSERT INTO product_inventory (
                    id, product_id, locker_id, slot_size, quantity_on_hand, quantity_reserved,
                    reorder_point, reorder_quantity, created_at, updated_at
                ) VALUES (
                    :id, :product_id, :locker_id, :slot_size, :quantity_on_hand, 0, 0, 0, :created_at, :updated_at
                )
                """
            ),
            {
                "id": inventory_id,
                "product_id": product_id,
                "locker_id": locker_id,
                "slot_size": slot_size,
                "quantity_on_hand": int(payload.quantity),
                "created_at": now,
                "updated_at": now,
            },
        )
    else:
        db.execute(
            text(
                """
                UPDATE product_inventory
                SET quantity_on_hand = quantity_on_hand + :quantity,
                    updated_at = :updated_at
                WHERE id = :id
                """
            ),
            {"id": str(row.get("id")), "quantity": int(payload.quantity), "updated_at": now},
        )

    movement_id = str(uuid4())
    db.execute(
        text(
            """
            INSERT INTO inventory_movements (
                id, product_id, locker_id, movement_type, quantity_delta,
                reference_id, reference_type, note, occurred_at, created_by, created_at
            ) VALUES (
                :id, :product_id, :locker_id, 'RESTOCK', :quantity_delta,
                NULL, 'MANUAL_COUNT', :note, :occurred_at, :created_by, :created_at
            )
            """
        ),
        {
            "id": movement_id,
            "product_id": product_id,
            "locker_id": locker_id,
            "quantity_delta": int(payload.quantity),
            "note": (payload.note.strip() if payload.note else None),
            "occurred_at": now,
            "created_by": (str(current_user.id) if current_user and current_user.id else None),
            "created_at": now,
        },
    )

    inventory_row = db.execute(
        text(
            """
            SELECT
                id, product_id, locker_id, slot_size, quantity_on_hand, quantity_reserved,
                quantity_available, reorder_point, reorder_quantity, last_counted_at, updated_at
            FROM product_inventory
            WHERE product_id = :product_id AND locker_id = :locker_id AND slot_size = :slot_size
            """
        ),
        {"product_id": product_id, "locker_id": locker_id, "slot_size": slot_size},
    ).mappings().first()
    db.flush()
    _audit_inventory(
        db=db,
        action="INVENTORY_RESTOCK",
        result="SUCCESS",
        user_id=(str(current_user.id) if current_user and current_user.id else None),
        details={
            "product_id": product_id,
            "locker_id": locker_id,
            "slot_size": slot_size,
            "quantity": int(payload.quantity),
            "movement_id": movement_id,
        },
    )
    db.commit()

    return InventoryRestockOut(
        ok=True,
        inventory=_to_inventory_item(dict(inventory_row or {})),
        movement_id=movement_id,
    )


@router.post("/inventory/reservations/{reservation_id}/release", response_model=InventoryReservationActionOut)
def post_inventory_reservation_release(
    reservation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reservation = db.execute(
        text(
            """
            SELECT
                id, order_id, product_id, locker_id, slot_size, quantity, status, expires_at, updated_at
            FROM inventory_reservations
            WHERE id = :id
            """
        ),
        {"id": reservation_id},
    ).mappings().first()
    if not reservation:
        raise HTTPException(status_code=404, detail={"type": "RESERVATION_NOT_FOUND", "message": "Reserva não encontrada."})

    reservation_dict = dict(reservation)
    if str(reservation_dict.get("status") or "").upper() != "ACTIVE":
        raise HTTPException(
            status_code=409,
            detail={"type": "RESERVATION_NOT_ACTIVE", "message": "Reserva não está ativa para release."},
        )

    now = datetime.now(timezone.utc)
    quantity = int(reservation_dict.get("quantity") or 0)
    inventory_before = _load_inventory_row(
        db=db,
        product_id=str(reservation_dict.get("product_id")),
        locker_id=str(reservation_dict.get("locker_id")),
        slot_size=str(reservation_dict.get("slot_size")),
    )
    db.execute(
        text(
            """
            UPDATE product_inventory
            SET quantity_reserved = GREATEST(quantity_reserved - :quantity, 0),
                updated_at = :updated_at
            WHERE id = :id
            """
        ),
        {"id": str(inventory_before.get("id")), "quantity": quantity, "updated_at": now},
    )
    db.execute(
        text("UPDATE inventory_reservations SET status = 'RELEASED', updated_at = :updated_at WHERE id = :id"),
        {"id": reservation_id, "updated_at": now},
    )
    movement_id = str(uuid4())
    db.execute(
        text(
            """
            INSERT INTO inventory_movements (
                id, product_id, locker_id, movement_type, quantity_delta,
                reference_id, reference_type, note, occurred_at, created_by, created_at
            ) VALUES (
                :id, :product_id, :locker_id, 'RESERVATION_RELEASE', 0,
                :reference_id, 'ORDER', :note, :occurred_at, :created_by, :created_at
            )
            """
        ),
        {
            "id": movement_id,
            "product_id": str(reservation_dict.get("product_id")),
            "locker_id": str(reservation_dict.get("locker_id")),
            "reference_id": str(reservation_dict.get("order_id")),
            "note": "Reserva liberada (stub operacional).",
            "occurred_at": now,
            "created_by": (str(current_user.id) if current_user and current_user.id else None),
            "created_at": now,
        },
    )
    reservation_after = db.execute(
        text(
            """
            SELECT
                id, order_id, product_id, locker_id, slot_size, quantity, status, expires_at, updated_at
            FROM inventory_reservations
            WHERE id = :id
            """
        ),
        {"id": reservation_id},
    ).mappings().first()
    inventory_after = _load_inventory_row(
        db=db,
        product_id=str(reservation_dict.get("product_id")),
        locker_id=str(reservation_dict.get("locker_id")),
        slot_size=str(reservation_dict.get("slot_size")),
    )
    _audit_inventory(
        db=db,
        action="INVENTORY_RESERVATION_RELEASE",
        result="SUCCESS",
        user_id=(str(current_user.id) if current_user and current_user.id else None),
        details={
            "reservation_id": reservation_id,
            "movement_id": movement_id,
            "before": _inventory_to_audit_payload(inventory_before),
            "after": _inventory_to_audit_payload(inventory_after),
        },
    )
    db.commit()
    return InventoryReservationActionOut(
        ok=True,
        reservation=_to_reservation_item(dict(reservation_after or {})),
        inventory=_to_inventory_item(inventory_after),
        movement_id=movement_id,
    )


@router.post("/inventory/reservations/{reservation_id}/consume", response_model=InventoryReservationActionOut)
def post_inventory_reservation_consume(
    reservation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reservation = db.execute(
        text(
            """
            SELECT
                id, order_id, product_id, locker_id, slot_size, quantity, status, expires_at, updated_at
            FROM inventory_reservations
            WHERE id = :id
            """
        ),
        {"id": reservation_id},
    ).mappings().first()
    if not reservation:
        raise HTTPException(status_code=404, detail={"type": "RESERVATION_NOT_FOUND", "message": "Reserva não encontrada."})
    reservation_dict = dict(reservation)
    if str(reservation_dict.get("status") or "").upper() != "ACTIVE":
        raise HTTPException(
            status_code=409,
            detail={"type": "RESERVATION_NOT_ACTIVE", "message": "Reserva não está ativa para consume."},
        )

    now = datetime.now(timezone.utc)
    quantity = int(reservation_dict.get("quantity") or 0)
    inventory_before = _load_inventory_row(
        db=db,
        product_id=str(reservation_dict.get("product_id")),
        locker_id=str(reservation_dict.get("locker_id")),
        slot_size=str(reservation_dict.get("slot_size")),
    )
    db.execute(
        text(
            """
            UPDATE product_inventory
            SET quantity_on_hand = GREATEST(quantity_on_hand - :quantity, 0),
                quantity_reserved = GREATEST(quantity_reserved - :quantity, 0),
                updated_at = :updated_at
            WHERE id = :id
            """
        ),
        {"id": str(inventory_before.get("id")), "quantity": quantity, "updated_at": now},
    )
    db.execute(
        text("UPDATE inventory_reservations SET status = 'CONSUMED', updated_at = :updated_at WHERE id = :id"),
        {"id": reservation_id, "updated_at": now},
    )
    movement_id = str(uuid4())
    db.execute(
        text(
            """
            INSERT INTO inventory_movements (
                id, product_id, locker_id, movement_type, quantity_delta,
                reference_id, reference_type, note, occurred_at, created_by, created_at
            ) VALUES (
                :id, :product_id, :locker_id, 'SALE', :quantity_delta,
                :reference_id, 'ORDER', :note, :occurred_at, :created_by, :created_at
            )
            """
        ),
        {
            "id": movement_id,
            "product_id": str(reservation_dict.get("product_id")),
            "locker_id": str(reservation_dict.get("locker_id")),
            "quantity_delta": -quantity,
            "reference_id": str(reservation_dict.get("order_id")),
            "note": "Reserva consumida (stub operacional de baixa por venda).",
            "occurred_at": now,
            "created_by": (str(current_user.id) if current_user and current_user.id else None),
            "created_at": now,
        },
    )
    reservation_after = db.execute(
        text(
            """
            SELECT
                id, order_id, product_id, locker_id, slot_size, quantity, status, expires_at, updated_at
            FROM inventory_reservations
            WHERE id = :id
            """
        ),
        {"id": reservation_id},
    ).mappings().first()
    inventory_after = _load_inventory_row(
        db=db,
        product_id=str(reservation_dict.get("product_id")),
        locker_id=str(reservation_dict.get("locker_id")),
        slot_size=str(reservation_dict.get("slot_size")),
    )
    _audit_inventory(
        db=db,
        action="INVENTORY_RESERVATION_CONSUME",
        result="SUCCESS",
        user_id=(str(current_user.id) if current_user and current_user.id else None),
        details={
            "reservation_id": reservation_id,
            "movement_id": movement_id,
            "before": _inventory_to_audit_payload(inventory_before),
            "after": _inventory_to_audit_payload(inventory_after),
        },
    )
    db.commit()
    return InventoryReservationActionOut(
        ok=True,
        reservation=_to_reservation_item(dict(reservation_after or {})),
        inventory=_to_inventory_item(inventory_after),
        movement_id=movement_id,
    )


@router.get("/inventory/ops/view", response_class=HTMLResponse)
def get_inventory_ops_view() -> HTMLResponse:
    html = """
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>ELLAN LAB Inventory OPS</title>
    <style>
      body { font-family: Inter, Arial, sans-serif; margin: 24px; background:#F8FAFC; color:#0F172A; }
      h1 { margin: 0 0 12px 0; font-size: 24px; }
      .row { display:flex; gap:10px; flex-wrap:wrap; margin-bottom: 12px; }
      input, button { padding:8px 10px; border:1px solid #CBD5E1; border-radius:8px; background:#fff; }
      button { background:#1D4ED8; color:#fff; border:none; cursor:pointer; }
      .cards { display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:12px; margin: 16px 0; }
      .card { background:#fff; border:1px solid #E2E8F0; border-radius:12px; padding:12px; }
      .label { color:#475569; font-size:12px; text-transform: uppercase; letter-spacing: .04em; }
      .value { font-size:24px; font-weight:700; margin-top:6px; }
      pre { background:#0B1220; color:#E2E8F0; border-radius:12px; padding:12px; overflow:auto; font-size:12px; }
    </style>
  </head>
  <body>
    <h1>OPS Inventory (Pr-2 D1-D3)</h1>
    <div class="row">
      <input id="lockerId" placeholder="locker_id (obrigatório)" size="30" />
      <button onclick="loadData()">Consultar locker</button>
    </div>
    <div class="cards">
      <div class="card"><div class="label">Itens retornados</div><div id="items" class="value">-</div></div>
      <div class="card"><div class="label">Total inventário</div><div id="total" class="value">-</div></div>
    </div>
    <pre id="payload">Informe um locker_id e clique em Consultar locker.</pre>
    <script>
      async function loadData() {
        const lockerId = document.getElementById('lockerId').value.trim();
        if (!lockerId) {
          document.getElementById('payload').textContent = 'locker_id é obrigatório.';
          return;
        }
        const resp = await fetch('/inventory/' + encodeURIComponent(lockerId) + '?limit=50&offset=0');
        const data = await resp.json();
        document.getElementById('payload').textContent = JSON.stringify(data, null, 2);
        document.getElementById('items').textContent = (data?.items || []).length;
        document.getElementById('total').textContent = data?.total ?? '-';
      }
    </script>
  </body>
</html>
"""
    return HTMLResponse(content=html)


@router.post("/ops/inventory/reconciliation/run", response_model=InventoryReservationReconciliationOut)
def run_inventory_ops_reconciliation_now(
    db: Session = Depends(get_db),
):
    result = run_inventory_reserved_reconciliation_once(db)
    items = [InventoryReservationReconciliationItemOut(**item) for item in (result.get("items") or [])]
    return InventoryReservationReconciliationOut(
        ok=True,
        checked_at=str(result.get("checked_at") or _to_iso_utc(datetime.now(timezone.utc))),
        auto_fixed=int(result.get("auto_fixed") or 0),
        divergence_alerts=int(result.get("divergence_alerts") or 0),
        orphan_active_groups=int(result.get("orphan_active_groups") or 0),
        items=items,
    )


@router.get("/ops/inventory/reconciliation", response_model=InventoryReservationReconciliationOut)
def get_inventory_ops_reconciliation_status(
    hours: int = Query(default=24, ge=1, le=24 * 30),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    actions = (
        "INVENTORY_RESERVED_DIVERGENCE_ALERT",
        "INVENTORY_RESERVED_RECONCILE_AUTO_FIX",
        "INVENTORY_RESERVED_ORPHAN_ALERT",
    )
    rows = db.execute(
        text(
            """
            SELECT created_at, action, result, details_json
            FROM ops_action_audit
            WHERE action IN (
                'INVENTORY_RESERVED_DIVERGENCE_ALERT',
                'INVENTORY_RESERVED_RECONCILE_AUTO_FIX',
                'INVENTORY_RESERVED_ORPHAN_ALERT'
            )
              AND created_at >= (NOW() - (:hours::text || ' hours')::interval)
            ORDER BY created_at DESC, id DESC
            LIMIT :limit
            """
        ),
        {"hours": int(hours), "limit": int(limit)},
    ).mappings().all()
    latest_checked_at = _to_iso_utc(datetime.now(timezone.utc))
    auto_fixed = 0
    divergence_alerts = 0
    orphan_active_groups = 0
    items: list[InventoryReservationReconciliationItemOut] = []
    for row in rows:
        action = str(row.get("action") or "")
        if action not in actions:
            continue
        details = _json_load_dict(row.get("details_json"))
        if not details:
            continue
        latest_checked_at = _to_iso_utc(row.get("created_at")) if row.get("created_at") else latest_checked_at
        status = "DIVERGENCE_ALERT"
        if action == "INVENTORY_RESERVED_RECONCILE_AUTO_FIX":
            auto_fixed += 1
            status = "AUTO_FIXED"
        elif action == "INVENTORY_RESERVED_ORPHAN_ALERT":
            orphan_active_groups += 1
            divergence_alerts += 1
            status = "ORPHAN_ACTIVE_RESERVATIONS"
        else:
            divergence_alerts += 1

        items.append(
            InventoryReservationReconciliationItemOut(
                product_id=str(details.get("product_id") or ""),
                locker_id=str(details.get("locker_id") or ""),
                slot_size=str(details.get("slot_size") or ""),
                reserved_stored=int(details.get("reserved_stored") or 0),
                reserved_active=int(details.get("reserved_active") or 0),
                delta=int(details.get("delta") or 0),
                status=status,
            )
        )

    return InventoryReservationReconciliationOut(
        ok=True,
        checked_at=latest_checked_at,
        auto_fixed=auto_fixed,
        divergence_alerts=divergence_alerts,
        orphan_active_groups=orphan_active_groups,
        items=items,
    )


@router.get("/ops/inventory/reservation-health", response_model=InventoryReservationHealthOut)
def get_inventory_ops_reservation_health(
    period_from: str | None = Query(default=None),
    period_to: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    parsed_to = _parse_iso_datetime_utc_optional(period_to, field_name="period_to") or now
    parsed_from = _parse_iso_datetime_utc_optional(period_from, field_name="period_from") or (parsed_to - timedelta(hours=24))
    if parsed_from >= parsed_to:
        raise HTTPException(
            status_code=422,
            detail={
                "type": "INVALID_DATE_RANGE",
                "message": "period_from deve ser menor que period_to.",
            },
        )
    window = parsed_to - parsed_from
    previous_to = parsed_from
    previous_from = previous_to - window

    actions = {
        "INVENTORY_RESERVED_DIVERGENCE_ALERT",
        "INVENTORY_RESERVED_RECONCILE_AUTO_FIX",
        "INVENTORY_RESERVED_ORPHAN_ALERT",
    }
    rows = (
        db.query(OpsActionAudit)
        .filter(
            OpsActionAudit.action.in_(actions),
            OpsActionAudit.created_at >= previous_from,
            OpsActionAudit.created_at <= parsed_to,
        )
        .order_by(OpsActionAudit.created_at.desc(), OpsActionAudit.id.desc())
        .all()
    )

    totals_current = {"divergence": 0, "autofix": 0, "orphan": 0}
    totals_previous = {"divergence": 0, "autofix": 0, "orphan": 0}
    grouped_current: dict[tuple[str, str, str], dict[str, int]] = {}
    grouped_previous: dict[tuple[str, str, str], dict[str, int]] = {}

    for row in rows:
        details = _json_load_dict(getattr(row, "details_json", {}))
        product_id = str(details.get("product_id") or "")
        locker_id = str(details.get("locker_id") or "")
        slot_size = str(details.get("slot_size") or "")
        if not product_id or not locker_id or not slot_size:
            continue
        key = (product_id, locker_id, slot_size)
        action = str(row.action or "").strip().upper()
        delta = abs(_to_int(details.get("delta")))
        created_at = row.created_at
        if created_at is None:
            continue
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        bucket = grouped_current if (created_at >= parsed_from and created_at <= parsed_to) else grouped_previous
        totals = totals_current if bucket is grouped_current else totals_previous
        stat = bucket.setdefault(
            key,
            {
                "divergence_events": 0,
                "abs_delta_sum": 0,
                "auto_fixes": 0,
                "orphan_alerts": 0,
            },
        )
        if action == "INVENTORY_RESERVED_RECONCILE_AUTO_FIX":
            stat["auto_fixes"] += 1
            totals["autofix"] += 1
        elif action == "INVENTORY_RESERVED_ORPHAN_ALERT":
            stat["orphan_alerts"] += 1
            stat["divergence_events"] += 1
            stat["abs_delta_sum"] += max(delta, abs(_to_int(details.get("reserved_active"))))
            totals["orphan"] += 1
            totals["divergence"] += 1
        elif action == "INVENTORY_RESERVED_DIVERGENCE_ALERT":
            stat["divergence_events"] += 1
            stat["abs_delta_sum"] += delta
            totals["divergence"] += 1

    all_keys = set(grouped_current.keys()) | set(grouped_previous.keys())
    ranking_items: list[InventoryReservationHealthRankItemOut] = []
    for product_id, locker_id, slot_size in all_keys:
        curr = grouped_current.get(
            (product_id, locker_id, slot_size),
            {"divergence_events": 0, "abs_delta_sum": 0, "auto_fixes": 0, "orphan_alerts": 0},
        )
        prev = grouped_previous.get(
            (product_id, locker_id, slot_size),
            {"divergence_events": 0, "abs_delta_sum": 0, "auto_fixes": 0, "orphan_alerts": 0},
        )
        divergence_curr = int(curr["divergence_events"])
        divergence_prev = int(prev["divergence_events"])
        delta_curr = int(curr["abs_delta_sum"])
        delta_prev = int(prev["abs_delta_sum"])
        trend = "stable"
        if divergence_curr > divergence_prev or delta_curr > delta_prev:
            trend = "up"
        elif divergence_curr < divergence_prev or delta_curr < delta_prev:
            trend = "down"

        ranking_items.append(
            InventoryReservationHealthRankItemOut(
                product_id=product_id,
                locker_id=locker_id,
                slot_size=slot_size,
                divergence_events_current=divergence_curr,
                divergence_events_previous=divergence_prev,
                divergence_events_delta_pct=_safe_delta_pct(divergence_curr, divergence_prev),
                abs_delta_sum_current=delta_curr,
                abs_delta_sum_previous=delta_prev,
                abs_delta_sum_delta_pct=_safe_delta_pct(delta_curr, delta_prev),
                auto_fixes_current=int(curr["auto_fixes"]),
                auto_fixes_previous=int(prev["auto_fixes"]),
                orphan_alerts_current=int(curr["orphan_alerts"]),
                orphan_alerts_previous=int(prev["orphan_alerts"]),
                trend=trend,
            )
        )

    ranking_items.sort(
        key=lambda item: (
            item.abs_delta_sum_current,
            item.divergence_events_current,
            item.orphan_alerts_current,
        ),
        reverse=True,
    )
    ranking_items = ranking_items[: int(limit)]

    return InventoryReservationHealthOut(
        ok=True,
        period_from=_to_iso_utc(parsed_from),
        period_to=_to_iso_utc(parsed_to),
        previous_from=_to_iso_utc(previous_from),
        previous_to=_to_iso_utc(previous_to),
        divergence_events_current=totals_current["divergence"],
        divergence_events_previous=totals_previous["divergence"],
        divergence_events_delta_pct=_safe_delta_pct(
            totals_current["divergence"],
            totals_previous["divergence"],
        ),
        auto_fixes_current=totals_current["autofix"],
        auto_fixes_previous=totals_previous["autofix"],
        auto_fixes_delta_pct=_safe_delta_pct(
            totals_current["autofix"],
            totals_previous["autofix"],
        ),
        orphan_alerts_current=totals_current["orphan"],
        orphan_alerts_previous=totals_previous["orphan"],
        orphan_alerts_delta_pct=_safe_delta_pct(
            totals_current["orphan"],
            totals_previous["orphan"],
        ),
        entities_with_divergence_current=len(grouped_current),
        entities_with_divergence_previous=len(grouped_previous),
        ranking=ranking_items,
    )

