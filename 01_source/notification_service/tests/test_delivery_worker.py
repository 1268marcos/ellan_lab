from app.core.database import SessionLocal, init_db
from app.models.notification import Notification
from app.workers import delivery_worker


def test_process_queue_success():
    init_db()
    db = SessionLocal()
    try:
        n = Notification(channel="email", payload="hi {{order_id}}", status="queued")
        db.add(n)
        db.commit()
        db.refresh(n)
        assert delivery_worker.process_queue(db, None, "ord1") == 1
        db.refresh(n)
        assert n.status == "sent"
    finally:
        db.close()


def test_process_queue_rate_limited(monkeypatch):
    init_db()
    db = SessionLocal()
    try:
        n = Notification(channel="sms", payload="x {{order_id}}", status="queued")
        db.add(n)
        db.commit()
        db.refresh(n)

        def fake_rl(_r, _k):
            return True

        monkeypatch.setattr("app.workers.production_hardening.rate_limited", fake_rl)
        assert delivery_worker.process_queue(db, None, "o") == 0
        db.refresh(n)
        assert n.status == "rate_limited"
    finally:
        db.close()


def test_deliver_failure_dlq(monkeypatch):
    init_db()
    db = SessionLocal()
    try:
        n = Notification(channel="email", payload="", status="queued")
        db.add(n)
        db.commit()
        db.refresh(n)
        monkeypatch.setattr("app.workers.production_hardening.rate_limited", lambda r, k: False)
        monkeypatch.setattr("app.workers.production_hardening.email.send_email", lambda *a, **k: False)
        import fakeredis

        r = fakeredis.FakeRedis(decode_responses=False)
        assert delivery_worker.deliver_one(db, r, n, "o") is False
        db.refresh(n)
        assert n.status == "failed"
    finally:
        db.close()


def test_deliver_unknown_channel():
    init_db()
    db = SessionLocal()
    try:
        n = Notification(channel="fax", payload="x", status="queued")
        db.add(n)
        db.commit()
        assert delivery_worker.deliver_one(db, None, n, "o") is False
    finally:
        db.close()


def test_process_queue_custom_sender():
    init_db()
    db = SessionLocal()
    try:
        n = Notification(channel="email", payload="x", status="queued")
        db.add(n)
        db.commit()

        def sender(session, r, row, oid):
            row.status = "sent"
            session.commit()
            return True

        assert delivery_worker.process_queue(db, None, "o", sender=sender) == 1
    finally:
        db.close()


def test_rate_limited_incr():
    import fakeredis

    from app.core.config import get_settings

    r = fakeredis.FakeRedis(decode_responses=False)
    settings = get_settings()
    for _ in range(settings.rate_limit_per_hour):
        assert delivery_worker.rate_limited(r, "rlk2") is False
    assert delivery_worker.rate_limited(r, "rlk2") is True


def test_deliver_sms_fail(monkeypatch):
    init_db()
    db = SessionLocal()
    try:
        n = Notification(channel="sms", payload="x", status="queued")
        db.add(n)
        db.commit()
        db.refresh(n)
        monkeypatch.setattr("app.workers.production_hardening.sms.send_sms", lambda *a, **k: False)
        assert delivery_worker.deliver_one(db, None, n, "o") is False
    finally:
        db.close()


def test_deliver_whatsapp_fail(monkeypatch):
    init_db()
    db = SessionLocal()
    try:
        n = Notification(channel="whatsapp", payload="x", status="queued")
        db.add(n)
        db.commit()
        db.refresh(n)
        monkeypatch.setattr("app.workers.production_hardening.whatsapp.send_whatsapp", lambda *a, **k: False)
        assert delivery_worker.deliver_one(db, None, n, "o") is False
    finally:
        db.close()


def test_push_dlq_serializes():
    import fakeredis

    r = fakeredis.FakeRedis(decode_responses=False)
    delivery_worker.push_dlq(r, {"a": 1})
    raw = r.lpop("notification:dlq")
    assert raw
