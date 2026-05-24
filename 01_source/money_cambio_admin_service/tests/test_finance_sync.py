from __future__ import annotations

import pytest

API = "/api/v1/money-cambio-admin"


MOCK_CATALOG = {
    "items": [
        {
            "id": "fin-1",
            "code": "INPOST",
            "name": "InPost (Finance)",
            "player_role": "LOCKER_OPERATOR",
            "parent_group": "LOCKER_NETWORK",
            "segment_code": "LOCKER_NETWORK",
            "country_code": "PL",
            "regions_json": '["PL","GB"]',
            "supports_lockers": True,
            "supports_marketplace": False,
            "supports_collection_points": False,
            "supports_food_delivery": False,
            "integration_modes_json": "[]",
            "global_tier": "GLOBAL",
            "locker_operator_ref": None,
            "default_billing_model": "HYBRID",
            "default_revenue_share_pct": None,
            "monthly_fee_cents": None,
            "integration_status": "LIVE",
            "estimated_locker_count": None,
            "finance_partner_id": None,
            "finance_partner_code": None,
            "api_docs_url": None,
            "notes": "from finance mock",
            "sort_order": 1,
            "active": True,
            "updated_at": "2026-05-24T00:00:00Z",
        },
        {
            "id": "fin-2",
            "code": "NEW_FIN_PLAYER",
            "name": "New From Finance",
            "player_role": "CARRIER",
            "parent_group": "CARRIER_LAST_MILE",
            "segment_code": "CARRIER_LAST_MILE",
            "country_code": "BR",
            "regions_json": '["BR"]',
            "supports_lockers": True,
            "supports_marketplace": False,
            "supports_collection_points": False,
            "supports_food_delivery": False,
            "integration_modes_json": "[]",
            "global_tier": "REGIONAL",
            "locker_operator_ref": None,
            "default_billing_model": "HYBRID",
            "default_revenue_share_pct": None,
            "monthly_fee_cents": None,
            "integration_status": "PLANNED",
            "estimated_locker_count": None,
            "finance_partner_id": None,
            "finance_partner_code": None,
            "api_docs_url": None,
            "notes": None,
            "sort_order": 2,
            "active": True,
            "updated_at": "2026-05-24T00:00:00Z",
        },
    ],
    "total": 2,
    "by_parent_group": {},
}

MOCK_SEGMENTS = {
    "items": [
        {"code": "LOCKER_NETWORK", "name": "Redes locker", "description": "x", "sort_order": 10},
    ],
    "total": 1,
}

MOCK_RELATIONS = {
    "items": [
        {
            "id": "rel-1",
            "from_catalog_code": "MAGALU",
            "to_catalog_code": "PONTO_MAGALU",
            "relation_type": "WHITE_LABEL",
            "notes": "mock",
        },
    ],
    "total": 1,
}


class _MockFinanceClient:
    base_url = "http://finance-mock/api/v1/finance-admin"

    def trigger_catalog_sync(self, **kwargs):
        return {"catalog_upserted": 2}

    def fetch_catalog(self):
        return list(MOCK_CATALOG["items"])

    def fetch_segments(self):
        return list(MOCK_SEGMENTS["items"])

    def fetch_relations(self):
        return list(MOCK_RELATIONS["items"])


@pytest.fixture
def mock_finance_client(monkeypatch):
    monkeypatch.setattr(
        "app.services.finance_sync_service.FinanceAdminClient",
        lambda *a, **k: _MockFinanceClient(),
    )


def test_sync_finance_admin_endpoint(client, mock_finance_client):
    client.post(f"{API}/seed")
    r = client.post(f"{API}/sync/finance-admin?trigger_finance_sync=true")
    assert r.status_code == 200
    body = r.json()
    assert body["finance_catalog_total"] == 2
    assert body["players_created"] >= 1
    assert body["players_updated"] >= 1

    r = client.get(f"{API}/locker-players")
    codes = {x["player_code"] for x in r.json()["items"]}
    assert "NEW_FIN_PLAYER" in codes

    inpost = next(x for x in r.json()["items"] if x["player_code"] == "INPOST")
    assert "Finance" in inpost["name"] or inpost["name"] == "InPost (Finance)"

    r = client.get(f"{API}/player-relations")
    assert any(
        x["from_player_code"] == "MAGALU" and x["to_player_code"] == "PONTO_MAGALU"
        for x in r.json()["items"]
    )


def test_finance_sync_status(client, mock_finance_client):
    client.post(f"{API}/sync/finance-admin")
    r = client.get(f"{API}/sync/finance-admin/status")
    assert r.status_code == 200
    assert r.json()["last_sync"] is not None
    assert r.json()["last_sync"]["finance_catalog_total"] == 2


def test_finance_sync_unavailable(client, monkeypatch):
    from app.clients.finance_admin_client import FinanceAdminClientError

    class _FailClient:
        base_url = "http://finance-mock/api/v1/finance-admin"

        def trigger_catalog_sync(self, **kwargs):
            raise FinanceAdminClientError("finance_admin_unreachable")

        def fetch_catalog(self):
            raise FinanceAdminClientError("finance_admin_unreachable")

    monkeypatch.setattr(
        "app.services.finance_sync_service.FinanceAdminClient",
        lambda *a, **k: _FailClient(),
    )
    r = client.post(f"{API}/sync/finance-admin?trigger_finance_sync=false")
    assert r.status_code == 503
