from __future__ import annotations

API = "/api/v1/hardware-admin"
HUB = f"{API}/integration-hub"


def test_integration_hub_seed_and_summary(client):
    r = client.post(f"{API}/seed")
    assert r.status_code == 200
    body = r.json()
    assert body["segments"] >= 10
    assert body["capabilities"] >= 80
    assert body["player_relations"] >= 5
    assert body["channel_bindings"] >= 6

    r = client.get(f"{HUB}/summary")
    assert r.status_code == 200
    summary = r.json()
    assert summary["segments"] >= 10
    assert summary["ecosystem_players"] >= 20
    assert summary["capabilities"] >= 80
    assert summary["readiness_rows"] >= 20
    assert summary["marketplace_partners_linked"] >= 20
    assert summary["food_delivery_bindings"] >= 2
    assert summary["aggregator_bindings"] >= 2
    assert summary["locker_channel_bindings"] >= 6


def test_integration_hub_lists(client):
    client.post(f"{API}/seed")

    r = client.get(f"{HUB}/segments")
    assert r.status_code == 200
    assert r.json()["total"] >= 10

    r = client.get(f"{HUB}/capabilities?player_code=CORREIOS")
    assert r.status_code == 200
    assert r.json()["total"] >= 4
    codes = {c["capability_code"] for c in r.json()["items"]}
    assert "TRACKING_PUSH" in codes
    assert "LABEL_API" in codes
    assert "LOCKER_INVENTORY" in codes

    r = client.get(f"{HUB}/player-relations?player_code=INPOST")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{HUB}/channel-bindings?locker_id=LOCKER-DEMO-01")
    assert r.status_code == 200
    bindings = r.json()["items"]
    types = {b["channel_type"] for b in bindings}
    assert "FOOD_DELIVERY" in types
    assert "AGGREGATOR" in types


def test_marketplace_bridge_and_readiness(client):
    client.post(f"{API}/seed")

    r = client.get(f"{HUB}/marketplace-bridge")
    assert r.status_code == 200
    bridge = r.json()
    assert bridge["marketplace_partners_linked"] >= 20
    assert bridge["capabilities_catalog_expected"] >= 80
    assert bridge["capabilities_in_sync"] >= 15

    correios = next(i for i in bridge["items"] if i["hardware_player_code"] == "CORREIOS")
    assert correios["marketplace_partner_code"] == "CORREIOS"
    assert correios["in_sync"] is True

    r = client.get(f"{HUB}/integration-readiness?band=GO_LIVE")
    assert r.status_code == 200
    rows = r.json()["items"]
    assert len(rows) >= 3
    assert all(row["readiness_band"] == "GO_LIVE" for row in rows)

    r = client.post(f"{HUB}/sync-marketplace-mirror")
    assert r.status_code == 200
    assert r.json()["capabilities_in_sync"] >= 15
