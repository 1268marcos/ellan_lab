from __future__ import annotations

import hashlib
import json
import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def partner_id_and_key(client: TestClient) -> tuple[str, str]:
    body = {"name": "inv-test", "partner_type": "ECOMMERCE", "status": "ACTIVE"}
    r = client.post("/api/v1/partners", json=body)
    assert r.status_code == 201, r.text
    data = r.json()
    return data["id"], data["api_key"]


def test_inventory_runtime_missing_key(client: TestClient, partner_id_and_key: tuple[str, str]) -> None:
    partner_id, _ = partner_id_and_key
    r = client.get(f"/api/partners/{partner_id}/inventory/runtime")
    assert r.status_code == 401


def test_inventory_runtime_forbidden_key(client: TestClient, partner_id_and_key: tuple[str, str]) -> None:
    partner_id, _ = partner_id_and_key
    r = client.get(f"/api/partners/{partner_id}/inventory/runtime", headers={"X-API-Key": "wrong"})
    assert r.status_code == 403


def test_inventory_runtime_unknown_partner(client: TestClient) -> None:
    r = client.get(
        "/api/partners/00000000-0000-0000-0000-000000000099/inventory/runtime",
        headers={"X-API-Key": "pk_any"},
    )
    assert r.status_code == 404


def test_inventory_runtime_ok_sqlite_empty(client: TestClient, partner_id_and_key: tuple[str, str]) -> None:
    partner_id, api_key = partner_id_and_key
    r = client.get(
        f"/api/partners/{partner_id}/inventory/runtime",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["cached"] is False
    assert body["data"]["lockers"] == []
    assert body["data"]["occupancy"]["total_runtime_slot_rows"] == 0
    assert "ETag" in r.headers
    assert "max-age=30" in r.headers.get("Cache-Control", "")


def test_inventory_runtime_if_none_match_cached(
    client: TestClient, partner_id_and_key: tuple[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    partner_id, api_key = partner_id_and_key
    etag = 'W/"inv:fixed"'

    def fake_fetch(
        pid: str,
        _etag_sql: str,
        _rows_sql: str,
    ) -> tuple[str, list[dict], str | None]:
        assert pid == partner_id
        return etag, [], "2020-01-01"

    monkeypatch.setattr("app.routers.inventory._fetch_etag_and_rows", fake_fetch)
    r1 = client.get(
        f"/api/partners/{partner_id}/inventory/runtime",
        headers={"X-API-Key": api_key},
    )
    assert r1.status_code == 200
    assert r1.json()["cached"] is False
    r2 = client.get(
        f"/api/partners/{partner_id}/inventory/runtime",
        headers={"X-API-Key": api_key, "If-None-Match": etag},
    )
    assert r2.status_code == 200
    j2 = r2.json()
    assert j2["cached"] is True
    assert j2["data"] is None


def test_inventory_allocations_ok(monkeypatch: pytest.MonkeyPatch, client: TestClient, partner_id_and_key) -> None:
    partner_id, api_key = partner_id_and_key

    def fake_fetch(
        pid: str,
        _etag_sql: str,
        _rows_sql: str,
    ) -> tuple[str, list[dict], str | None]:
        return 'W/"inv:a"', [{"id": "a1", "order_id": "o1", "locker_id": "L1", "slot": 3, "state": "OPENED_FOR_PICKUP"}], None

    monkeypatch.setattr("app.routers.inventory._fetch_etag_and_rows", fake_fetch)
    r = client.get(
        f"/api/partners/{partner_id}/inventory/allocations",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert len(body["data"]["allocations"]) == 1
    assert body["data"]["allocations"][0]["id"] == "a1"


def test_inventory_middleware_sets_cache_control(client: TestClient, partner_id_and_key) -> None:
    partner_id, api_key = partner_id_and_key
    r = client.get(
        f"/api/partners/{partner_id}/inventory/allocations",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 200
    assert "Cache-Control" in r.headers


def test_rate_limit_extracts_partner_from_inventory_path(client: TestClient, partner_id_and_key) -> None:
    partner_id, api_key = partner_id_and_key
    for _ in range(3):
        r = client.get(
            f"/api/partners/{partner_id}/inventory/runtime",
            headers={"X-API-Key": api_key},
        )
        assert r.status_code == 200


def test_fixed_uuid_partner_demo_key(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core import database
    from app.models.partner import Partner, PartnerApiKey

    pid = str(uuid.UUID(int=1))
    raw = "pk_test_partner_01"
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    db = database.SessionLocal()
    try:
        db.query(PartnerApiKey).filter(PartnerApiKey.partner_id == pid).delete(synchronize_session=False)
        db.query(Partner).filter(Partner.id == pid).delete(synchronize_session=False)
        db.add(
            Partner(
                id=pid,
                name="demo",
                partner_type="ECOMMERCE",
                legal_name=None,
                contact_email=None,
                status="ACTIVE",
            )
        )
        db.add(
            PartnerApiKey(
                id=str(uuid.uuid4()),
                partner_id=pid,
                key_hash=key_hash,
                key_prefix=raw[:8],
                is_active=True,
            )
        )
        db.commit()
    finally:
        db.close()

    monkeypatch.setattr(
        "app.routers.inventory._fetch_etag_and_rows",
        lambda *_a, **_k: ('W/"inv:x"', [], None),
    )
    r = client.get(f"/api/partners/{pid}/inventory/runtime", headers={"X-API-Key": raw})
    assert r.status_code == 200
    assert json.loads(r.content)["success"] is True
