from fastapi.testclient import TestClient


def test_credit_other_valueerror(client, monkeypatch):
    import app.routers.transactions as tr
    from app.main import app

    monkeypatch.setattr(tr.wallet_service, "credit_wallet", lambda *a, **k: (_ for _ in ()).throw(ValueError("other")))
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/api/v1/credit", json={"user_id": "x", "amount": 1, "transaction_id": "t"})
    assert r.status_code == 400
