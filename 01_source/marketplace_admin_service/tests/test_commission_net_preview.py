from __future__ import annotations

API = "/api/v1/marketplace-admin"


def test_commission_net_preview(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/commissions/net-preview", params={"price_cents": 10000, "commission_pct": "8.5"})
    assert r.status_code == 200
    body = r.json()
    assert body["price_cents"] == 10000
    assert body["commission_cents"] == 850
    assert body["ellan_fee_cents"] == 299
    assert body["gateway_fee_cents"] == 250
    assert body["net_cents"] == 10000 - round(10000 * (8.5 + 2.99 + 2.5) / 100)
