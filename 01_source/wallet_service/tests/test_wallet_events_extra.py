import json

from app.core.database import SessionLocal, init_db
from app.events import consumer
from app.services import wallet_service


def test_handle_payment_skips_empty_user():
    init_db()
    db = SessionLocal()
    try:
        consumer.handle_event(db, None, {"type": "payment.confirmed", "payload": {}})
    finally:
        db.close()


def test_handle_order_expired_insufficient_swallowed():
    init_db()
    db = SessionLocal()
    try:
        wallet_service.get_or_create_wallet(db, "oe")
        consumer.handle_event(db, None, {"type": "order.expired", "payload": {"user_id": "oe", "penalty_amount": 99, "transaction_id": "oe1"}})
    finally:
        db.close()


def test_handle_order_expired_debits():
    init_db()
    db = SessionLocal()
    try:
        wallet_service.credit_wallet(db, None, "oe2", 50, "s-oe2", "credit")
        consumer.handle_event(db, None, {"type": "order.expired", "payload": {"user_id": "oe2", "penalty_amount": 10, "transaction_id": "oe2x"}})
    finally:
        db.close()
    db2 = SessionLocal()
    try:
        w = wallet_service.get_or_create_wallet(db2, "oe2")
        assert w.balance == 40
    finally:
        db2.close()


def test_consume_once_bad_json(client):
    from app.events import consumer

    r = client.app.state.redis
    r.xadd("wallet:test", {"data": "not-json"})
    assert consumer.consume_once(r, SessionLocal, stream_key="wallet:test") == 0


def test_consume_once_no_data_field(client):
    from app.events import consumer

    r = client.app.state.redis
    r.xadd("wallet:empty", {"other": "x"})
    assert consumer.consume_once(r, SessionLocal, stream_key="wallet:empty") == 0


def test_consume_once_payment(client):
    from app.core.config import get_settings
    from app.events import consumer

    init_db()
    r = client.app.state.redis
    settings = get_settings()
    payload = {"type": "payment.confirmed", "payload": {"user_id": "cz", "amount": 2, "transaction_id": "cz1"}}
    r.xadd(settings.wallet_events_stream, {"data": json.dumps(payload)})
    assert consumer.consume_once(r, SessionLocal) >= 1
