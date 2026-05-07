from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.coo import router as coo_router
from app.routers.coo.deps import require_coo_access


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(coo_router)

    def _allow_coo() -> None:
        return None

    app.dependency_overrides[require_coo_access] = _allow_coo
    return TestClient(app)


def test_coo_meta_returns_payload() -> None:
    client = _build_client()
    r = client.get("/api/v1/coo/meta")
    assert r.status_code == 200
    data = r.json()
    assert data["portal"] == "coo"
    assert data["title"] == "Portal COO"
    assert "api_version" in data
    assert "as_of" in data


def test_coo_meta_forbidden_without_override() -> None:
    app = FastAPI()
    app.include_router(coo_router)
    client = TestClient(app)
    r = client.get("/api/v1/coo/meta")
    assert r.status_code == 403
