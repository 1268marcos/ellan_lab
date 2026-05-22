from __future__ import annotations

API = "/api/v1/partner-admin"


def test_mirror_capability_webhooks(client):
    client.post(f"{API}/ecosystem/players/sync-catalog")
    client.post(f"{API}/ecosystem/players/seed-professional")
    r = client.post(f"{API}/ecosystem/capability-webhooks/mirror-from-capabilities")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 5

    lst = client.get(f"{API}/ecosystem/capability-webhooks", params={"player_code": "INPOST"})
    assert lst.status_code == 200
    items = lst.json()["items"]
    assert len(items) >= 1
    assert items[0]["url"]


def test_capability_webhook_test_ping(client):
    client.post(f"{API}/seed")
    hooks = client.get(f"{API}/ecosystem/capability-webhooks").json()["items"]
    assert hooks
    tid = hooks[0]["id"]
    t = client.post(f"{API}/ecosystem/capability-webhooks/{tid}/test")
    assert t.status_code == 200
    assert t.json()["success"] is True
