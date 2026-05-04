"""Targeted tests for branches that are easy to miss in coverage."""

from __future__ import annotations

import json
from unittest import mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.partner import Partner
from app.models.rate_limit import PartnerRateLimitWindow
from app.models.webhook import PartnerWebhookDelivery, PartnerWebhookSubscription
from app.services import webhook_delivery
from app.workers import webhook_worker


def test_client_health_endpoint(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["service"] == "partner-service"


def test_rate_limit_path_without_partners_segment(client):
    assert client.get("/api/v1/not-a-partner-route").status_code == 404


def test_webhook_deliveries_404(client):
    assert (
        client.get("/api/v1/partners/00000000-0000-0000-0000-000000000099/webhooks/deliveries").status_code
        == 404
    )


def test_rate_limit_window_default_created_at():
    from datetime import datetime, timezone

    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    Session = sessionmaker(bind=eng)
    db = Session()
    p = Partner(id="p1", name="n", partner_type="ECOMMERCE", status="ACTIVE")
    db.add(p)
    db.commit()
    row = PartnerRateLimitWindow(partner_id="p1", window_start=datetime.now(timezone.utc), request_count=1)
    db.add(row)
    db.commit()
    db.refresh(row)
    assert row.created_at is not None
    db.close()


@pytest.fixture
def db_session_scope():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    Session = sessionmaker(bind=eng)
    s = Session()
    yield s
    s.close()


def test_worker_xgroup_create_raises_once(db_session_scope):
    m = mock.Mock()
    m.xgroup_create.side_effect = Exception("BUSYGROUP")
    m.xreadgroup.return_value = []
    n = webhook_worker.process_stream_batch(
        db=db_session_scope,
        redis_client=m,
        stream_key="sx",
        group="gx",
        consumer="cx",
        count=10,
        block_ms=1,
    )
    assert n == 0
    m.xgroup_create.assert_called()


def test_worker_delivery_row_missing(db_session_scope, fake_redis):
    fake_redis.xadd(
        "sm",
        {
            "payload": json.dumps({"delivery_id": "00000000-0000-0000-0000-000000000099"}),
        },
    )
    webhook_worker.process_stream_batch(
        db=db_session_scope,
        redis_client=fake_redis,
        stream_key="sm",
        group="gm",
        consumer="cm",
        count=10,
        block_ms=1,
    )


def test_worker_subscription_missing(db_session_scope, fake_redis):
    d = PartnerWebhookDelivery(
        id="d1",
        subscription_id="00000000-0000-0000-0000-000000000099",
        event_type="e",
        payload_json="{}",
        status="PENDING",
        attempts=0,
    )
    db_session_scope.add(d)
    db_session_scope.commit()
    fake_redis.xadd("sm2", {"payload": json.dumps({"delivery_id": "d1"})})
    webhook_worker.process_stream_batch(
        db=db_session_scope,
        redis_client=fake_redis,
        stream_key="sm2",
        group="gm2",
        consumer="cm2",
        count=10,
        block_ms=1,
    )


@pytest.mark.asyncio
async def test_deliver_http_async_with_secret(monkeypatch):
    seen = {}

    class MAC:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def post(self, url, json=None, headers=None):
            seen["headers"] = headers
            r = mock.Mock()
            r.status_code = 200
            r.is_success = True
            r.text = ""
            return r

    monkeypatch.setattr(webhook_delivery.httpx, "AsyncClient", lambda **k: MAC())
    sub = PartnerWebhookSubscription(
        id="s1",
        partner_id="p1",
        url="http://test/hook",
        events="[]",
        secret="sec",
        is_active=True,
    )
    await webhook_delivery.deliver_http(sub, {})
    assert seen["headers"].get("X-Webhook-Secret") == "sec"
