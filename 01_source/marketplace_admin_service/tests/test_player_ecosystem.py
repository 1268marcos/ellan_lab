from __future__ import annotations

from app.data.channel_players_catalog import CHANNEL_PLAYERS_CATALOG

API = "/api/v1/marketplace-admin"


def test_player_ecosystem_seed_and_world_map(client):
    client.post(f"{API}/seed")
    client.post(f"{API}/channel-partners/seed-players")
    client.post(f"{API}/player-ecosystem/seed")

    m = client.get(f"{API}/player-ecosystem/world-map").json()
    assert m["catalog_players_total"] == len(CHANNEL_PLAYERS_CATALOG)
    assert m["catalog_players_total"] >= 100
    assert m["segments_total"] >= 10
    assert "LOCKER_NETWORK" in m["parent_groups"] or "MARKETPLACE" in m["parent_groups"]


def test_corridors_relationships_integration_plans(client):
    client.post(f"{API}/seed")
    client.post(f"{API}/channel-partners/seed-players")
    client.post(f"{API}/player-ecosystem/seed")

    corridors = client.get(f"{API}/player-ecosystem/corridors").json()
    assert corridors["total"] >= 8
    br = client.get(f"{API}/player-ecosystem/corridors/BR-BR-MARKETPLACE-LOCKER").json()
    assert br["code"] == "BR-BR-MARKETPLACE-LOCKER"
    assert len(br["players"]) >= 4

    rels = client.get(f"{API}/player-ecosystem/relationships").json()
    assert rels["total"] >= 15
    agg = [r for r in rels["relationships"] if r["relationship_type"] == "AGGREGATES_CARRIER"]
    assert len(agg) >= 3

    plans = client.get(f"{API}/sellers/mk-seller-demo-001/integration-plans").json()
    assert plans["total"] >= 4

    ext = client.get(f"{API}/priority-players/extended-world").json()
    assert ext["total"] >= 15
