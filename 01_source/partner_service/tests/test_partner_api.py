from __future__ import annotations

import asyncio

import httpx
import pytest

from app.core import health
from app.main import _partner_id_for_rate_limit, _should_skip_rate_limit
from app.services import partner_service


def test_health_payload():
    assert health.health_payload()["status"] == "ok"


def test_engine_kwargs_postgres_and_sqlite():
    from app.core.database import _engine_kwargs

    assert _engine_kwargs("postgresql://localhost/db") == {"pool_pre_ping": True}
    sk = _engine_kwargs("sqlite:///:memory:")
    assert "connect_args" in sk and "poolclass" in sk
    sk2 = _engine_kwargs("sqlite:///./file.db")
    assert "connect_args" in sk2 and "poolclass" not in sk2


def test_should_skip_and_partner_path():
    assert _should_skip_rate_limit("/api/v1/health") is True
    assert _should_skip_rate_limit("/metrics") is True
    assert _should_skip_rate_limit("/api/v1/partners/x") is False
    assert _partner_id_for_rate_limit("/api/v1/partners/u1/eligible-lockers", None) == "u1"


def test_create_and_get_partner(client):
    r = client.post(
        "/api/v1/partners",
        json={
            "name": "Acme",
            "partner_type": "ECOMMERCE",
            "legal_name": "Acme LTDA",
            "contact_email": "ops@acme.example",
            "status": "ACTIVE",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Acme"
    assert data["id"]
    assert data.get("api_key", "").startswith("pk_")
    g = client.get(f"/api/v1/partners/{data['id']}")
    assert g.status_code == 200
    assert g.json()["id"] == data["id"]


def test_get_partner_not_found(client):
    r = client.get("/api/v1/partners/00000000-0000-0000-0000-000000000099")
    assert r.status_code == 404


def test_rotate_not_found(client):
    r = client.put("/api/v1/partners/00000000-0000-0000-0000-000000000099/apikey/rotate")
    assert r.status_code == 404


def test_rotate_ok(client):
    pid = client.post("/api/v1/partners", json={"name": "R"}).json()["id"]
    r = client.put(f"/api/v1/partners/{pid}/apikey/rotate")
    assert r.status_code == 200
    assert r.json()["api_key"].startswith("pk_")


def test_eligible_lockers(client):
    pid = client.post("/api/v1/partners", json={"name": "L"}).json()["id"]
    r = client.get(f"/api/v1/partners/{pid}/eligible-lockers")
    assert r.status_code == 200
    assert len(r.json()["lockers"]) == 2
    r2 = client.get(f"/api/v1/partners/{pid}/eligible-lockers?product_sku=HEAVY_ONLY")
    assert len(r2.json()["lockers"]) == 1


def test_eligible_lockers_404(client):
    assert client.get("/api/v1/partners/00000000-0000-0000-0000-000000000099/eligible-lockers").status_code == 404


def test_compatibility(client):
    pid = client.post("/api/v1/partners", json={"name": "C"}).json()["id"]
    b = {"partner_sku": "UNKNOWN_SKU", "locker_id": "locker-m-001"}
    r = client.post(f"/api/v1/partners/{pid}/check-compatibility", json=b)
    assert r.json()["compatible"] is False
    r2 = client.post(
        f"/api/v1/partners/{pid}/check-compatibility",
        json={"partner_sku": "SKU1", "locker_id": "bad-locker"},
    )
    assert r2.json()["reason"] == "LOCKER_NOT_FOUND"
    r3 = client.post(
        f"/api/v1/partners/{pid}/check-compatibility",
        json={"partner_sku": "OVERSIZE", "locker_id": "locker-m-001"},
    )
    assert r3.json()["compatible"] is False
    r4 = client.post(
        f"/api/v1/partners/{pid}/check-compatibility",
        json={"partner_sku": "SKU1", "locker_id": "locker-m-001"},
    )
    assert r4.json()["compatible"] is True


def test_compatibility_partner_404(client):
    r = client.post(
        "/api/v1/partners/00000000-0000-0000-0000-000000000099/check-compatibility",
        json={"partner_sku": "x", "locker_id": "locker-m-001"},
    )
    assert r.status_code == 404


def test_webhooks_flow(client):
    pid = client.post("/api/v1/partners", json={"name": "W"}).json()["id"]
    r = client.post(
        f"/api/v1/partners/{pid}/webhooks",
        json={"url": "https://example.com/hook", "events": ["order.created"], "secret": "s"},
    )
    assert r.status_code == 201
    d = client.get(f"/api/v1/partners/{pid}/webhooks/deliveries")
    assert d.status_code == 200
    assert len(d.json()) >= 1


def test_webhooks_404(client):
    assert (
        client.post(
            "/api/v1/partners/00000000-0000-0000-0000-000000000099/webhooks",
            json={"url": "https://example.com/h"},
        ).status_code
        == 404
    )


def test_metrics_endpoint(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert b"partner_shadow" in r.content or b"python" in r.content.lower()


def test_compare_public_schema():
    a = {"id": "1", "name": "n", "partner_type": "t", "legal_name": None, "contact_email": None, "status": "ACTIVE", "created_at": "x", "updated_at": "y"}
    b = dict(a)
    assert partner_service.compare_public_schema(a, b) == []
    assert "mismatch:name" in str(partner_service.compare_public_schema(a, {**b, "name": "z"}))
    c = {k: v for k, v in a.items() if k != "name"}
    assert any("missing_remote" in x for x in partner_service.compare_public_schema(a, c))
    d = {k: v for k, v in a.items() if k != "status"}
    assert any("missing_local" in x for x in partner_service.compare_public_schema(d, a))


def test_schedule_shadow_disabled(monkeypatch):
    monkeypatch.setenv("SHADOW_MODE_ENABLED", "false")
    from app.core.config import get_settings

    get_settings.cache_clear()
    partner_service.schedule_shadow_compare("p", {})
    get_settings.cache_clear()


def test_schedule_shadow_no_event_loop(monkeypatch):
    monkeypatch.setenv("SHADOW_MODE_ENABLED", "true")
    monkeypatch.setenv("SHADOW_LEGACY_BASE_URL", "http://legacy.test")
    from app.core.config import get_settings

    get_settings.cache_clear()
    partner_service.schedule_shadow_compare("p", {"id": "p"})
    get_settings.cache_clear()
    monkeypatch.delenv("SHADOW_LEGACY_BASE_URL", raising=False)
    monkeypatch.delenv("SHADOW_MODE_ENABLED", raising=False)
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_run_shadow_short_circuit_disabled(monkeypatch):
    monkeypatch.setenv("SHADOW_MODE_ENABLED", "false")
    from app.core.config import get_settings

    get_settings.cache_clear()
    await partner_service.run_shadow_partner_compare("p", {})
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_run_shadow_fetch_error(monkeypatch):
    monkeypatch.setenv("SHADOW_MODE_ENABLED", "true")
    monkeypatch.setenv("SHADOW_LEGACY_BASE_URL", "http://legacy.test")
    from app.core.config import get_settings

    get_settings.cache_clear()

    class BoomClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url):
            raise OSError("boom")

    monkeypatch.setattr(httpx, "AsyncClient", lambda **k: BoomClient())
    await partner_service.run_shadow_partner_compare("p1", {"id": "p1", "name": "n", "partner_type": "t", "legal_name": None, "contact_email": None, "status": "A", "created_at": "c", "updated_at": "u"})
    monkeypatch.delenv("SHADOW_LEGACY_BASE_URL", raising=False)
    monkeypatch.delenv("SHADOW_MODE_ENABLED", raising=False)
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_run_shadow_not_dict(monkeypatch):
    monkeypatch.setenv("SHADOW_MODE_ENABLED", "true")
    monkeypatch.setenv("SHADOW_LEGACY_BASE_URL", "http://legacy.test")
    from app.core.config import get_settings

    get_settings.cache_clear()

    class OkClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url):
            return httpx.Response(200, json=[])

    monkeypatch.setattr(httpx, "AsyncClient", lambda **k: OkClient())
    await partner_service.run_shadow_partner_compare("p1", {"id": "p1", "name": "n", "partner_type": "t", "legal_name": None, "contact_email": None, "status": "A", "created_at": "c", "updated_at": "u"})
    monkeypatch.delenv("SHADOW_LEGACY_BASE_URL", raising=False)
    monkeypatch.delenv("SHADOW_MODE_ENABLED", raising=False)
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_run_shadow_match_and_diverge(monkeypatch):
    monkeypatch.setenv("SHADOW_MODE_ENABLED", "true")
    monkeypatch.setenv("SHADOW_LEGACY_BASE_URL", "http://legacy.test")
    from app.core.config import get_settings

    get_settings.cache_clear()
    payload = {"id": "p1", "name": "n", "partner_type": "t", "legal_name": None, "contact_email": None, "status": "A", "created_at": "c", "updated_at": "u"}

    class MatchClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url):
            return httpx.Response(200, json=dict(payload))

    monkeypatch.setattr(httpx, "AsyncClient", lambda **k: MatchClient())
    await partner_service.run_shadow_partner_compare("p1", dict(payload))

    class DivClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url):
            return httpx.Response(200, json={**payload, "name": "other"})

    monkeypatch.setattr(httpx, "AsyncClient", lambda **k: DivClient())
    await partner_service.run_shadow_partner_compare("p1", dict(payload))
    monkeypatch.delenv("SHADOW_LEGACY_BASE_URL", raising=False)
    monkeypatch.delenv("SHADOW_MODE_ENABLED", raising=False)
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_get_partner_triggers_shadow_task(client, monkeypatch):
    from app.core.config import get_settings

    pid = client.post("/api/v1/partners", json={"name": "Shadow"}).json()["id"]
    monkeypatch.setenv("SHADOW_MODE_ENABLED", "false")
    get_settings.cache_clear()
    snapshot = dict(client.get(f"/api/v1/partners/{pid}").json())
    monkeypatch.setenv("SHADOW_MODE_ENABLED", "true")
    monkeypatch.setenv("SHADOW_LEGACY_BASE_URL", "http://legacy.test")
    get_settings.cache_clear()

    class MatchClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url):
            return httpx.Response(200, json=snapshot)

    monkeypatch.setattr(httpx, "AsyncClient", lambda **k: MatchClient())
    client.get(f"/api/v1/partners/{pid}")
    await asyncio.sleep(0.05)
    monkeypatch.delenv("SHADOW_LEGACY_BASE_URL", raising=False)
    monkeypatch.delenv("SHADOW_MODE_ENABLED", raising=False)
    get_settings.cache_clear()


def test_rate_limit_429(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "2")
    from app.core.config import get_settings

    get_settings.cache_clear()
    pid = client.post("/api/v1/partners", json={"name": "RL"}).json()["id"]
    assert client.get(f"/api/v1/partners/{pid}").status_code == 200
    assert client.get(f"/api/v1/partners/{pid}").status_code == 200
    assert client.get(f"/api/v1/partners/{pid}").status_code == 429
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "5000")
    get_settings.cache_clear()
