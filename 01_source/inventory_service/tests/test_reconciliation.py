from app.core.database import SessionLocal, init_db
from app.services import reconciliation_service


def test_reconciliation_aligned(client):
    client.post("/api/v1/inventory/movements", json={"sku_id": "z", "delta": 7, "reason": "s"})
    r = client.post("/api/v1/reconciliation/run")
    assert r.status_code == 200
    rows = r.json()
    z = next(x for x in rows if x["sku_id"] == "z")
    assert z["divergent"] is False


def test_reconciliation_divergent_repair():
    init_db()
    db = SessionLocal()
    try:
        from app.models.inventory import InventoryMovement, ProductInventory

        inv = ProductInventory(sku_id="div", quantity_on_hand=99, version=1)
        db.add(inv)
        db.add(InventoryMovement(sku_id="div", delta=1, reason="only", idempotency_key=None))
        db.commit()
        rep = reconciliation_service.reconcile_all(db)
        row = next(x for x in rep if x["sku_id"] == "div")
        assert row["divergent"] is True
        reconciliation_service.repair_from_movements(db, "div")
        rep2 = reconciliation_service.reconcile_all(db)
        row2 = next(x for x in rep2 if x["sku_id"] == "div")
        assert row2["divergent"] is False
    finally:
        db.close()
