from __future__ import annotations

API = "/api/v1/ml-admin"


def test_ml_network_player_by_finance_code(client):
    client.post(f"{API}/ml-locker-network-players/seed-from-catalog")
    r = client.get(f"{API}/ml-locker-network-players/by-finance-code/MAGALU")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == "MAGALU"
    assert body["finance_catalog_code"] == "MAGALU"
