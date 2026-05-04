import json

import pytest

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.models.inventory import Reservation
from app.services.idempotency import IdempotencyStore
from app.workers import stream_consumer


def test_reserve_confirm_release_flow(client):
    client.post("/api/v1/inventory/movements", json={"sku_id": "r1", "delta": 10, "reason": "seed"})
    cr = client.post("/api/v1/reservations", json={"order_id": "o1", "sku_id": "r1", "quantity": 4})
    assert cr.status_code == 201
    rid = cr.json()["id"]
    ver = cr.json()["version"]
    cf = client.post(f"/api/v1/reservations/{rid}/confirm?version={ver}")
    assert cf.status_code == 200
    assert cf.json()["state"] == "confirmed"
    ver2 = cf.json()["version"]
    rel = client.delete(f"/api/v1/reservations/{rid}?version={ver2}")
    assert rel.status_code == 200
    assert rel.json()["state"] == "released"


def test_reserve_idempotency(client):
    client.post("/api/v1/inventory/movements", json={"sku_id": "r2", "delta": 2, "reason": "seed"})
    a = client.post(
        "/api/v1/reservations",
        json={"order_id": "o2", "sku_id": "r2", "quantity": 1},
        headers={"X-Idempotency-Key": "idem-r"},
    )
    b = client.post(
        "/api/v1/reservations",
        json={"order_id": "o2", "sku_id": "r2", "quantity": 1},
        headers={"X-Idempotency-Key": "idem-r"},
    )
    assert a.json()["id"] == b.json()["id"]


def test_stream_payment_and_expire(client):
    client.post("/api/v1/inventory/movements", json={"sku_id": "r3", "delta": 10, "reason": "seed"})
    cr = client.post("/api/v1/reservations", json={"order_id": "pay1", "sku_id": "r3", "quantity": 2})
    assert cr.status_code == 201
    r = client.app.state.redis
    settings = get_settings()
    r.xadd(settings.events_stream, {"data": json.dumps({"type": "payment.confirmed", "payload": {"order_id": "pay1"}})})
    n = stream_consumer.consume_once(r, store=IdempotencyStore(None))
    assert n == 1
    db = SessionLocal()
    try:
        row = db.query(Reservation).filter(Reservation.order_id == "pay1").one()
        assert row.state == "confirmed"
    finally:
        db.close()

    client.post("/api/v1/inventory/movements", json={"sku_id": "r4", "delta": 3, "reason": "seed"})
    cr2 = client.post("/api/v1/reservations", json={"order_id": "exp1", "sku_id": "r4", "quantity": 1})
    assert cr2.status_code == 201
    r.xadd(settings.events_stream, {"data": json.dumps({"type": "order.expired", "payload": {"order_id": "exp1"}})})
    n2 = stream_consumer.consume_once(r, store=IdempotencyStore(None))
    assert n2 == 1
    db = SessionLocal()
    try:
        row2 = db.query(Reservation).filter(Reservation.order_id == "exp1").one()
        assert row2.state == "expired"
    finally:
        db.close()


def test_dlq_on_bad_event(client):
    r = client.app.state.redis
    settings = get_settings()
    r.xadd(settings.events_stream, {"data": json.dumps({"type": "nope", "payload": {}})})
    stream_consumer.consume_once(r, store=IdempotencyStore(None))
    dlq = client.get("/api/v1/dlq").json()
    assert dlq
    assert "error" in dlq[0]


def test_process_message_custom_handler():
    init_db()
    db = SessionLocal()
    seen = {}

    def h(session, payload):
        seen["ok"] = payload.get("x")

    try:
        stream_consumer.process_message(db, {"type": "custom", "payload": {"x": 1}}, None, handlers={"custom": h})
        assert seen.get("ok") == 1
    finally:
        db.close()


def test_read_dlq_none_app():
    from app.workers.stream_consumer import read_dlq

    assert read_dlq(None) == []


def test_process_message_unsupported():
    init_db()
    db = SessionLocal()
    try:
        with pytest.raises(ValueError):
            stream_consumer.process_message(db, {"type": "nope", "payload": {}}, None)
    finally:
        db.close()
