from __future__ import annotations

API = "/api/v1/locker-create/lockers"


def _create(client):
    client.post(
        API,
        json={
            "id": "LK-WH-001",
            "display_name": "Webhook Locker",
            "region": "SP",
            "city": "Osasco",
            "state": "SP",
        },
    )


def test_webhook_configure_and_get(client):
    _create(client)
    r = client.put(
        f"{API}/LK-WH-001/webhook",
        json={"url": "https://example.com/hooks/locker", "secret": "s3cret", "events": ["locker.created"]},
    )
    assert r.status_code == 200
    assert r.json()["has_secret"] is True

    r = client.get(f"{API}/LK-WH-001/webhook")
    assert r.status_code == 200
    assert "locker.created" in r.json()["events"]
