from __future__ import annotations

import json
from unittest import mock

import fakeredis
import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.middleware.shadow_mode import ShadowModeMiddleware
from app.services import v1_order_bridge
from app.workers import consistency_checker
from app.workers import redis_streams_consumer


async def _ok(_: Request):
    return JSONResponse({"ok": True}, status_code=200)


async def _err(_: Request):
    return JSONResponse({"ok": False}, status_code=500)


def test_consistency_compare_and_log():
    a = {"x": 1, "y": 2}
    b = {"x": 1, "y": 3}
    assert consistency_checker.compare_schemas(a, b, ("x",)) == []
    divs = consistency_checker.compare_schemas(a, b, ("y",))
    assert divs == ["y"]
    consistency_checker.log_divergences(context="t", divergences=[], legacy=a, remote=b)
    consistency_checker.log_divergences(context="t", divergences=divs, legacy=a, remote=b)


def test_redis_streams_consumer_ok():
    r = fakeredis.FakeRedis(decode_responses=True)
    r.xadd("s", {"event_type": "product.created", "payload": json.dumps({"sku_id": "1", "name": "N", "category_id": "C", "amount_cents": 1, "currency": "BRL"}), "occurred_at": "now"})
    seen = []

    def h(et, pl):
        seen.append((et, pl))

    n = redis_streams_consumer.process_stream_batch(
        redis_client=r,
        stream_key="s",
        group="g",
        consumer_name="c1",
        handler=h,
        count=10,
        block_ms=1,
    )
    assert n == 1
    assert seen[0][0] == "product.created"


def test_redis_streams_bad_payload_json():
    r = fakeredis.FakeRedis(decode_responses=True)
    r.xadd("s2", {"event_type": "product.created", "payload": "not-json", "occurred_at": "now"})

    def h(et, pl):
        pass

    redis_streams_consumer.process_stream_batch(
        redis_client=r,
        stream_key="s2",
        group="g2",
        consumer_name="c2",
        handler=h,
        count=10,
        block_ms=1,
    )


def test_redis_streams_empty_batch():
    r = fakeredis.FakeRedis(decode_responses=True)
    n = redis_streams_consumer.process_stream_batch(
        redis_client=r,
        stream_key="empty_stream",
        group="ge",
        consumer_name="ce",
        handler=lambda et, pl: None,
        count=10,
        block_ms=1,
    )
    assert n == 0


def test_redis_streams_payload_not_dict():
    r = fakeredis.FakeRedis(decode_responses=True)
    r.xadd("s4", {"event_type": "product.created", "payload": "42", "occurred_at": "now"})
    seen = []

    def h(et, pl):
        seen.append(pl)

    redis_streams_consumer.process_stream_batch(
        redis_client=r,
        stream_key="s4",
        group="g4",
        consumer_name="c4",
        handler=h,
        count=10,
        block_ms=1,
    )
    assert seen == [{}]


def test_redis_streams_xgroup_create_twice():
    r = fakeredis.FakeRedis(decode_responses=True)
    r.xadd("s5", {"event_type": "e", "payload": "{}", "occurred_at": "x"})
    redis_streams_consumer.process_stream_batch(
        redis_client=r,
        stream_key="s5",
        group="g5",
        consumer_name="c5a",
        handler=lambda et, pl: None,
        count=10,
        block_ms=1,
    )
    redis_streams_consumer.process_stream_batch(
        redis_client=r,
        stream_key="s5",
        group="g5",
        consumer_name="c5b",
        handler=lambda et, pl: None,
        count=10,
        block_ms=1,
    )


def test_redis_streams_handler_raises():
    r = fakeredis.FakeRedis(decode_responses=True)
    r.xadd("s3", {"event_type": "product.created", "payload": "{}", "occurred_at": "now"})

    def h(et, pl):
        raise RuntimeError("boom")

    redis_streams_consumer.process_stream_batch(
        redis_client=r,
        stream_key="s3",
        group="g3",
        consumer_name="c3",
        handler=h,
        count=10,
        block_ms=1,
    )


def test_decode_fields_bytes():
    raw = {b"a": b"b"}
    d = redis_streams_consumer._decode_fields(raw)
    assert d == {"a": "b"}


def test_shadow_middleware_records():
    from app.config import feature_flags
    from app.services import rollback_service

    feature_flags.reset_metrics()
    rollback_service.reset_window()

    app = Starlette(
        routes=[Route("/", _ok)],
        middleware=[Middleware(ShadowModeMiddleware)],
    )
    from starlette.testclient import TestClient

    with TestClient(app) as client:
        client.get("/")
    m = feature_flags.get_metrics()
    assert m["total_requests"] >= 1


def test_shadow_middleware_error_branch():
    from app.config import feature_flags
    from app.services import rollback_service

    feature_flags.reset_metrics()
    rollback_service.reset_window()
    app = Starlette(
        routes=[Route("/", _err)],
        middleware=[Middleware(ShadowModeMiddleware)],
    )
    from starlette.testclient import TestClient

    with TestClient(app) as client:
        client.get("/")
    m = feature_flags.get_metrics()
    assert m["error_responses"] >= 1


def test_shadow_middleware_executes_auto_rollback(monkeypatch):
    from app.config import feature_flags
    from app.core.config import settings
    from app.services import rollback_service

    feature_flags.reset_metrics()
    rollback_service.reset_window()
    monkeypatch.setattr(settings, "rollback_min_samples", 2)
    monkeypatch.setattr(settings, "rollback_error_rate_threshold", 0.2)
    monkeypatch.setattr(settings, "rollback_window_seconds", 3600)
    feature_flags.set_flag_override("AUTO_ROLLBACK_ENABLED", True)
    feature_flags.set_flag_override("USE_CATALOG_SERVICE", True)

    app = Starlette(
        routes=[Route("/", _err)],
        middleware=[Middleware(ShadowModeMiddleware)],
    )
    from starlette.testclient import TestClient

    with TestClient(app) as client:
        client.get("/")
        client.get("/")
    assert feature_flags.use_catalog_service() is False
    feature_flags.set_flag_override("USE_CATALOG_SERVICE", None)
    feature_flags.set_flag_override("AUTO_ROLLBACK_ENABLED", None)


def test_shadow_middleware_inner_exception(monkeypatch):
    from app.config import feature_flags

    def boom(**kwargs):
        raise RuntimeError("x")

    monkeypatch.setattr(feature_flags, "record_http_outcome", boom)
    app = Starlette(
        routes=[Route("/", _ok)],
        middleware=[Middleware(ShadowModeMiddleware)],
    )
    from starlette.testclient import TestClient

    with TestClient(app) as client:
        client.get("/")


def test_shadow_middleware_dispatch_exception():
    async def boom(_: Request):
        raise RuntimeError("x")

    app = Starlette(
        routes=[Route("/", boom)],
        middleware=[Middleware(ShadowModeMiddleware)],
    )
    from starlette.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as client:
        client.get("/")


def test_run_shadow_non_dict_cache():
    with mock.patch("app.services.v1_order_bridge.catalog_client.fetch_product_safe", return_value={"order_pickup_cache": [1, 2]}):
        v1_order_bridge.run_shadow_compare("sku")


def test_run_shadow_no_remote():
    with mock.patch("app.services.v1_order_bridge.catalog_client.fetch_product_safe", return_value=None):
        v1_order_bridge.run_shadow_compare("sku")
