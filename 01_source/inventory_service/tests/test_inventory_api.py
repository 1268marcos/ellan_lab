import json

from app.core.config import get_settings
from app.services import inventory_service
from app.services.idempotency import IdempotencyStore


def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["service"] == "inventory-service"


def test_get_inventory_creates_row(client):
    r = client.get("/api/v1/inventory/sku-1")
    assert r.status_code == 200
    body = r.json()
    assert body["sku_id"] == "sku-1"
    assert body["quantity_on_hand"] == 0


def test_movement_and_idempotency(client):
    client.post("/api/v1/inventory/movements", json={"sku_id": "x", "delta": 5, "reason": "seed"})
    r1 = client.post(
        "/api/v1/inventory/movements",
        json={"sku_id": "x", "delta": 1, "reason": "adj"},
        headers={"X-Idempotency-Key": "k1"},
    )
    assert r1.status_code == 201
    r2 = client.post(
        "/api/v1/inventory/movements",
        json={"sku_id": "x", "delta": 1, "reason": "adj"},
        headers={"X-Idempotency-Key": "k1"},
    )
    assert r2.status_code == 201
    assert r1.json()["movement_id"] == r2.json()["movement_id"]
    inv = client.get("/api/v1/inventory/x").json()
    assert inv["quantity_on_hand"] == 6


def test_movement_insufficient(client):
    client.post("/api/v1/inventory/movements", json={"sku_id": "y", "delta": 1, "reason": "s"})
    r = client.post("/api/v1/inventory/movements", json={"sku_id": "y", "delta": -5, "reason": "x"})
    assert r.status_code == 409


def test_create_locker(client):
    r = client.post("/api/v1/lockers", json={"site_id": "s1", "name": "L1", "capacity_units": 3})
    assert r.status_code == 201
    assert r.json()["site_id"] == "s1"


def test_double_write_mirror(client):
    client.post("/api/v1/inventory/movements", json={"sku_id": "dw", "delta": 2, "reason": "t"})
    settings = get_settings()
    r = client.app.state.redis
    key = f"{settings.events_stream}:mirror"
    assert int(r.xlen(key)) >= 1
    entries = r.xrevrange(key, count=1)
    _id, fields = entries[0]
    data = fields.get(b"data") or fields.get("data")
    if isinstance(data, bytes):
        data = data.decode()
    obj = json.loads(data)
    assert obj["sku_id"] == "dw"


def test_optimistic_lock_service():
    from app.core.database import SessionLocal, init_db
    from app.models.inventory import ProductInventory

    init_db()
    db = SessionLocal()
    try:
        inventory_service.get_or_create_inventory(db, "ol")
        inventory_service.apply_movement(db, "ol", 10, "seed", None, IdempotencyStore(None))
        inv = db.get(ProductInventory, "ol")
        assert inv is not None
        version_after_seed = inv.version
        inventory_service.update_inventory_optimistic(db, "ol", version_after_seed, 3)
        inv2 = db.get(ProductInventory, "ol")
        assert inv2 is not None
        assert inv2.quantity_on_hand == 3
        try:
            inventory_service.update_inventory_optimistic(db, "ol", version_after_seed, 9)
        except inventory_service.OptimisticLockError:
            pass
        else:
            raise AssertionError("expected OptimisticLockError")
    finally:
        db.close()
