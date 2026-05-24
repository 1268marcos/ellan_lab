from __future__ import annotations

API = "/api/v1/money-cambio-admin"


def test_intelligence_after_seed(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/money-intelligence/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["players_total"] >= 70
    assert body["settlement_schedules"] >= 3

    r = client.get(f"{API}/money-intelligence/readiness")
    assert r.status_code == 200
    assert r.json()["total"] >= 70
    assert r.json()["avg_score"] >= 0

    r = client.get(f"{API}/money-intelligence/insights")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/money-intelligence/fx-alert-rules")
    assert r.status_code == 200
    assert r.json()["total"] >= 3


def test_analyze_and_resolve_insight(client):
    client.post(f"{API}/seed")
    r = client.post(f"{API}/money-intelligence/analyze")
    assert r.status_code == 200
    assert r.json()["players_scored"] >= 70

    r = client.get(f"{API}/money-intelligence/insights?severity=HIGH")
    assert r.status_code == 200
    items = r.json()["items"]
    if items:
        ins_id = items[0]["id"]
        r = client.post(f"{API}/money-intelligence/insights/{ins_id}/resolve")
        assert r.status_code == 200
        assert r.json()["status"] == "RESOLVED"


def test_fx_alert_rule_and_settlement(client):
    client.post(f"{API}/seed")
    r = client.post(
        f"{API}/money-intelligence/fx-alert-rules",
        json={
            "name": "Test GBP/USD",
            "base_currency": "GBP",
            "quote_currency": "USD",
            "threshold_bps": 50,
        },
    )
    assert r.status_code == 201

    r = client.post(
        f"{API}/money-intelligence/settlement-schedules",
        json={
            "scope_type": "PLAYER",
            "scope_code": "DHL",
            "country_code": "DE",
            "settlement_currency": "EUR",
            "settlement_days": 2,
        },
    )
    assert r.status_code == 201

    r = client.get(f"{API}/money-intelligence/settlement-schedules?scope_code=DHL")
    assert r.status_code == 200
    assert any(x["scope_code"] == "DHL" for x in r.json()["items"])


def test_global_dashboard_includes_intelligence(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/global-ops/dashboard")
    body = r.json()
    assert body.get("open_insights", 0) >= 1
    assert "avg_player_readiness" in body
