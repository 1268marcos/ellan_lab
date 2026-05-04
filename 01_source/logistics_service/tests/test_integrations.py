from unittest.mock import MagicMock, patch

import httpx
import pytest

from app import kafka_events
from app.core.database import SessionLocal, init_db
from app.integrations import backend_runtime, order_lifecycle
from app.services import manifest_service


def test_backend_runtime_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    class R:
        status_code = 200

        def json(self):
            return {"s": 1}

    monkeypatch.setattr(httpx.Client, "get", lambda self, url: R())
    assert backend_runtime.get_locker_status("L1", httpx.Client())["ok"] is True


def test_backend_runtime_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx.Client, "get", lambda *a, **k: (_ for _ in ()).throw(OSError("x")))
    assert backend_runtime.get_locker_status("L2")["ok"] is False


def test_order_lifecycle_deadlines(monkeypatch: pytest.MonkeyPatch) -> None:
    class R:
        status_code = 200

        def json(self):
            return {"deadlines": [{"id": "d1"}]}

    monkeypatch.setattr(httpx.Client, "get", lambda self, url: R())
    out = order_lifecycle.fetch_sla_deadlines(httpx.Client())
    assert out["ok"] is True


def test_manifest_service_locks_out(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(backend_runtime, "get_locker_status", lambda lid, c=None: {"ok": False})
    init_db()
    db = SessionLocal()
    try:
        with pytest.raises(ValueError, match="locker_unreachable"):
            manifest_service.create_manifest_with_events(db, [], "x", "draft")
    finally:
        db.close()


@patch("app.kafka_events.KafkaProducer")
def test_emit_manifest_created_ok(mock_kp: MagicMock) -> None:
    p = MagicMock()
    mock_kp.return_value = p
    m = MagicMock()
    m.kafka_bootstrap_servers = "localhost:9099"
    with patch.object(kafka_events, "get_settings", return_value=m):
        assert kafka_events.emit_manifest_created("m1", "L1", "open") is True


def test_emit_manifest_kafka_send_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    class P:
        def send(self, *a, **k):
            raise RuntimeError("x")

        def flush(self, *a, **k):
            pass

        def close(self):
            pass

    monkeypatch.setattr(kafka_events, "KafkaProducer", lambda **k: P())
    m = MagicMock()
    m.kafka_bootstrap_servers = "localhost:1"
    with patch.object(kafka_events, "get_settings", return_value=m):
        assert kafka_events.emit_manifest_created("m1", "L1", "open") is False


def test_emit_manifest_no_servers() -> None:
    m = MagicMock()
    m.kafka_bootstrap_servers = None
    with patch.object(kafka_events, "get_settings", return_value=m):
        assert kafka_events.emit_manifest_created("m1", "L1", "open") is False


def test_shared_topics_import() -> None:
    from shared.kafka.topics import LOGISTICS_STREAM, MANIFEST_CREATED

    assert LOGISTICS_STREAM == "logistics-stream"
    assert MANIFEST_CREATED == "manifest.created"


def test_order_lifecycle_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    class R:
        status_code = 500

        def json(self):
            return {}

    monkeypatch.setattr(httpx.Client, "get", lambda self, url: R())
    assert order_lifecycle.fetch_sla_deadlines(httpx.Client())["ok"] is False


def test_order_lifecycle_bad_json(monkeypatch: pytest.MonkeyPatch) -> None:
    class R:
        status_code = 200

        def json(self):
            return []

    monkeypatch.setattr(httpx.Client, "get", lambda self, url: R())
    assert order_lifecycle.fetch_sla_deadlines(httpx.Client())["ok"] is False


def test_order_lifecycle_exc(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx.Client, "get", lambda *a, **k: (_ for _ in ()).throw(OSError("e")))
    assert order_lifecycle.fetch_sla_deadlines()["ok"] is False


@patch("app.kafka_events.KafkaProducer")
def test_emit_manifest_close_raises(mock_kp: MagicMock) -> None:
    p = MagicMock()
    p.send.return_value = None
    p.flush.return_value = None
    p.close.side_effect = RuntimeError("c")
    mock_kp.return_value = p
    m = MagicMock()
    m.kafka_bootstrap_servers = "localhost:9099"
    with patch.object(kafka_events, "get_settings", return_value=m):
        assert kafka_events.emit_manifest_created("m1", "L1", "open") is True
