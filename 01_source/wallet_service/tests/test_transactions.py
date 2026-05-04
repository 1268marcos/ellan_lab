from fastapi.testclient import TestClient

from app.main import app


def test_debit_success(client):
    client.post("/api/v1/credit", json={"user_id": "d0", "amount": 20, "transaction_id": "cd0"})
    r = client.post("/api/v1/debit", json={"user_id": "d0", "amount": 7, "transaction_id": "dd0"})
    assert r.status_code == 201
    assert r.json()["balance"] == 13


def test_reconcile_empty(client):
    r = client.post("/api/v1/reconcile")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_stress_sequential_debits(client):
    client.post("/api/v1/credit", json={"user_id": "seq", "amount": 10_000, "transaction_id": "seq-seed"})
    for i in range(200):
        r = client.post("/api/v1/debit", json={"user_id": "seq", "amount": 1, "transaction_id": f"seq-d-{i}"})
        assert r.status_code == 201
    b = client.get("/api/v1/balance/seq").json()["balance"]
    assert b == 10_000 - 200


def test_load_many_requests():
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    import fakeredis
    import redis

    redis.Redis.from_url = lambda *a, **k: fakeredis.FakeRedis(decode_responses=False)  # type: ignore[method-assign]
    with TestClient(app) as c:
        for i in range(50):
            c.post("/api/v1/credit", json={"user_id": "load", "amount": 1, "transaction_id": f"lt-{i}"})
        b = c.get("/api/v1/balance/load").json()["balance"]
        assert b >= 50
