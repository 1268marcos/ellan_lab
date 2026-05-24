from __future__ import annotations

API = "/api/v1/payments-admin"


def test_seed_ecosystem_and_intelligence(client):
    r = client.post(f"{API}/seed")
    assert r.status_code == 200
    assert r.json()["ecosystem_players"] >= 30
    assert r.json().get("player_relations", 0) >= 10

    r = client.get(f"{API}/intelligence/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["transactions_total"] >= 1
    assert body["ecosystem_players_total"] >= 30
    assert body["ecosystem_players_live"] >= 1
    assert body["priority_players_live"] >= 10
    assert "INPOST" in body["priority_player_codes"]
    assert "MAGALU" in body["priority_player_codes"]
    assert "LOCKER_NETWORK" in body["segments"] or body["segments"]
    assert body["ecosystem_segments_defined"] >= 8
    assert body["country_coverage_rows"] >= 20
    assert body["integrations_production_ready"] >= 10


def test_ecosystem_professional_endpoints(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/ecosystem-segments")
    assert r.status_code == 200
    codes = {s["code"] for s in r.json()["items"]}
    assert "FOOD_DELIVERY" in codes
    assert "LOGISTICS_PLATFORM" in codes

    r = client.get(f"{API}/player-integrations?min_readiness=70&limit=50")
    assert r.status_code == 200
    assert r.json()["total"] >= 5

    r = client.get(f"{API}/player-integrations/INPOST")
    assert r.status_code == 200
    assert r.json()["player_code"] == "INPOST"
    assert r.json()["readiness_score"] >= 70

    r = client.get(f"{API}/player-integrations/playbook/MARKETPLACE")
    assert r.status_code == 200
    assert "marketplace" in r.json()["linked_domains"]

    r = client.get(f"{API}/player-country-coverage?country_code=BR")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    players = {i["player_code"] for i in r.json()["items"]}
    assert "INPOST" in players or "CORREIOS" in players


def test_order_graph_and_context(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/intelligence/order-graph/ORD-DEMO-INPOST-001")
    assert r.status_code == 200
    g = r.json()
    assert g["order_id"] == "ORD-DEMO-INPOST-001"
    assert g["context"] is not None
    assert len(g["transactions"]) >= 1
    assert len(g["context"]["player_links"]) >= 2

    r = client.get(f"{API}/order-context/by-order/ORD-DEMO-INPOST-001")
    assert r.status_code == 200
    assert r.json()["locker_network_code"] == "INPOST"


def test_player_relations_and_priority_players(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/ecosystem-players?segment=LOCKER_NETWORK")
    assert r.status_code == 200
    codes = {i["code"] for i in r.json()["items"]}
    assert "INPOST" in codes
    assert "SWIPBOX" in codes

    r = client.get(f"{API}/player-relations?from_player=MAGALU")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_reconciliation_batch_and_webhook_retry(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/reconciliation-batches")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/webhook-deliveries?status=PENDING")
    assert r.status_code == 200
    items = r.json()["items"]
    if items:
        rid = items[0]["id"]
        r = client.post(f"{API}/webhook-deliveries/{rid}/retry")
        assert r.status_code == 200
        assert r.json()["status"] == "PENDING"
