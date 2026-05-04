import fakeredis
from fastapi.testclient import TestClient

from app.core.database import SessionLocal, init_db
from app.services import wallet_service


def test_mirror_event_with_redis():
    from app.core.config import get_settings

    r = fakeredis.FakeRedis(decode_responses=True)
    wallet_service.mirror_event(r, "wallet.credited", {"a": 1})
    assert int(r.xlen(get_settings().wallet_events_stream)) >= 1


def test_cached_balance_bytes():
    r = fakeredis.FakeRedis(decode_responses=False)
    r.setex(wallet_service.cache_balance_key("b1"), 60, b"7")
    assert wallet_service.get_cached_balance(r, "b1") == 7


def test_debit_idempotent_existing():
    init_db()
    db = SessionLocal()
    try:
        wallet_service.credit_wallet(db, None, "idemd", 10, "seed-d", "credit")
        w1, t1 = wallet_service.debit_wallet(db, None, "idemd", 2, "tx-same")
        w2, t2 = wallet_service.debit_wallet(db, None, "idemd", 2, "tx-same")
        assert t1.id == t2.id
        assert w1.balance == w2.balance
    finally:
        db.close()


def test_transactions_router_generic_error(client, monkeypatch):
    import app.routers.transactions as tr
    from app.main import app

    def boom(*a, **k):
        raise ValueError("other")

    monkeypatch.setattr(tr.wallet_service, "credit_wallet", boom)
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/api/v1/credit", json={"user_id": "z", "amount": 1, "transaction_id": "g"})
    assert r.status_code == 400


def test_reconcile_endpoint_generic(client, monkeypatch):
    import app.routers.transactions as tr
    from app.main import app

    monkeypatch.setattr(tr.reconciliation_service, "reconcile_all", lambda db: (_ for _ in ()).throw(ValueError("x")))
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/api/v1/reconcile")
    assert r.status_code == 500
