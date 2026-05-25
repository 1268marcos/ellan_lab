from __future__ import annotations

from unittest.mock import patch

API = "/api/v1/hardware-admin"
CROSS = f"{API}/cross-domain"

MOCK_GATEWAY_METHODS = {
    "items": [
        {"locker_id": "LOCKER-DEMO-01", "method": "PIX", "is_active": True},
        {"locker_id": "LOCKER-DEMO-01", "method": "CREDIT_CARD", "is_active": True},
    ],
    "total": 2,
}

MOCK_PICKUPS = {
    "items": [
        {"id": "pkp-1", "order_id": "ord-1", "locker_id": "LOCKER-DEMO-01", "status": "PENDING"},
    ],
    "total": 1,
}

MOCK_PAYMENT_CONTEXTS = {
    "items": [{"id": "ctx-1", "order_id": "ord-1", "locker_id": "LOCKER-DEMO-01", "status": "OPEN"}],
    "total": 1,
}

MOCK_PARTNER_PLAYERS = {
    "items": [
        {
            "id": "prt-ep-inpost",
            "player_code": "INPOST",
            "finance_catalog_code": "INPOST",
            "locker_operator_ref": "INPOST-EU",
        },
    ],
    "total": 1,
}


def test_locker_360_and_gaps_scan(client):
    client.post(f"{API}/seed")

    with patch("app.services.cross_domain_link_service.fetch_json") as mock_fetch, patch(
        "app.services.cross_domain_link_service.fetch_items"
    ) as mock_items:

        def items_side(domain, url, params=None):
            if "locker-payment-methods" in url:
                return MOCK_GATEWAY_METHODS["items"]
            if "pickups" in url:
                return MOCK_PICKUPS["items"]
            if "order-context" in url:
                return MOCK_PAYMENT_CONTEXTS["items"]
            if "ecosystem/players" in url:
                return MOCK_PARTNER_PLAYERS["items"]
            return []

        mock_items.side_effect = items_side
        mock_fetch.return_value = {"catalog_code": "INPOST", "input": "INPOST"}

        r = client.get(f"{CROSS}/lockers/LOCKER-DEMO-01/360")
        assert r.status_code == 200
        body = r.json()
        assert body["locker_id"] == "LOCKER-DEMO-01"
        assert body["runtime"] is not None
        assert body["remote"]["payment_gateway"]["total"] == 2
        assert len(body["domain_verifications"]) >= 1

        r = client.get(f"{CROSS}/gaps-scan?locker_id=LOCKER-DEMO-01")
        assert r.status_code == 200
        gaps = r.json()
        assert gaps["lockers_scanned"] == 1
        assert isinstance(gaps["gaps"], list)


def test_verify_domain_references(client):
    client.post(f"{API}/seed")

    with patch("app.services.cross_domain_link_service.fetch_items", return_value=MOCK_GATEWAY_METHODS["items"]):
        r = client.post(f"{CROSS}/domain-references/verify?locker_id=LOCKER-DEMO-01")
        assert r.status_code == 200
        rows = r.json()
        assert len(rows) >= 1
        statuses = {row["status"] for row in rows}
        assert statuses & {"OK", "LOCAL_ONLY", "MISMATCH", "NOT_FOUND", "UNREACHABLE"}


def test_sync_payment_bindings_from_gateway(client):
    client.post(f"{API}/seed")

    with patch("app.services.cross_domain_link_service.fetch_items", return_value=MOCK_GATEWAY_METHODS["items"]):
        r = client.post(f"{CROSS}/payment-bindings/sync-from-gateway?locker_id=LOCKER-DEMO-01&dry_run=true")
        assert r.status_code == 200
        body = r.json()
        assert body["dry_run"] is True
        assert body["gateway_methods"] == 2

        r = client.post(f"{CROSS}/payment-bindings/sync-from-gateway?locker_id=LOCKER-DEMO-01")
        assert r.status_code == 200
        assert r.json()["inserted"] >= 0

        r = client.get(f"{CROSS}/payment-bindings?locker_id=LOCKER-DEMO-01")
        codes = {i["payment_method_code"] for i in r.json()["items"]}
        assert "PIX" in codes or "CREDIT_CARD" in codes


def test_align_ecosystem_with_partner(client):
    client.post(f"{API}/seed")

    with patch("app.services.cross_domain_link_service.fetch_items", return_value=MOCK_PARTNER_PLAYERS["items"]):
        r = client.post(f"{CROSS}/ecosystem-players/align-partner?apply=false")
        assert r.status_code == 200
        body = r.json()
        assert body["apply"] is False
        assert isinstance(body["matched"], list)

        r = client.post(f"{CROSS}/ecosystem-players/align-partner?apply=true")
        assert r.status_code == 200
        assert r.json()["metadata_updated"] >= 0
