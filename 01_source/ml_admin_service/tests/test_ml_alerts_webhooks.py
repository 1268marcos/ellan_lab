from __future__ import annotations

API = "/api/v1/ml-admin"


def test_ml_readiness_alerts_list(client):
    client.post(f"{API}/seed")
    client.put(
        f"{API}/ml-capability-webhooks",
        json={
            "network_player_id": client.get(f"{API}/ml-locker-network-players").json()["items"][0]["id"],
            "capability_code": "LOCKER_INVENTORY",
            "url": "https://httpbin.org/post",
            "secret": "whsec_ml",
        },
    )
    alerts = client.get(f"{API}/ml-readiness-alerts")
    assert alerts.status_code == 200
