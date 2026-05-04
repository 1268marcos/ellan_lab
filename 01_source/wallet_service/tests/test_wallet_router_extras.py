from fastapi.testclient import TestClient


def test_balance_cache_miss_then_hit(client):
    u = "fresh_balance_only"
    a = client.get(f"/api/v1/balance/{u}").json()
    b = client.get(f"/api/v1/balance/{u}").json()
    assert a["balance"] == 0 == b["balance"]
    assert a["version"] == b["version"]


def test_balance_cache_hit(monkeypatch, client):
    import app.services.wallet_service as ws

    monkeypatch.setattr(ws, "get_cached_balance", lambda r, uid: 55)
    r = client.get("/api/v1/balance/cacheu")
    assert r.json()["balance"] == 55


def test_balance_uses_cache_version(client):
    client.post("/api/v1/credit", json={"user_id": "bc", "amount": 3, "transaction_id": "bc0"})
    a = client.get("/api/v1/balance/bc").json()
    b = client.get("/api/v1/balance/bc").json()
    assert a["balance"] == b["balance"]


def test_credit_bad_request(client, monkeypatch):
    import app.services.wallet_service as ws
    from app.main import app

    def boom(*a, **k):
        raise ValueError("boom")

    monkeypatch.setattr(ws, "credit_wallet", boom)
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/api/v1/credit", json={"user_id": "x", "amount": 1, "transaction_id": "t"})
    assert r.status_code == 400


def test_debit_bad_request(client, monkeypatch):
    import app.services.wallet_service as ws
    from app.main import app

    monkeypatch.setattr(ws, "debit_wallet", lambda *a, **k: (_ for _ in ()).throw(ValueError("boom")))
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/api/v1/debit", json={"user_id": "x", "amount": 1, "transaction_id": "t"})
    assert r.status_code == 400


def test_apply_credit_bad(client):
    r = client.post("/api/v1/apply-credit", json={"user_id": "nope", "credit_id": "00000000-0000-0000-0000-000000000001", "transaction_id": "a"})
    assert r.status_code == 400


def test_expired_pickup_bad(client):
    r = client.post("/api/v1/expired-pickup", json={"user_id": "nope", "amount": 1, "transaction_id": "e"})
    assert r.status_code in (400, 402)
