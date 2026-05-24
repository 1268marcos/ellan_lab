from __future__ import annotations

API = "/api/v1/finance-admin"

PRIORITY_CODES = {
    "INPOST",
    "DHL",
    "MAGALU",
    "MERCADOLIVRE",
    "AMAZON_BR",
    "DPD",
    "CORREIOS",
    "CTT",
    "WORTEN",
    "EL_CORTE_INGLES",
}


def test_global_locker_catalog_sync_and_priority_players(client):
    r = client.post(f"{API}/locker-network-catalog/sync")
    assert r.status_code == 200
    body = r.json()
    assert body["catalog_upserted"] >= 90
    assert body["partners_created"] >= 1 or body["partners_linked"] >= 40

    r = client.get(f"{API}/locker-network-catalog")
    assert r.status_code == 200
    data = r.json()
    codes = {item["code"] for item in data["items"]}
    missing = PRIORITY_CODES - codes
    assert not missing, f"missing priority players: {missing}"

    r = client.get(f"{API}/locker-network-catalog?parent_group=MARKETPLACE")
    assert r.status_code == 200
    assert r.json()["total"] >= 10

    magalu = next(i for i in data["items"] if i["code"] == "MAGALU")
    assert magalu["finance_partner_id"] is not None
    assert magalu["finance_partner_code"] == "MAGALU"
    assert magalu["supports_marketplace"] is True

    inpost = next(i for i in data["items"] if i["code"] == "INPOST")
    assert inpost["supports_lockers"] is True
    assert inpost["global_tier"] == "GLOBAL"

    r = client.get(f"{API}/locker-network-catalog/world-priority-index")
    assert r.status_code == 200
    idx_codes = {x["code"] for x in r.json()["items"]}
    assert PRIORITY_CODES <= idx_codes

    r = client.get(f"{API}/locker-network-catalog/relations?catalog_code=MAGALU")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
