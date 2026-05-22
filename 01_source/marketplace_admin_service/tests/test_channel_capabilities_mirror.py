from __future__ import annotations

from app.data.channel_players_catalog import (
    CHANNEL_PLAYERS_CATALOG,
    catalog_capability_rows,
    expected_capability_count,
    expected_capabilities_for_partner,
)

API = "/api/v1/marketplace-admin"


def test_catalog_capability_helpers():
    rows = catalog_capability_rows()
    assert len(rows) == expected_capability_count()
    assert expected_capability_count() >= 20
    meli_caps = expected_capabilities_for_partner("mcp-meli")
    assert ("ORDERS_POLL", "REST", "OUTBOUND") in meli_caps
    assert ("SELLER_OAUTH", "OAUTH2", "OUTBOUND") in meli_caps


def test_seed_players_capabilities_mirror_catalog(client):
    r = client.post(f"{API}/channel-partners/seed-players")
    assert r.status_code == 200
    body = r.json()
    expected = expected_capability_count()
    assert body["capabilities_catalog_expected"] == expected
    assert body["capabilities_db_enabled"] == expected
    assert body["capabilities_in_sync"] is True

    # Re-seed idempotente: nenhuma linha extra
    r2 = client.post(f"{API}/channel-partners/seed-players")
    assert r2.status_code == 200
    assert r2.json()["capabilities_db_enabled"] == expected
    assert r2.json()["capabilities_in_sync"] is True

    meli = client.get(f"{API}/channel-partners/mcp-meli").json()
    catalog_meli = {c[0]: (c[1], c[2]) for c in expected_capabilities_for_partner("mcp-meli")}
    assert len(meli["capabilities"]) == len(catalog_meli)
    for cap in meli["capabilities"]:
        assert cap["enabled"] is True
        code = cap["capability_code"]
        assert code in catalog_meli
        assert cap["protocol"] == catalog_meli[code][0]
        assert cap["direction"] == catalog_meli[code][1]

    inpost = client.get(f"{API}/channel-partners/mcp-inpost").json()
    assert len(inpost["capabilities"]) == len(expected_capabilities_for_partner("mcp-inpost"))

    # Player sem capabilities no catalogo => lista vazia no DB
    shopee = next(p for p in CHANNEL_PLAYERS_CATALOG if p["code"] == "SHOPEE")
    assert not shopee.get("capabilities")
    shopee_api = client.get(f"{API}/channel-partners/mcp-shopee").json()
    assert shopee_api["capabilities"] == []
