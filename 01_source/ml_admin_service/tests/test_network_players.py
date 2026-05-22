from __future__ import annotations

API = "/api/v1/ml-admin"

PRIORITY_EXPECTED = {"INPOST", "DHL", "MAGALU", "MERCADOLIVRE", "AMAZON_BR", "DPD", "CORREIOS", "CTT"}


def test_seed_locker_network_players_from_catalog(client):
    client.post(f"{API}/seed")
    r = client.post(f"{API}/ml-locker-network-players/seed-from-catalog")
    assert r.status_code == 200
    body = r.json()
    assert body["catalog_size"] >= 8
    assert body["inserted"] + body["updated"] >= 8

    r2 = client.get(f"{API}/ml-locker-network-players?active_only=true")
    assert r2.status_code == 200
    codes = {x["code"] for x in r2.json()["items"]}
    assert PRIORITY_EXPECTED.issubset(codes)

    r3 = client.get(f"{API}/ml-network-ml-profiles")
    assert r3.status_code == 200
    assert r3.json()["total"] >= len(PRIORITY_EXPECTED)

    dash = client.get(f"{API}/dashboard").json()
    assert dash["locker_network_players"] >= 8
    assert dash["locker_network_priority"] >= 8
    assert dash["network_ml_profiles"] >= 1

    partners = client.get(f"{API}/ml-data-partners").json()["partners"]
    inpost = next((p for p in partners if p.get("code") == "TELEMETRY-INPOST"), None)
    assert inpost is not None
    assert inpost.get("network_player_code") == "INPOST"


def test_network_players_filter_priority(client):
    client.post(f"{API}/ml-locker-network-players/seed-from-catalog")
    r = client.get(f"{API}/ml-locker-network-players?priority_only=true&active_only=true")
    assert r.status_code == 200
    for item in r.json()["items"]:
        assert item["code"] in r.json()["priority_codes"]
