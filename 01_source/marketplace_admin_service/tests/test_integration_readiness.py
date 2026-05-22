from __future__ import annotations

API = "/api/v1/marketplace-admin"


def test_integration_readiness_hub_after_seed(client):
    client.post(f"{API}/seed")
    hub = client.get(f"{API}/integration-hub/summary")
    assert hub.status_code == 200
    body = hub.json()
    assert body["readiness_rows"] >= 50
    assert body["avg_score"] > 0
    assert body["bands"].get("GO_LIVE", 0) >= 1
    assert body["open_incidents"] >= 1

    r = client.get(f"{API}/integration-readiness", params={"band": "GO_LIVE"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    top = r.json()["items"][0]
    assert top["score_total"] >= 45
    assert isinstance(top["blockers"], list)

    inc = client.get(f"{API}/integration-incidents")
    assert inc.status_code == 200
    assert inc.json()["total"] >= 1

    audit = client.get(f"{API}/sync-audit-log")
    assert audit.status_code == 200
    assert audit.json()["total"] >= 1

    dash = client.get(f"{API}/dashboard").json()
    assert dash["integration_readiness_rows"] >= 50
    assert dash["integration_go_live"] >= 1
