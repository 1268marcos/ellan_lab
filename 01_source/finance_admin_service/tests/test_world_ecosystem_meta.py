from __future__ import annotations

API = "/api/v1/finance-admin"


def test_world_ecosystem_sync_meta_and_resolve_alias(client):
    r = client.post(f"{API}/locker-network-catalog/sync")
    assert r.status_code == 200
    body = r.json()
    assert body["catalog_upserted"] >= 90
    assert body["aliases_upserted"] >= 1
    assert body["blueprints_upserted"] >= 1
    assert body["coverage_upserted"] >= 1

    r = client.get(f"{API}/locker-network-catalog")
    codes = {x["code"] for x in r.json()["items"]}
    for code in ("LAZADA", "SF_EXPRESS", "SENDCLOUD", "ALLEGRO", "INSTABOX"):
        assert code in codes, f"missing expansion player {code}"

    r = client.get(f"{API}/locker-network-catalog/resolve/MELI")
    assert r.status_code == 200
    assert r.json()["catalog_code"] == "MERCADOLIVRE"

    r = client.get(f"{API}/locker-network-catalog/aliases?catalog_code=MERCADOLIVRE")
    assert r.status_code == 200
    aliases = {a["alias_code"] for a in r.json()["items"]}
    assert "MELI" in aliases

    r = client.get(f"{API}/locker-network-catalog/integration-blueprints")
    assert r.status_code == 200
    assert r.json()["total"] >= 6

    r = client.get(f"{API}/locker-network-catalog/ecosystem-matrix")
    assert r.status_code == 200
    matrix = r.json()
    assert matrix["total_players"] >= 90
    assert "segments" in matrix

    r = client.get(f"{API}/locker-network-catalog/segments")
    seg_codes = {s["code"] for s in r.json()["items"]}
    assert "CROSS_BORDER_HUB" in seg_codes
    assert "RETAIL_PICKUP" in seg_codes
