import json

from app.core.config import get_settings
from app.services import wallet_service


def test_health(client):
    assert client.get("/api/v1/health").json()["service"] == "wallet-service"


def test_balance_create_and_cache(client):
    client.post("/api/v1/credit", json={"user_id": "u1", "amount": 100, "transaction_id": "t-seed"})
    r1 = client.get("/api/v1/balance/u1")
    assert r1.json()["balance"] == 100
    r2 = client.get("/api/v1/balance/u1")
    assert r2.json()["balance"] == 100


def test_balance_cache_key_helpers():
    assert wallet_service.cache_balance_key("x").startswith("wallet:")


def test_mirror_event(client):
    client.post("/api/v1/credit", json={"user_id": "u2", "amount": 1, "transaction_id": "t-m1"})
    r = client.app.state.redis
    settings = get_settings()
    assert int(r.xlen(settings.wallet_events_stream)) >= 1


def test_get_or_create_wallet_unit():
    from app.core.database import SessionLocal, init_db

    init_db()
    db = SessionLocal()
    try:
        w = wallet_service.get_or_create_wallet(db, "unit-u")
        assert w.balance == 0
    finally:
        db.close()


def test_ledger_sum_empty():
    from app.core.database import SessionLocal, init_db

    init_db()
    db = SessionLocal()
    try:
        wallet_service.get_or_create_wallet(db, "ls")
        assert wallet_service.ledger_sum(db, "ls") == 0
    finally:
        db.close()


def test_debit_insufficient(client):
    r = client.post("/api/v1/debit", json={"user_id": "u3", "amount": 5, "transaction_id": "d1"})
    assert r.status_code == 402


def test_debit_version_mismatch(client):
    client.post("/api/v1/credit", json={"user_id": "u4", "amount": 10, "transaction_id": "c4"})
    b = client.get("/api/v1/balance/u4").json()
    r = client.post(
        "/api/v1/debit",
        json={"user_id": "u4", "amount": 1, "transaction_id": "d4", "version": b["version"] + 9},
    )
    assert r.status_code == 409


def test_credit_idempotent(client):
    body = {"user_id": "u5", "amount": 3, "transaction_id": "idem-c"}
    a = client.post("/api/v1/credit", json=body)
    b = client.post("/api/v1/credit", json=body)
    assert a.json()["transaction_id"] == b.json()["transaction_id"]


def test_events_payment_confirmed(client):
    from app.core.database import SessionLocal, init_db
    from app.events import consumer

    init_db()
    r = client.app.state.redis
    settings = get_settings()
    payload = {"type": "payment.confirmed", "payload": {"user_id": "payu", "amount": 4, "transaction_id": "paytx"}}
    r.xadd(settings.wallet_events_stream, {"data": json.dumps(payload)})
    n = consumer.consume_once(r, SessionLocal)
    assert n == 1
