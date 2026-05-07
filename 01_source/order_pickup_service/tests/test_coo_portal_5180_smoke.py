"""COO 5180: contrato OpenAPI (sem DB) + smoke opcional com Postgres (RUN_COO_LIVE=1)."""

from __future__ import annotations

import os
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.coo import router as coo_router
from app.routers.coo.deps import require_coo_access
from app.schemas.coo import CooWidgetsSummary


def _minimal_coo_client() -> TestClient:
    a = FastAPI()
    a.include_router(coo_router)

    def _allow() -> None:
        return None

    a.dependency_overrides[require_coo_access] = _allow
    return TestClient(a)


EXPECTED_PATHS = frozenset(
    {
        "/api/v1/coo/meta",
        "/api/v1/coo/dashboard/consolidated",
        "/api/v1/coo/health/pickups",
        "/api/v1/coo/deadlines/urgent",
        "/api/v1/coo/logistics/manifests/active",
        "/api/v1/coo/logistics/routing/realtime",
        "/api/v1/coo/logistics/inventory/by-depot",
        "/api/v1/coo/suppliers/sla",
        "/api/v1/coo/suppliers/penalties",
        "/api/v1/coo/suppliers/compliance",
        "/api/v1/coo/kpis/network/uptime",
        "/api/v1/coo/kpis/mttr",
        "/api/v1/coo/kpis/fleet/efficiency",
        "/api/v1/coo/approvals/pending",
        "/api/v1/coo/approvals/sla/adjust",
        "/api/v1/coo/approvals/expansion",
        "/api/v1/coo/widgets/summary",
    }
)


def test_coo_openapi_paths_registered() -> None:
    a = FastAPI()
    a.include_router(coo_router)
    spec = a.openapi()
    paths: dict[str, Any] = spec.get("paths") or {}
    missing = sorted(p for p in EXPECTED_PATHS if p not in paths)
    assert not missing, f"paths ausentes no OpenAPI: {missing}"


def test_widgets_summary_mocked_200(monkeypatch: pytest.MonkeyPatch) -> None:
    sample = CooWidgetsSummary(
        sla_violated_24h=0,
        avg_pickup_time_min=None,
        deliveries_today=0,
        lockers_offline=0,
        cost_per_delivery=None,
    )

    def _fake_widgets(self: Any) -> CooWidgetsSummary:
        return sample

    monkeypatch.setattr(
        "app.services.coo.kpis_service.KPIsService.get_widgets_summary",
        _fake_widgets,
    )
    client = _minimal_coo_client()
    r = client.get("/api/v1/coo/widgets/summary")
    assert r.status_code == 200
    data = r.json()
    assert data["sla_violated_24h"] == 0
    assert set(data.keys()) >= {
        "sla_violated_24h",
        "avg_pickup_time_min",
        "deliveries_today",
        "lockers_offline",
        "cost_per_delivery",
    }


@pytest.fixture(scope="module")
def live_client() -> TestClient:
    if os.getenv("RUN_COO_LIVE") != "1":
        pytest.skip("Defina RUN_COO_LIVE=1 e Postgres com schema válido para smoke live.")
    from app.main import app as full_app

    def _allow() -> None:
        return None

    full_app.dependency_overrides[require_coo_access] = _allow
    with TestClient(full_app) as c:
        yield c
    full_app.dependency_overrides.pop(require_coo_access, None)


@pytest.mark.skipif(os.getenv("RUN_COO_LIVE") != "1", reason="smoke live opcional")
@pytest.mark.parametrize("method, path, body", [("GET", "/api/v1/coo/widgets/summary", None)])
def test_coo_live_smoke_sample(live_client: TestClient, method: str, path: str, body: dict | None) -> None:
    r = live_client.get(path) if method == "GET" else live_client.post(path, json=body or {})
    assert r.status_code == 200
