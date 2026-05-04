from datetime import datetime, timedelta, timezone


def test_apply_credit_flow(client):
    client.post("/api/v1/credit", json={"user_id": "cr", "amount": 50, "transaction_id": "cr0"})
    off = client.post(
        "/api/v1/credit-offer",
        json={"user_id": "cr", "amount": 5, "promotional": True, "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()},
    )
    cid = off.json()["credit_id"]
    r = client.post("/api/v1/apply-credit", json={"user_id": "cr", "credit_id": cid, "transaction_id": "ap1"})
    assert r.status_code == 201


def test_expired_pickup(client):
    client.post("/api/v1/credit", json={"user_id": "ex", "amount": 10, "transaction_id": "ex0"})
    r = client.post("/api/v1/expired-pickup", json={"user_id": "ex", "amount": 3, "transaction_id": "xp1"})
    assert r.status_code == 201


def test_apply_credit_not_found(client):
    r = client.post(
        "/api/v1/apply-credit",
        json={"user_id": "cr", "credit_id": "00000000-0000-0000-0000-000000000001", "transaction_id": "apx"},
    )
    assert r.status_code == 400


def test_credit_service_unit():
    from app.core.database import SessionLocal, init_db
    from app.services import credit_service, wallet_service

    init_db()
    db = SessionLocal()
    try:
        wallet_service.credit_wallet(db, None, "cu", 10, "s0", "credit")
        c = credit_service.create_promotional_credit(db, None, "cu", 2, True, None)
        c2, w, t = credit_service.apply_credit(db, None, "cu", c.id, "apu")
        assert c2.remaining == 0
        assert t.transaction_id == "apu"
    finally:
        db.close()


def test_apply_credit_empty_remaining():
    from app.core.database import SessionLocal, init_db
    from app.services import credit_service, wallet_service

    init_db()
    db = SessionLocal()
    try:
        wallet_service.credit_wallet(db, None, "ce", 1, "s1", "credit")
        c = credit_service.create_promotional_credit(db, None, "ce", 1, False, None)
        credit_service.apply_credit(db, None, "ce", c.id, "u1")
        import pytest

        with pytest.raises(ValueError):
            credit_service.apply_credit(db, None, "ce", c.id, "u2")
    finally:
        db.close()


def test_expire_pickup_unit_insufficient():
    from app.core.database import SessionLocal, init_db
    from app.services import credit_service, wallet_service

    init_db()
    db = SessionLocal()
    try:
        wallet_service.get_or_create_wallet(db, "ins")
        import pytest

        with pytest.raises(ValueError):
            credit_service.expire_pickup_debit(db, None, "ins", 5, "x1")
    finally:
        db.close()
