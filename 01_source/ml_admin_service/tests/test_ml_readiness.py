from __future__ import annotations

API = "/api/v1/ml-admin"


def test_ml_readiness_after_network_seed(client):
    client.post(f"{API}/seed")
    hub = client.get(f"{API}/ml-readiness-hub/summary")
    assert hub.status_code == 200
    assert hub.json()["readiness_rows"] >= 20

    rows = client.get(f"{API}/ml-integration-readiness")
    assert rows.status_code == 200
    assert rows.json()["total"] >= 20

    inpost = next((x for x in rows.json()["items"] if x["network_player_code"] == "INPOST"), None)
    assert inpost is not None
    assert inpost["score_total"] > 0
    assert inpost["readiness_band"] in ("GO_LIVE", "PILOT", "PLANNED", "BLOCKED")

    dash = client.get(f"{API}/dashboard").json()
    assert dash["ml_readiness_rows"] >= 20
