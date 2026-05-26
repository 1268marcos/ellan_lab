from __future__ import annotations

API = "/api/v1/analytics-bi-admin"
PARTNERS = f"{API}/bi-data-partners"


def test_seed_and_dashboard(client):
    r = client.post(f"{API}/seed")
    assert r.status_code == 200
    assert r.json()["partners"] >= 1

    r = client.get(f"{API}/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["partners"] >= 1
    assert body["kpi_definitions"] >= 1


def test_partner_webhook_and_api_key_rotate(client):
    client.post(f"{API}/seed")
    r = client.post(
        PARTNERS,
        json={
            "id": "bi-partner-test",
            "name": "BI Lab",
            "code": "BI-LAB",
            "partner_type": "WAREHOUSE",
        },
    )
    assert r.status_code == 201

    r = client.put(
        f"{PARTNERS}/bi-partner-test/webhook",
        json={"url": "https://hooks.example/bi/lab", "secret": "whsec_bi"},
    )
    assert r.status_code == 200

    r = client.post(f"{PARTNERS}/bi-partner-test/api-keys/rotate")
    assert r.status_code == 200
    assert r.json()["api_key"].startswith("bi_")


def test_facts_kpis_players(client):
    client.post(f"{API}/seed")

    r = client.post(
        f"{API}/analytics-facts",
        json={
            "fact_key": "test.fact.1",
            "fact_name": "test_event",
            "order_id": "ord-1",
            "payload": {"k": 1},
            "occurred_at": "2026-05-20T12:00:00Z",
        },
    )
    assert r.status_code == 201

    r = client.get(f"{API}/kpi-definitions")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(f"{API}/bi-locker-network-players/seed-global-catalog")
    assert r.status_code == 200
    assert r.json()["players_inserted"] >= 0

    r = client.get(f"{API}/bi-locker-network-players?priority_only=true")
    assert r.status_code == 200
    assert r.json()["total"] >= 8

    r = client.get(f"{API}/bi-locker-network-players/tier1-coverage")
    assert r.status_code == 200
    assert r.json()["tier1_present"] == 12
    codes = set(r.json()["tier1_codes"])
    for required in ("INPOST", "DHL", "MAGALU", "MERCADOLIVRE", "CORREIOS", "CTT", "WORTEN", "EL_CORTE_INGLES"):
        assert required in codes


def test_capability_webhooks(client):
    client.post(f"{API}/seed")
    r = client.post(
        f"{API}/bi-capability-webhooks",
        json={
            "network_player_code": "INPOST",
            "capability_code": "MART_REFRESH",
            "url": "https://hooks.example/inpost/mart",
            "secret": "whsec_cap",
        },
    )
    assert r.status_code == 201
    r = client.get(f"{API}/bi-capability-webhooks")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_integration_hub(client):
    r = client.get(f"{API}/integration-hub/links")
    assert r.status_code == 200
    assert "ml_admin_url" in r.json()
