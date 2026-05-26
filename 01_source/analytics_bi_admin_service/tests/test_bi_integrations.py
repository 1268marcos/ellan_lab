from __future__ import annotations

API = "/api/v1/analytics-bi-admin"


def test_integration_seed_and_matrix(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/player-integrations/matrix")
    assert r.status_code == 200
    m = r.json()
    assert m["profiles"] >= 10
    assert m["capabilities"] >= 5
    assert m["cross_domain"] >= 3
    assert "LOCKER_NETWORK" in m["by_segment"] or "MARKETPLACE" in m["by_segment"]


def test_integration_profiles_by_segment(client):
    client.post(f"{API}/player-integrations/seed")
    r = client.get(f"{API}/player-integrations/profiles?segment=MARKETPLACE")
    assert r.status_code == 200
    codes = {p["network_player_code"] for p in r.json()["profiles"]}
    assert "MAGALU" in codes or "MERCADOLIVRE" in codes


def test_cross_domain_ml_bi(client):
    client.post(f"{API}/player-integrations/seed")
    r = client.get(f"{API}/player-integrations/cross-domain")
    assert r.status_code == 200
    domains = {x["target_domain"] for x in r.json()["integrations"]}
    assert "ML" in domains
    assert "BI" in domains


def test_catalog_size_after_full_seed(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/bi-locker-network-players")
    assert r.status_code == 200
    assert r.json()["total"] >= 55
    r = client.get(f"{API}/player-integrations/capabilities?player_code=INPOST")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
