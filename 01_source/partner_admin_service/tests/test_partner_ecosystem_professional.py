from __future__ import annotations

API = "/api/v1/partner-admin"


def test_seed_professional_ecosystem(client):
    client.post(f"{API}/ecosystem/players/sync-catalog")
    r = client.post(f"{API}/ecosystem/players/seed-professional")
    assert r.status_code == 200
    body = r.json()
    assert body["player_relations"] >= 10
    assert body["market_presence"] >= 20


def test_ecosystem_summary_and_matrix(client):
    client.post(f"{API}/seed")
    s = client.get(f"{API}/ecosystem/players/summary")
    assert s.status_code == 200
    data = s.json()
    assert data["total_players"] >= 80
    assert "LOCKER_NETWORK" in data["by_parent_group"]
    assert "FOOD_DELIVERY" in data["by_parent_group"]
    assert data["player_relations"] >= 10

    m = client.get(f"{API}/ecosystem/players/integration-matrix")
    assert m.status_code == 200
    groups = {g["parent_group"] for g in m.json()}
    assert "LOGISTICS_PLATFORM" in groups
    assert "MARKETPLACE" in groups


def test_relations_include_aggregator(client):
    client.post(f"{API}/seed")
    rels = client.get(f"{API}/ecosystem/players/relations").json()
    types = {r["relation_type"] for r in rels}
    assert "AGGREGATES" in types
    assert "USES_LOCKER_NETWORK" in types
