from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.inventory import InventoryMovement, ProductInventory, Reservation
from app.services.inventory_service import get_or_create_inventory
from app.services.idempotency import IdempotencyStore


def _utc() -> datetime:
    return datetime.now(timezone.utc)


def create_reservation(
    db: Session, order_id: str, sku_id: str, quantity: int, store: IdempotencyStore, idempotency_key: str | None = None
) -> Reservation:
    if idempotency_key:
        cached = store.get(idempotency_key)
        if cached and cached.get("type") == "reservation":
            r = db.get(Reservation, cached["reservation_id"])
            if r:
                return r

    inv = get_or_create_inventory(db, sku_id)
    if inv.quantity_on_hand < quantity:
        raise ValueError("insufficient_stock")

    inv.quantity_on_hand -= quantity
    inv.version += 1
    inv.updated_at = _utc()
    db.add(InventoryMovement(sku_id=sku_id, delta=-quantity, reason="reserve", idempotency_key=None))
    res = Reservation(sku_id=sku_id, order_id=order_id, quantity=quantity, state="pending", version=1)
    db.add(res)
    db.commit()
    db.refresh(res)
    if idempotency_key:
        store.set(idempotency_key, {"type": "reservation", "reservation_id": res.id})
    return res


def confirm_reservation(db: Session, reservation_id: str, expected_version: int) -> Reservation:
    r = db.get(Reservation, reservation_id)
    if not r:
        raise ValueError("not_found")
    if r.version != expected_version:
        raise ValueError("version_mismatch")
    if r.state != "pending":
        raise ValueError("invalid_state")
    r.state = "confirmed"
    r.version += 1
    r.updated_at = _utc()
    db.add(InventoryMovement(sku_id=r.sku_id, delta=0, reason="confirm", idempotency_key=None))
    db.commit()
    db.refresh(r)
    return r


def release_reservation(db: Session, reservation_id: str, expected_version: int, store: IdempotencyStore) -> Reservation:
    r = db.get(Reservation, reservation_id)
    if not r:
        raise ValueError("not_found")
    if r.version != expected_version:
        raise ValueError("version_mismatch")
    if r.state not in ("pending", "confirmed"):
        raise ValueError("invalid_state")
    inv = db.get(ProductInventory, r.sku_id)
    if inv:
        inv.quantity_on_hand += r.quantity
        inv.version += 1
        inv.updated_at = _utc()
    db.add(InventoryMovement(sku_id=r.sku_id, delta=r.quantity, reason="release", idempotency_key=None))
    r.state = "released"
    r.version += 1
    r.updated_at = _utc()
    db.commit()
    db.refresh(r)
    return r


def expire_reservation(db: Session, order_id: str) -> list[Reservation]:
    rows = db.query(Reservation).filter(Reservation.order_id == order_id, Reservation.state == "pending").all()
    out: list[Reservation] = []
    for r in rows:
        inv = db.get(ProductInventory, r.sku_id)
        if inv:
            inv.quantity_on_hand += r.quantity
            inv.version += 1
            inv.updated_at = _utc()
        db.add(InventoryMovement(sku_id=r.sku_id, delta=r.quantity, reason="expire", idempotency_key=None))
        r.state = "expired"
        r.version += 1
        r.updated_at = _utc()
        out.append(r)
    db.commit()
    for r in out:
        db.refresh(r)
    return out


def on_payment_confirmed(db: Session, order_id: str, _store: IdempotencyStore | None = None) -> list[Reservation]:
    rows = db.query(Reservation).filter(Reservation.order_id == order_id, Reservation.state == "pending").all()
    for r in rows:
        r.state = "confirmed"
        r.version += 1
        r.updated_at = _utc()
    db.commit()
    for r in rows:
        db.refresh(r)
    return rows
