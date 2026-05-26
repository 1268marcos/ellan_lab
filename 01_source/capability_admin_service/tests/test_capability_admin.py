from __future__ import annotations

PREFIX = "/api/v1/capability-admin"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_seed_and_dashboard(client):
    r = client.post(f"{PREFIX}/seed")
    assert r.status_code == 200
    assert r.json()["channels"] >= 1
    d = client.get(f"{PREFIX}/dashboard")
    assert d.status_code == 200
    body = d.json()
    assert body["profiles"] >= 1
    assert body["channels"] >= 1


def test_list_profiles(client):
    client.post(f"{PREFIX}/seed")
    r = client.get(f"{PREFIX}/profiles")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_webhook_and_api_key_rotate(client):
    client.post(f"{PREFIX}/seed")
    profiles = client.get(f"{PREFIX}/profiles").json()["items"]
    pid = profiles[0]["id"]
    wh = client.put(
        f"{PREFIX}/webhooks",
        json={"profile_id": pid, "url": "https://example.com/hook", "secret": "s3cret"},
    )
    assert wh.status_code == 200
    rot = client.post(f"{PREFIX}/profiles/{pid}/api-keys/rotate")
    assert rot.status_code == 200
    assert rot.json()["api_key"].startswith("cap_")
