from fastapi.testclient import TestClient


def test_expired_pickup_propagates(client, monkeypatch):
    import app.routers.credits as cr
    from app.main import app

    monkeypatch.setattr(cr.credit_service, "expire_pickup_debit", lambda *a, **k: (_ for _ in ()).throw(ValueError("boom")))
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/api/v1/expired-pickup", json={"user_id": "x", "amount": 1, "transaction_id": "t"})
    assert r.status_code == 400


def test_apply_credit_propagates(client, monkeypatch):
    import app.routers.credits as cr
    from app.main import app

    monkeypatch.setattr(cr.credit_service, "apply_credit", lambda *a, **k: (_ for _ in ()).throw(ValueError("boom")))
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/api/v1/apply-credit", json={"user_id": "x", "credit_id": "00000000-0000-0000-0000-000000000001", "transaction_id": "t"})
    assert r.status_code == 400
