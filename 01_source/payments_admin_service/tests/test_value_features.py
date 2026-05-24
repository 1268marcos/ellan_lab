from __future__ import annotations

API = "/api/v1/payments-admin"


def test_value_features_seed_and_lists(client):
    r = client.post(f"{API}/seed")
    assert r.status_code == 200
    body = r.json()
    assert body.get("integration_milestones", 0) >= 1 or body.get("routing_rules", 0) >= 1

    r = client.get(f"{API}/integration-milestones")
    assert r.status_code == 200
    assert r.json()["total"] >= 5

    r = client.get(f"{API}/settlement-corridors")
    assert r.status_code == 200
    assert r.json()["total"] >= 3

    r = client.get(f"{API}/player-compliance?country_code=BR")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/routing-rules?country_code=BR")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/integration-incidents")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_intelligence_value_endpoints(client):
    client.post(f"{API}/seed")

    r = client.get(f"{API}/intelligence/global-readiness")
    assert r.status_code == 200
    g = r.json()
    assert g["players_total"] >= 30
    assert g["active_routing_rules"] >= 1

    r = client.get(f"{API}/intelligence/ecosystem-graph")
    assert r.status_code == 200
    graph = r.json()
    assert graph["node_count"] >= 10
    assert graph["edge_count"] >= 5

    r = client.get(f"{API}/intelligence/routing-suggest?country_code=BR&payment_method=PIX&sales_channel=MARKETPLACE")
    assert r.status_code == 200
    assert r.json()["primary_player_code"] == "MERCADOPAGO"

    r = client.get(f"{API}/intelligence/summary")
    assert r.status_code == 200
    assert r.json()["open_integration_incidents"] >= 0
    assert r.json()["routing_rules_active"] >= 1


def test_milestone_and_routing_crud(client):
    client.post(f"{API}/seed")

    r = client.post(
        f"{API}/integration-milestones",
        json={
            "player_code": "INPOST",
            "phase": "PILOT",
            "title": "Test milestone CRUD",
            "status": "PLANNED",
            "owner_team": "qa",
        },
    )
    assert r.status_code == 201
    mid = r.json()["id"]

    r = client.patch(f"{API}/integration-milestones/{mid}", json={"status": "IN_PROGRESS"})
    assert r.status_code == 200
    assert r.json()["status"] == "IN_PROGRESS"

    r = client.delete(f"{API}/integration-milestones/{mid}")
    assert r.status_code == 204

    r = client.post(
        f"{API}/routing-rules",
        json={
            "rule_code": "TEST-BR-PIX",
            "country_code": "BR",
            "payment_method": "PIX",
            "primary_player_code": "MERCADOPAGO",
            "priority": 5,
            "rationale": "test rule",
        },
    )
    assert r.status_code == 201
    rid = r.json()["id"]

    r = client.patch(f"{API}/routing-rules/{rid}", json={"is_active": False})
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    r = client.delete(f"{API}/routing-rules/{rid}")
    assert r.status_code == 204
