from __future__ import annotations

API = "/api/v1/marketplace-admin"


def test_score_drop_alert_and_capability_webhook(client):
    client.post(f"{API}/seed")
    client.post(f"{API}/capability-webhooks/seed-demo")

    row = client.get(f"{API}/integration-readiness").json()["items"]
    inpost = next(x for x in row if x["partner_code"] == "INPOST")
    assert inpost["score_total"] > 50

    sim = client.post(
        f"{API}/integration-readiness/simulate-drop",
        json={"partner_code": "INPOST", "new_score": 30},
    )
    assert sim.status_code == 200
    assert sim.json()["alerts_created"] >= 1

    alerts = client.get(f"{API}/readiness-alerts").json()
    assert alerts["total"] >= 1
    assert any(a["partner_code"] == "INPOST" for a in alerts["items"])

    hooks = client.get(f"{API}/capability-webhooks", params={"channel_partner_id": "mcp-inpost"})
    assert hooks.status_code == 200
    assert hooks.json()["total"] >= 1

    wh_id = hooks.json()["items"][0]["id"]
    test = client.post(f"{API}/capability-webhooks/{wh_id}/test")
    assert test.status_code == 200
    assert test.json()["success"] is True

    hub = client.get(f"{API}/integration-hub/summary").json()
    assert hub["open_readiness_alerts"] >= 1
