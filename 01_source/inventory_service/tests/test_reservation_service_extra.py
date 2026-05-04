import pytest
from sqlalchemy.orm import Session as OrmSession

from app.core.database import SessionLocal, init_db
from app.models.inventory import ProductInventory, Reservation
from app.services import inventory_service, reservation_service
from app.services.idempotency import IdempotencyStore


def test_create_reservation_insufficient_stock_unit():
    init_db()
    db = SessionLocal()
    try:
        with pytest.raises(ValueError):
            reservation_service.create_reservation(db, "o", "no-stock", 5, IdempotencyStore(None))
    finally:
        db.close()


def test_release_when_inventory_row_missing(monkeypatch):
    orig_get = OrmSession.get

    def fake_get(self, entity, ident, options=None):  # noqa: ANN001
        if entity is ProductInventory:
            return None
        return orig_get(self, entity, ident, options=options)

    monkeypatch.setattr(OrmSession, "get", fake_get)
    init_db()
    db = SessionLocal()
    try:
        db.add(ProductInventory(sku_id="ghost-rel-1", quantity_on_hand=1, version=1))
        db.add(Reservation(sku_id="ghost-rel-1", order_id="go-rel-1", quantity=1, state="pending", version=1))
        db.commit()
        rid = db.query(Reservation).filter(Reservation.order_id == "go-rel-1").one().id
        out = reservation_service.release_reservation(db, rid, 1, IdempotencyStore(None))
        assert out.state == "released"
    finally:
        db.close()


def test_create_reservation_cache_miss_deleted_row():
    init_db()
    db = SessionLocal()
    store = IdempotencyStore(None)
    try:
        db.add(ProductInventory(sku_id="c1", quantity_on_hand=5, version=1))
        db.commit()
        r1 = reservation_service.create_reservation(db, "o1", "c1", 1, store, "idem-x")
        store.set("idem-x", {"type": "reservation", "reservation_id": r1.id})
        db.delete(r1)
        db.commit()
        r2 = reservation_service.create_reservation(db, "o2", "c1", 1, store, "idem-x")
        assert r2.state == "pending"
    finally:
        db.close()


def test_expire_missing_inventory_row(monkeypatch):
    import uuid

    orig_get = OrmSession.get

    def fake_get(self, entity, ident, options=None):  # noqa: ANN001
        if entity is ProductInventory:
            return None
        return orig_get(self, entity, ident, options=options)

    init_db()
    db = SessionLocal()
    try:
        sku = f"exg-{uuid.uuid4().hex[:10]}"
        oid = f"eo-{uuid.uuid4().hex[:10]}"
        inventory_service.apply_movement(db, sku, 5, "seed", None, IdempotencyStore(None))
        reservation_service.create_reservation(db, oid, sku, 1, IdempotencyStore(None))
        monkeypatch.setattr(OrmSession, "get", fake_get)
        out = reservation_service.expire_reservation(db, oid)
        assert len(out) == 1
        assert out[0].state == "expired"
    finally:
        db.close()


def test_release_twice_raises_invalid_state():
    init_db()
    db = SessionLocal()
    store = IdempotencyStore(None)
    try:
        db.add(ProductInventory(sku_id="rel2", quantity_on_hand=3, version=1))
        db.commit()
        r = reservation_service.create_reservation(db, "o", "rel2", 1, store)
        v = r.version
        reservation_service.release_reservation(db, r.id, v, store)
        with pytest.raises(ValueError):
            reservation_service.release_reservation(db, r.id, v + 1, store)
    finally:
        db.close()
