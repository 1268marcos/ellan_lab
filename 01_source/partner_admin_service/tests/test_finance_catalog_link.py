from __future__ import annotations

API = "/api/v1/partner-admin"


def test_ecosystem_player_by_finance_catalog_code(client):
    client.post(f"{API}/ecosystem/players/sync-catalog")
    r = client.get(f"{API}/ecosystem/players/by-finance-code/INPOST")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == "INPOST"
    assert body["finance_catalog_code"] == "INPOST"

    r = client.get(f"{API}/ecosystem/players/by-finance-code/MERCADOLIVRE")
    assert r.status_code == 200
    assert r.json()["finance_catalog_code"] == "MERCADOLIVRE"
