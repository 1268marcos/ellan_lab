import pytest

from app.core.database import SessionLocal, init_db
from app.models.transaction import Transaction
from app.services import wallet_service


def test_get_cached_balance_r_none():
    assert wallet_service.get_cached_balance(None, "any") is None


def test_get_cached_balance_miss_with_redis():
    import fakeredis

    r = fakeredis.FakeRedis(decode_responses=True)
    assert wallet_service.get_cached_balance(r, "missing-key-xyz") is None


def test_credit_existing_wallet_missing(monkeypatch):
    init_db()
    db = SessionLocal()
    try:
        fake = Transaction(user_id="wm", amount=1, tx_type="credit", status="completed", transaction_id="wm-tx")
        monkeypatch.setattr(db, "scalar", lambda _q: fake)
        monkeypatch.setattr(db, "get", lambda *a, **k: None)
        with pytest.raises(ValueError):
            wallet_service.credit_wallet(db, None, "wm", 1, "wm-tx")
    finally:
        db.close()


def test_debit_existing_wallet_missing(monkeypatch):
    init_db()
    db = SessionLocal()
    try:
        fake = Transaction(user_id="wm2", amount=-1, tx_type="debit", status="completed", transaction_id="wm2-tx")
        monkeypatch.setattr(db, "scalar", lambda _q: fake)
        monkeypatch.setattr(db, "get", lambda *a, **k: None)
        with pytest.raises(ValueError):
            wallet_service.debit_wallet(db, None, "wm2", 1, "wm2-tx")
    finally:
        db.close()


def test_maybe_mtls_spec_none(monkeypatch):
    import importlib

    import app.main as mm

    monkeypatch.setenv("MTLS_ENFORCE", "1")
    monkeypatch.setattr(mm.importlib.util, "spec_from_file_location", lambda *a, **k: None)
    importlib.reload(mm)
    monkeypatch.setenv("MTLS_ENFORCE", "0")
    importlib.reload(mm)
