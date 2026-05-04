from __future__ import annotations

import json
from unittest import mock

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.partner import Partner
from app.models.webhook import PartnerWebhookDelivery, PartnerWebhookSubscription
from app.schemas.webhook import WebhookConfigureIn
from app.services import webhook_delivery
from app.workers import webhook_worker


@pytest.fixture
def db_session():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    Session = sessionmaker(bind=eng)
    s = Session()
    try:
        yield s
    finally:
        s.close()


def test_configure_and_list(db_session):
    p = Partner(id="p1", name="n", partner_type="ECOMMERCE", status="ACTIVE")
    db_session.add(p)
    db_session.commit()
    sub = webhook_delivery.configure_webhook(
        db_session,
        "p1",
        WebhookConfigureIn(url="https://example.com/h", events=["a"]),
    )
    assert sub.url.startswith("https://")
    rows = webhook_delivery.list_deliveries(db_session, "p1")
    assert rows == []


def test_enqueue_and_worker_default(db_session, fake_redis, monkeypatch):
    monkeypatch.setattr(
        "app.workers.webhook_worker.deliver_http_sync",
        lambda sub, inner: (200, None),
    )
    p = Partner(id="p1", name="n", partner_type="ECOMMERCE", status="ACTIVE")
    db_session.add(p)
    db_session.commit()
    sub = PartnerWebhookSubscription(
        id="s1",
        partner_id="p1",
        url="https://example.com/nope",
        events=json.dumps(["*"]),
        secret=None,
        is_active=True,
    )
    db_session.add(sub)
    db_session.commit()
    d = webhook_delivery.create_pending_delivery(db_session, "s1", "e", {"x": 1})
    webhook_delivery.enqueue_test_event(
        fake_redis,
        stream_key="tstream",
        subscription_id="s1",
        event_type="e",
        payload={"delivery_id": d.id, "x": 1},
    )
    n = webhook_worker.process_stream_batch(
        db=db_session,
        redis_client=fake_redis,
        stream_key="tstream",
        group="g1",
        consumer="c1",
        count=10,
        block_ms=1,
    )
    assert n == 1
    db_session.refresh(d)
    assert d.attempts >= 1
    assert d.status == "DELIVERED"


def test_worker_http_failure_marks_failed(db_session, fake_redis, monkeypatch):
    monkeypatch.setattr(
        "app.workers.webhook_worker.deliver_http_sync",
        lambda sub, inner: (500, "err"),
    )
    p = Partner(id="p1", name="n", partner_type="ECOMMERCE", status="ACTIVE")
    db_session.add(p)
    sub = PartnerWebhookSubscription(
        id="s9",
        partner_id="p1",
        url="http://x",
        events="[]",
        secret=None,
        is_active=True,
    )
    db_session.add(sub)
    db_session.commit()
    d = webhook_delivery.create_pending_delivery(db_session, "s9", "e", {})
    webhook_delivery.enqueue_test_event(
        fake_redis,
        stream_key="tsf",
        subscription_id="s9",
        event_type="e",
        payload={"delivery_id": d.id},
    )
    webhook_worker.process_stream_batch(
        db=db_session,
        redis_client=fake_redis,
        stream_key="tsf",
        group="gf",
        consumer="cf",
        count=10,
        block_ms=1,
    )
    db_session.refresh(d)
    assert d.status == "FAILED"


def test_worker_empty_stream(db_session, fake_redis):
    n = webhook_worker.process_stream_batch(
        db=db_session,
        redis_client=fake_redis,
        stream_key="empty_x",
        group="ge",
        consumer="ce",
        count=10,
        block_ms=1,
    )
    assert n == 0


def test_publish_to_stream(db_session, fake_redis, monkeypatch):
    monkeypatch.setattr(
        "app.services.webhook_delivery.get_settings",
        lambda: mock.Mock(webhook_stream_key="ps"),
    )
    p = Partner(id="p1", name="n", partner_type="ECOMMERCE", status="ACTIVE")
    db_session.add(p)
    sub = PartnerWebhookSubscription(id="s2", partner_id="p1", url="http://u", events="[]", secret=None, is_active=True)
    db_session.add(sub)
    db_session.commit()
    d = webhook_delivery.publish_to_stream(db_session, fake_redis, sub, "evt", {"a": 1})
    assert d.id


def test_worker_custom_handler(db_session, fake_redis):
    fake_redis.xadd("ts2", {"event_type": "x", "payload": "{}", "occurred_at": "now"})
    seen = []

    def h(db, fields):
        seen.append(fields)

    n = webhook_worker.process_stream_batch(
        db=db_session,
        redis_client=fake_redis,
        stream_key="ts2",
        group="g2",
        consumer="c2",
        handler=h,
        count=10,
        block_ms=1,
    )
    assert n == 1
    assert seen


def test_worker_invalid_json(db_session, fake_redis):
    fake_redis.xadd("ts3", {"payload": "not-json"})
    webhook_worker.process_stream_batch(
        db=db_session,
        redis_client=fake_redis,
        stream_key="ts3",
        group="g3",
        consumer="c3",
        count=10,
        block_ms=1,
    )


def test_worker_no_delivery_id(db_session, fake_redis):
    fake_redis.xadd("ts4", {"payload": "{}"})
    webhook_worker.process_stream_batch(
        db=db_session,
        redis_client=fake_redis,
        stream_key="ts4",
        group="g4",
        consumer="c4",
        count=10,
        block_ms=1,
    )


def test_decode_fields_bytes():
    raw = {b"a": b"b"}
    assert webhook_worker._decode_fields(raw) == {"a": "b"}


def test_deliver_http_sync_non_success(monkeypatch):
    class MC:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

        def post(self, url, json=None, headers=None):
            r = mock.Mock()
            r.status_code = 502
            r.is_success = False
            r.text = "bad"
            return r

    monkeypatch.setattr(httpx, "Client", lambda **k: MC())
    sub = PartnerWebhookSubscription(
        id="s1",
        partner_id="p1",
        url="http://test/hook",
        events="[]",
        secret=None,
        is_active=True,
    )
    code, err = webhook_delivery.deliver_http_sync(sub, {})
    assert code == 502
    assert err == "bad"


def test_deliver_http_sync_ok(monkeypatch):
    class MC:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

        def post(self, url, json=None, headers=None):
            r = mock.Mock()
            r.status_code = 200
            r.is_success = True
            r.text = ""
            return r

    monkeypatch.setattr(httpx, "Client", lambda **k: MC())
    sub = PartnerWebhookSubscription(
        id="s1",
        partner_id="p1",
        url="http://test/hook",
        events="[]",
        secret="x",
        is_active=True,
    )
    code, err = webhook_delivery.deliver_http_sync(sub, {"a": 1})
    assert code == 200
    assert err is None


def test_deliver_http_sync_fail(monkeypatch):
    class MC:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return None

        def post(self, url, json=None, headers=None):
            raise OSError("down")

    monkeypatch.setattr(httpx, "Client", lambda **k: MC())
    sub = PartnerWebhookSubscription(
        id="s1",
        partner_id="p1",
        url="http://test/hook",
        events="[]",
        secret=None,
        is_active=True,
    )
    code, err = webhook_delivery.deliver_http_sync(sub, {})
    assert code == 0
    assert err


@pytest.mark.asyncio
async def test_deliver_http_async_ok(monkeypatch):
    class MAC:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def post(self, url, json=None, headers=None):
            r = mock.Mock()
            r.status_code = 201
            r.is_success = True
            r.text = ""
            return r

    monkeypatch.setattr(httpx, "AsyncClient", lambda **k: MAC())
    sub = PartnerWebhookSubscription(
        id="s1",
        partner_id="p1",
        url="http://test/hook",
        events="[]",
        secret=None,
        is_active=True,
    )
    code, err = await webhook_delivery.deliver_http(sub, {})
    assert code == 201
    assert err is None


@pytest.mark.asyncio
async def test_deliver_http_async_non_success(monkeypatch):
    class MAC:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def post(self, url, json=None, headers=None):
            r = mock.Mock()
            r.status_code = 500
            r.is_success = False
            r.text = "failbody"
            return r

    monkeypatch.setattr(httpx, "AsyncClient", lambda **k: MAC())
    sub = PartnerWebhookSubscription(
        id="s1",
        partner_id="p1",
        url="http://test/hook",
        events="[]",
        secret=None,
        is_active=True,
    )
    code, err = await webhook_delivery.deliver_http(sub, {})
    assert code == 500
    assert err == "failbody"


@pytest.mark.asyncio
async def test_deliver_http_async_error(monkeypatch):
    class MAC:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def post(self, url, json=None, headers=None):
            raise RuntimeError("x")

    monkeypatch.setattr(httpx, "AsyncClient", lambda **k: MAC())
    sub = PartnerWebhookSubscription(
        id="s1",
        partner_id="p1",
        url="http://test/hook",
        events="[]",
        secret=None,
        is_active=True,
    )
    code, err = await webhook_delivery.deliver_http(sub, {})
    assert code == 0
    assert err
