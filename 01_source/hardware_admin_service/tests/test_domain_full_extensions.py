from __future__ import annotations

from unittest.mock import patch

API = "/api/v1/hardware-admin"
CROSS = f"{API}/cross-domain"
RUNTIME = f"{API}/runtime-lockers"
HUB = f"{API}/integration-hub"

MOCK_RUNTIME_LOCKERS = {
    "items": [
        {
            "locker_id": "LOCKER-RUNTIME-01",
            "machine_id": "MACHINE-R-01",
            "display_name": "Runtime Locker",
            "region": "BR-SP",
            "country": "BR",
            "timezone": "America/Sao_Paulo",
            "operator_id": "op-meli",
            "mqtt_region": "br",
            "mqtt_locker_id": "r-01",
            "slot_count_total": 20,
            "active": True,
            "runtime_enabled": True,
            "payment_methods_json": ["PIX"],
        }
    ],
    "total": 1,
}

MOCK_MKT_PARTNERS = {
    "items": [
        {"id": "mcp-magalu", "code": "MAGALU", "name": "Magazine Luiza", "supports_lockers": True},
        {"id": "mcp-inpost", "code": "INPOST", "name": "InPost", "supports_lockers": True},
    ],
    "total": 2,
}


def test_domain_full_seed(client):
    r = client.post(f"{API}/seed/domain-full")
    assert r.status_code == 200
    body = r.json()
    assert body["ecosystem_players"] >= 20
    assert body["network_runtime_lockers"] >= 10
    assert body["player_domain_refs"] >= 20
    assert body["all_carrier_bindings"] >= 50
    assert body["ecosystem_players_total"] >= 20


def test_cross_domain_patch_delete(client):
    client.post(f"{API}/seed")

    r = client.post(
        f"{CROSS}/payment-bindings",
        json={"locker_id": "LOCKER-DEMO-01", "payment_method_code": "BOLETO", "payment_provider_code": "TEST"},
    )
    assert r.status_code == 201
    bid = r.json()["id"]

    r = client.patch(f"{CROSS}/payment-bindings/{bid}", json={"is_active": False})
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    r = client.delete(f"{CROSS}/payment-bindings/{bid}")
    assert r.status_code == 204


def test_runtime_reconcile_pull_push(client):
    client.post(f"{API}/seed/domain-full")

    with patch(
        "app.services.runtime_reconcile_service.runtime_client.list_runtime_registry_lockers",
        return_value=MOCK_RUNTIME_LOCKERS["items"],
    ):
        r = client.post(f"{RUNTIME}/reconcile/pull")
        assert r.status_code == 200
        assert r.json()["inserted"] >= 1

    r = client.get(f"{RUNTIME}/reconcile/diff")
    assert r.status_code == 200
    assert "admin_only" in r.json()

    r = client.post(f"{RUNTIME}/reconcile/push")
    assert r.status_code == 200
    assert r.json()["queued"] >= 1


def test_mirror_marketplace_channel_partners(client):
    client.post(f"{API}/seed/domain-full")

    with patch("httpx.Client.get") as mock_get:
        class Resp:
            status_code = 200

            def raise_for_status(self):
                return None

            def json(self):
                return MOCK_MKT_PARTNERS

        mock_get.return_value = Resp()
        r = client.post(f"{HUB}/mirror-marketplace-channel-partners")
        assert r.status_code == 200
        body = r.json()
        assert body["marketplace_partners"] == 2
        assert body["matched"] >= 1


def test_locker_360_fiscal_ml(client):
    client.post(f"{API}/seed/domain-full")

    with patch("app.services.cross_domain_link_service.fetch_items") as mock_items, patch(
        "app.services.cross_domain_link_service.fetch_json"
    ) as mock_json:

        def items_side(domain, url, params=None):
            if "fiscal-global-ops/corridors" in url:
                return [{"corridor_code": "FISC-EU-INPOST", "name": "EU InPost"}]
            if "fiscal-global-ops/certifications" in url:
                return [{"issuer_code": "INPOST", "certification_type": "CE"}]
            if "ml-locker-network-players" in url:
                return [{"code": "INPOST", "name": "InPost ML"}]
            if "channel-partners" in url:
                return MOCK_MKT_PARTNERS["items"]
            return []

        mock_items.side_effect = items_side
        mock_json.return_value = {"catalog_code": "INPOST"}

        r = client.get(f"{CROSS}/lockers/LOCKER-DEMO-01/360")
        assert r.status_code == 200
        body = r.json()
        assert "fiscal" in body["remote"]
        assert "ml" in body["remote"]
        assert "marketplace" in body["remote"]
