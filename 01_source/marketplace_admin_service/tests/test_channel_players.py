from __future__ import annotations

API = "/api/v1/marketplace-admin"


def test_channel_players_and_seller_links(client):
    client.post(f"{API}/seed")
    r = client.post(f"{API}/channel-partners/seed-players")
    assert r.status_code == 200
    assert r.json().get("capabilities_in_sync") is True

    r = client.get(f"{API}/channel-partners")
    assert r.status_code == 200
    codes = {p["code"] for p in r.json()["partners"]}
    assert "INPOST" in codes
    assert "DHL" in codes
    assert "MAGALU" in codes
    assert "MERCADOLIVRE" in codes
    assert "AMAZON_BR" in codes
    assert "CORREIOS" in codes
    assert "CTT" in codes
    assert "DPD" in codes
    assert "MELHOR_ENVIO" in codes
    assert "MONDIAL_RELAY" in codes

    r = client.get(f"{API}/channel-partners/integration-matrix")
    assert r.status_code == 200
    assert r.json()["total_partners"] >= 30

    r = client.get(f"{API}/channel-partners", params={"lockers_only": True})
    assert r.status_code == 200
    assert all(p["supports_lockers"] for p in r.json()["partners"])

    r = client.get(f"{API}/seller-channel-listings", params={"seller_id": "mk-seller-demo-001"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(
        f"{API}/seller-channel-listings",
        json={
            "seller_id": "mk-seller-demo-001",
            "channel_partner_id": "mcp-shopee",
            "external_store_id": "SHOPEE-DEMO",
        },
    )
    assert r.status_code == 201

    r = client.get(f"{API}/seller-locker-network-links", params={"seller_id": "mk-seller-demo-001"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/channel-partners/mcp-meli")
    assert r.status_code == 200
    assert len(r.json().get("capabilities", [])) >= 1

    dash = client.get(f"{API}/dashboard").json()
    assert dash["channel_partners_active"] >= 30
