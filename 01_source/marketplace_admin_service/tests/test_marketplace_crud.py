from __future__ import annotations

API = "/api/v1/marketplace-admin"


def test_sellers_products_commissions_reviews_and_integrations(client):
    client.post(f"{API}/seed")

    r = client.post(
        f"{API}/sellers",
        json={
            "legal_name": "Seller Teste SA",
            "tax_id": "11.111.111/0001-11",
            "email": "seller@test.local",
            "commission_pct": "7.50",
        },
    )
    assert r.status_code == 201
    seller_id = r.json()["id"]

    r = client.post(
        f"{API}/seller-products",
        json={
            "seller_id": seller_id,
            "locker_id": "LCK-TEST-01",
            "product_id": "PROD-TEST-01",
            "price_cents": 1990,
            "quantity": 5,
        },
    )
    assert r.status_code == 201
    product_id = r.json()["id"]

    r = client.post(
        f"{API}/commissions",
        json={
            "seller_id": seller_id,
            "order_id": "ord-test-001",
            "commission_rate_pct": "7.50",
            "commission_amount_cents": 149,
            "ellan_fee_cents": 50,
            "payment_gateway_fee_cents": 40,
            "net_to_seller_cents": 1751,
        },
    )
    assert r.status_code == 201
    commission_id = r.json()["id"]

    r = client.patch(f"{API}/commissions/{commission_id}", json={"status": "SETTLED"})
    assert r.status_code == 200
    assert r.json()["status"] == "SETTLED"

    r = client.post(
        f"{API}/seller-reviews",
        json={"seller_id": seller_id, "order_id": "ord-test-001", "rating": 4},
    )
    assert r.status_code == 201

    r = client.put(
        f"{API}/sellers/{seller_id}/webhook",
        json={"url": "https://hooks.test.local/marketplace", "secret": "whsec-test"},
    )
    assert r.status_code == 200

    r = client.post(f"{API}/sellers/{seller_id}/api-keys/rotate")
    assert r.status_code == 200
    assert "api_key" in r.json()

    r = client.get(f"{API}/sellers")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.delete(f"{API}/seller-products/{product_id}")
    assert r.status_code == 204

    r = client.delete(f"{API}/sellers/{seller_id}")
    assert r.status_code == 204
