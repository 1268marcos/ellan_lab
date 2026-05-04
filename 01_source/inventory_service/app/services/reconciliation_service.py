from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.inventory import ProductInventory
from app.services.inventory_service import sum_movements_for_sku


def reconcile_all(db: Session) -> list[dict]:
    rows = db.query(ProductInventory).all()
    report: list[dict] = []
    for inv in rows:
        expected = sum_movements_for_sku(db, inv.sku_id)
        divergent = expected != inv.quantity_on_hand
        report.append(
            {
                "sku_id": inv.sku_id,
                "expected_from_movements": expected,
                "quantity_on_hand": inv.quantity_on_hand,
                "divergent": divergent,
            }
        )
    return report


def repair_from_movements(db: Session, sku_id: str) -> dict:
    inv = db.get(ProductInventory, sku_id)
    if not inv:
        raise ValueError("not_found")
    expected = sum_movements_for_sku(db, sku_id)
    inv.quantity_on_hand = expected
    inv.version += 1
    db.commit()
    db.refresh(inv)
    return {"sku_id": sku_id, "quantity_on_hand": inv.quantity_on_hand, "repaired": True}
