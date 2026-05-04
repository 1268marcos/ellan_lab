import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_movement_propagates_valueerror(monkeypatch):
    import app.services.inventory_service as inv

    def boom(*a, **k):
        raise ValueError("boom")

    monkeypatch.setattr(inv, "apply_movement", boom)
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/api/v1/inventory/movements", json={"sku_id": "z", "delta": 1, "reason": "r"})
    assert r.status_code == 500


def test_reservation_create_propagates(monkeypatch):
    import app.services.reservation_service as rs

    def boom(*a, **k):
        raise ValueError("boom")

    monkeypatch.setattr(rs, "create_reservation", boom)
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/api/v1/reservations", json={"order_id": "a", "sku_id": "b", "quantity": 1})
    assert r.status_code == 500


def test_reservation_confirm_propagates(monkeypatch):
    import app.services.reservation_service as rs

    def boom(*a, **k):
        raise ValueError("boom")

    monkeypatch.setattr(rs, "confirm_reservation", boom)
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/api/v1/reservations/00000000-0000-0000-0000-000000000099/confirm?version=1")
    assert r.status_code == 500


def test_reservation_release_propagates(monkeypatch):
    import app.services.reservation_service as rs

    def boom(*a, **k):
        raise ValueError("boom")

    monkeypatch.setattr(rs, "release_reservation", boom)
    c = TestClient(app, raise_server_exceptions=False)
    r = c.delete("/api/v1/reservations/00000000-0000-0000-0000-000000000099?version=1")
    assert r.status_code == 500


def test_reservation_create_other_valueerror_raises(monkeypatch):
    import app.services.reservation_service as rs

    monkeypatch.setattr(rs, "create_reservation", lambda *a, **k: (_ for _ in ()).throw(ValueError("other")))
    with pytest.raises(ValueError):
        client = TestClient(app)
        client.post("/api/v1/reservations", json={"order_id": "a2", "sku_id": "b2", "quantity": 1})
