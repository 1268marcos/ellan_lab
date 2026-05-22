from __future__ import annotations

API = "/api/v1/ml-admin"


def test_ecosystem_after_network_seed(client):
    client.post(f"{API}/seed")
    client.post(f"{API}/ml-locker-network-players/seed-from-catalog")

    caps = client.get(f"{API}/ml-integration-capabilities")
    assert caps.status_code == 200
    assert caps.json()["total"] >= 8

    pc = client.get(f"{API}/ml-player-capabilities")
    assert pc.status_code == 200
    assert pc.json()["total"] >= 1

    rel = client.get(f"{API}/ml-player-relations")
    assert rel.status_code == 200
    assert rel.json()["total"] >= 5
    types = {r["relation_type"] for r in rel.json()["items"]}
    assert "AGGREGATES" in types

    mp = client.get(f"{API}/ml-market-presence?country=BR")
    assert mp.status_code == 200
    assert mp.json()["total"] >= 1

    summary = client.get(f"{API}/ml-ecosystem/summary").json()
    assert summary["tier1_players"] >= 5
    assert summary["player_relations"] >= 5

    dash = client.get(f"{API}/dashboard").json()
    assert dash["player_capabilities"] >= 1
    assert dash["tier1_players"] >= 5

    players = client.get(f"{API}/ml-locker-network-players?active_only=true").json()["items"]
    inpost = next(p for p in players if p["code"] == "INPOST")
    assert inpost["global_tier"] == "TIER1"
    assert inpost["integration_status"] in ("PILOT", "LIVE", "PLANNED")
