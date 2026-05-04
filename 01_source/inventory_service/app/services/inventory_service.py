from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.inventory import InventoryMovement, ProductInventory
from app.services import double_write
from app.services.idempotency import IdempotencyStore


class OptimisticLockError(Exception):
    pass


def _utc() -> datetime:
    return datetime.now(timezone.utc)


def get_or_create_inventory(db: Session, sku_id: str, partner_id: str | None = None) -> ProductInventory:
    row = db.get(ProductInventory, sku_id)
    if row:
        return row
    row = ProductInventory(sku_id=sku_id, partner_id=partner_id, quantity_on_hand=0, version=1)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def apply_movement(
    db: Session,
    sku_id: str,
    delta: int,
    reason: str,
    idempotency_key: str | None,
    store: IdempotencyStore,
    redis: Any = None,
) -> tuple[InventoryMovement, ProductInventory]:
    if idempotency_key:
        cached = store.get(idempotency_key)
        if cached and cached.get("type") == "movement":
            mid = cached["movement_id"]
            m = db.get(InventoryMovement, mid)
            inv = db.get(ProductInventory, sku_id)
            if m and inv:
                return m, inv

    inv = get_or_create_inventory(db, sku_id)
    if idempotency_key:
        existing = db.execute(select(InventoryMovement).where(InventoryMovement.idempotency_key == idempotency_key)).scalar_one_or_none()
        if existing:
            inv2 = db.get(ProductInventory, existing.sku_id)
            return existing, inv2 or inv

    new_qty = inv.quantity_on_hand + delta
    if new_qty < 0:
        raise ValueError("insufficient_stock")

    movement = InventoryMovement(sku_id=sku_id, delta=delta, reason=reason, idempotency_key=idempotency_key)
    db.add(movement)
    inv.quantity_on_hand = new_qty
    inv.version = inv.version + 1
    inv.updated_at = _utc()
    db.commit()
    db.refresh(movement)
    db.refresh(inv)
    if idempotency_key:
        store.set(idempotency_key, {"type": "movement", "movement_id": movement.id, "sku_id": sku_id})
    double_write.mirror_inventory_state(redis, inv.sku_id, inv.quantity_on_hand, inv.version)
    return movement, inv


def update_inventory_optimistic(
    db: Session, sku_id: str, expected_version: int, new_qty: int
) -> ProductInventory:
    inv = db.get(ProductInventory, sku_id)
    if not inv:
        raise ValueError("not_found")
    if inv.version != expected_version:
        raise OptimisticLockError("version_mismatch")
    inv.quantity_on_hand = new_qty
    inv.version = inv.version + 1
    inv.updated_at = _utc()
    db.commit()
    db.refresh(inv)
    return inv


def sum_movements_for_sku(db: Session, sku_id: str) -> int:
    q = select(func.coalesce(func.sum(InventoryMovement.delta), 0)).where(InventoryMovement.sku_id == sku_id)
    return int(db.execute(q).scalar_one())
