from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal, init_db
from app.main import app
from app.routers import delivery as delivery_router
from app.services import logistics_service, sla_service
from app.workers import sla_monitor


def test_health_and_sla_route(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/health/ready").status_code == 200
    assert client.get("/health/live").json()["status"] == "alive"
    monkeypatch.setattr(delivery_router.sla_service, "fetch_compliance", lambda: {"ok": True, "via": "route"})
    assert client.get("/api/v1/sla/compliance").json()["via"] == "route"


def test_post_and_get_manifest(client: TestClient) -> None:
    r = client.post(
        "/api/v1/manifest",
        json={"shipments": [{"id": "1"}], "locker_id": "L1", "status": "open"},
    )
    assert r.status_code == 201
    mid = r.json()["id"]
    g = client.get(f"/api/v1/manifest/{mid}")
    assert g.status_code == 200
    assert g.json()["locker_id"] == "L1"


def test_get_manifest_404(client: TestClient) -> None:
    assert client.get("/api/v1/manifest/00000000-0000-0000-0000-000000000099").status_code == 404


def test_delivery_track_create_and_update(client: TestClient) -> None:
    a = client.post("/api/v1/delivery/track", json={"tracking": "T1", "eta": "2030-01-01T00:00:00+00:00"})
    assert a.status_code == 201
    b = client.post(
        "/api/v1/delivery/track",
        json={"tracking": "T1", "signature": "sig", "manifest_id": None},
    )
    assert b.status_code == 201
    assert b.json()["signature"] == "sig"
    c = client.post(
        "/api/v1/delivery/track",
        json={"tracking": "T1", "eta": "2032-06-06T00:00:00+00:00"},
    )
    assert c.status_code == 201
    assert c.json()["signature"] == "sig"


def test_delivery_eta_and_404(client: TestClient) -> None:
    r = client.post("/api/v1/delivery/track", json={"tracking": "T2"})
    did = r.json()["id"]
    e = client.get(f"/api/v1/delivery/{did}/eta")
    assert e.status_code == 200
    assert e.json()["eta"] is None
    assert client.get("/api/v1/delivery/bad-id/eta").status_code == 404


def test_sla_compliance_uses_default_on_error() -> None:
    with patch.object(httpx.Client, "get", side_effect=RuntimeError("x")):
        out = sla_service.fetch_compliance()
    assert out["ok"] is False


def test_sla_compliance_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    class R:
        status_code = 200

        def json(self):
            return {"compliance_pct": 99.5, "deadlines": []}

    monkeypatch.setattr(httpx.Client, "get", lambda self, url: R())
    assert sla_service.fetch_compliance(httpx.Client()).get("compliance_pct") == 99.5


def test_sla_compliance_non_200_and_bad_body(monkeypatch: pytest.MonkeyPatch) -> None:
    class R500:
        status_code = 500

        def json(self):
            return {}

    monkeypatch.setattr(httpx.Client, "get", lambda self, url: R500())
    assert sla_service.fetch_compliance(httpx.Client())["ok"] is False

    class RList:
        status_code = 200

        def json(self):
            return [1, 2]

    monkeypatch.setattr(httpx.Client, "get", lambda self, url: RList())
    assert sla_service.fetch_compliance(httpx.Client())["ok"] is False


def test_sla_fetch_own_client_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    class R:
        status_code = 200

        def json(self):
            return {"compliance_pct": 1.0}

    monkeypatch.setattr(httpx.Client, "get", lambda self, url: R())
    assert sla_service.fetch_compliance()["ok"] is True


def test_fetch_locker_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    class R:
        status_code = 200

        def json(self):
            return {"status": "ready"}

    monkeypatch.setattr(httpx.Client, "get", lambda self, url: R())
    assert logistics_service.fetch_locker_status("L9", httpx.Client())["ok"] is True
    assert logistics_service.fetch_locker_status("L9a")["ok"] is True


def test_fetch_locker_bad_status(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.integrations import backend_runtime

    monkeypatch.setattr(backend_runtime, "get_locker_status", lambda lid, c=None: {"ok": False, "data": None})
    assert logistics_service.fetch_locker_status("L8", httpx.Client())["ok"] is False


def test_fetch_locker_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.integrations import backend_runtime

    monkeypatch.setattr(backend_runtime, "get_locker_status", lambda lid, c=None: {"ok": False, "data": None})
    assert logistics_service.fetch_locker_status("L7")["ok"] is False


def test_sla_monitor_run_once(monkeypatch: pytest.MonkeyPatch) -> None:
    init_db()
    db = SessionLocal()
    try:
        monkeypatch.setattr(
            sla_service,
            "fetch_compliance",
            lambda client=None: {"ok": True, "compliance_pct": 88.0},
        )
        assert sla_monitor.run_once(db)["compliance_pct"] == 88.0
    finally:
        db.close()


def test_sla_monitor_overdue(monkeypatch: pytest.MonkeyPatch) -> None:
    init_db()
    db = SessionLocal()
    try:
        past = datetime.now(timezone.utc) - timedelta(days=1)
        logistics_service.track_delivery(db, "TOD", eta=past)
        monkeypatch.setattr(sla_service, "fetch_compliance", lambda client=None: {"ok": False, "compliance_pct": 0.0})
        r = sla_monitor.run_once(db)
        assert r["overdue_count"] >= 1
    finally:
        db.close()


def test_overdue_custom_now() -> None:
    init_db()
    db = SessionLocal()
    try:
        logistics_service.track_delivery(db, "TCN", eta=datetime(2020, 1, 1, tzinfo=timezone.utc))
        lst = sla_monitor.overdue_without_signature(db, now=datetime(2025, 1, 1, tzinfo=timezone.utc))
        assert any(d.tracking == "TCN" for d in lst)
    finally:
        db.close()


def test_database_engine_memory_pool() -> None:
    from sqlalchemy.pool import StaticPool

    from app.core import database as dbmod

    assert dbmod.engine_kwargs("postgresql://localhost/db") == {"pool_pre_ping": True}
    sk = dbmod.engine_kwargs("sqlite:///./not_memory.db")
    assert sk["connect_args"]["check_same_thread"] is False
    assert "poolclass" not in sk
    eng = dbmod.create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    eng.dispose()


def test_main_lifespan_redis_down(monkeypatch: pytest.MonkeyPatch) -> None:
    import redis as redis_mod

    def boom(*a, **k):
        raise RuntimeError("down")

    monkeypatch.setattr(redis_mod.Redis, "from_url", staticmethod(boom))
    from app.main import app as app2

    with TestClient(app2) as c:
        assert c.app.state.redis is None


def test_main_lifespan_close_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    import redis as redis_mod

    m = MagicMock()
    m.ping.return_value = True
    m.close.side_effect = RuntimeError("x")
    monkeypatch.setattr(redis_mod.Redis, "from_url", staticmethod(lambda *a, **k: m))
    from app.main import app as app2

    with TestClient(app2):
        pass


def test_post_manifest_value_error(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import manifest_service

    def boom(*a, **k):
        raise ValueError("bad")

    monkeypatch.setattr(manifest_service, "create_manifest_with_events", boom)
    r = client.post("/api/v1/manifest", json={"shipments": [], "locker_id": "Lx"})
    assert r.status_code == 400


def test_health_ready_ping_fails(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    m = MagicMock()
    m.ping.side_effect = RuntimeError("ping")
    monkeypatch.setattr(client.app.state, "redis", m)
    assert client.get("/health/ready").status_code == 503


def test_health_ready_db_fails() -> None:
    from app.core.database import get_db
    from app.main import app as app2

    def override_get_db():
        db = MagicMock()
        db.execute.side_effect = RuntimeError("db")
        yield db

    app2.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app2) as c:
            assert c.get("/health/ready").status_code == 503
    finally:
        app2.dependency_overrides.clear()


def test_health_ready_redis_down(monkeypatch: pytest.MonkeyPatch) -> None:
    import redis as redis_mod

    def boom(*a, **k):
        raise RuntimeError("down")

    monkeypatch.setattr(redis_mod.Redis, "from_url", staticmethod(boom))
    from app.main import app as app2

    with TestClient(app2) as c:
        assert c.get("/health/ready").status_code == 503


def test_track_delivery_update_manifest_id(client: TestClient) -> None:
    m = client.post("/api/v1/manifest", json={"shipments": [], "locker_id": "LX"}).json()["id"]
    client.post("/api/v1/delivery/track", json={"tracking": "TMF"})
    u = client.post("/api/v1/delivery/track", json={"tracking": "TMF", "manifest_id": m}).json()
    assert u["manifest_id"] == m
