from __future__ import annotations

EC_API = "/api/v1/partner-admin/ecommerce-partners"
BASE = "/api/v1/partner-admin/partners/ec-demo-001"


def test_webhook_and_api_key(client):
    client.post("/api/v1/partner-admin/seed")
    r = client.put(
        f"{BASE}/webhook",
        params={"partner_type": "ECOMMERCE"},
        json={"url": "https://hooks.example/partner", "secret": "s3cret", "events": ["order.created"]},
    )
    assert r.status_code == 200
    assert r.json()["url"].startswith("https://")

    r = client.get(f"{BASE}/webhook", params={"partner_type": "ECOMMERCE"})
    assert r.status_code == 200

    r = client.post(f"{BASE}/api-keys/rotate", params={"partner_type": "ECOMMERCE"})
    assert r.status_code == 200
    assert r.json()["api_key"].startswith("pt_ec_")

    r = client.get(f"{BASE}/api-keys", params={"partner_type": "ECOMMERCE"})
    assert r.status_code == 200
    assert len(r.json()["keys"]) >= 1

    r = client.post(
        f"{BASE}/contacts",
        params={"partner_type": "ECOMMERCE"},
        json={"name": "Ops Contact", "email": "ops@demo.example", "is_primary": True},
    )
    assert r.status_code == 201
