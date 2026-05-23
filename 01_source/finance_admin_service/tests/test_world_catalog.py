from __future__ import annotations

API = "/api/v1/finance-admin"


def test_world_catalog_segments_relations_and_food_delivery(client):
    r = client.post(f"{API}/locker-network-catalog/sync")
    assert r.status_code == 200
    body = r.json()
    assert body["catalog_upserted"] >= 85
    assert body["segments_upserted"] >= 8
    assert body["relations_upserted"] >= 1

    r = client.get(f"{API}/locker-network-catalog/segments")
    assert r.status_code == 200
    codes = {s["code"] for s in r.json()["items"]}
    assert "FOOD_DELIVERY" in codes
    assert "COLLECTION_POINT" in codes
    assert "LOCKER_NETWORK_OPERATOR" in codes

    r = client.get(f"{API}/locker-network-catalog?segment_code=FOOD_DELIVERY")
    assert r.status_code == 200
    food_codes = {i["code"] for i in r.json()["items"]}
    assert "IFOOD" in food_codes
    assert "RAPPI" in food_codes

    r = client.get(f"{API}/locker-network-catalog?segment_code=COLLECTION_POINT")
    assert r.status_code == 200
    cp = {i["code"] for i in r.json()["items"]}
    assert "PONTO_MAGALU" in cp
    assert "ECI_COLLECTION" in cp

    r = client.get(f"{API}/locker-network-catalog/relations?catalog_code=MAGALU")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
