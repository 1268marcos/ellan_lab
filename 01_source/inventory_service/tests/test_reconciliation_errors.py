import pytest

from app.core.database import SessionLocal, init_db
from app.services import reconciliation_service


def test_repair_not_found():
    init_db()
    db = SessionLocal()
    try:
        with pytest.raises(ValueError):
            reconciliation_service.repair_from_movements(db, "missing-sku")
    finally:
        db.close()
