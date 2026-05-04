import pytest

from app.core.database import SessionLocal, init_db
from app.services import inventory_service
from app.services.idempotency import IdempotencyStore


def test_apply_movement_idempotency_db_path():
    init_db()
    db = SessionLocal()
    try:
        s1 = IdempotencyStore(None)
        m1, _ = inventory_service.apply_movement(db, "idem-sku-zz", 3, "seed", "idem-db-zz", s1)
        s2 = IdempotencyStore(None)
        m2, _ = inventory_service.apply_movement(db, "idem-sku-zz", 3, "seed", "idem-db-zz", s2)
        assert m1.id == m2.id
    finally:
        db.close()


def test_update_inventory_not_found():
    init_db()
    db = SessionLocal()
    try:
        with pytest.raises(ValueError):
            inventory_service.update_inventory_optimistic(db, "nope", 1, 1)
    finally:
        db.close()
