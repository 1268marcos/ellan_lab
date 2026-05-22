from __future__ import annotations

API = "/api/v1/order-pickup-admin"
EC = f"{API}/ecommerce-partners"
ORDERS = f"{API}/orders"
OUTBOX = f"{API}/integration-outbox"
LIFECYCLE = API


def test_seed_and_partner_crud(client):
    client.post(f"{API}/seed")
    r = client.get(EC)
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(
        EC,
        json={
            "id": "ec-test-99",
            "name": "Test EC",
            "code": "TEST-EC-99",
            "integration_type": "REST",
            "status": "ACTIVE",
        },
    )
    assert r.status_code == 201

    r = client.put(
        f"{API}/partners/ec-test-99/webhook?partner_type=ECOMMERCE",
        json={"url": "https://hooks.example/orders", "secret": "whsec_test"},
    )
    assert r.status_code == 200

    r = client.post(f"{API}/partners/ec-test-99/api-keys/rotate?partner_type=ECOMMERCE")
    assert r.status_code == 200
    assert r.json()["api_key"].startswith("pt_ec_")


def test_orders_pickups_outbox_and_lifecycle(client):
    client.post(f"{API}/seed")
    r = client.get(ORDERS)
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(
        ORDERS,
        json={
            "id": "ord-test-01",
            "amount_cents": 1200,
            "ecommerce_partner_id": "ec-ops-001",
            "status": "PENDING",
            "payment_status": "PENDING",
        },
    )
    assert r.status_code == 201

    r = client.post(
        f"{API}/pickups",
        json={"id": "pkp-test-01", "order_id": "ord-test-01", "locker_id": "L1", "status": "PENDING"},
    )
    assert r.status_code == 201

    r = client.get(f"{API}/pickups/pkp-test-01")
    assert r.status_code == 200

    r = client.post(
        f"{API}/credits",
        json={"order_id": "ord-test-01", "user_id": "usr-1", "amount_cents": 300, "type": "REFUND"},
    )
    assert r.status_code == 201

    r = client.get(f"{LIFECYCLE}/order-items?order_id=ord-seed-demo-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{LIFECYCLE}/pickup-events?pickup_id=pkp-seed-demo-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{LIFECYCLE}/pickup-tokens?order_id=ord-seed-demo-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{LIFECYCLE}/pickup-attempts?order_id=ord-seed-demo-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{LIFECYCLE}/domain-event-outbox")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{OUTBOX}?status=PENDING")
    assert r.status_code == 200
    items = r.json()["items"]
    if items:
        ob_id = items[0]["id"]
        r = client.post(f"{OUTBOX}/{ob_id}/replay")
        assert r.status_code == 200
        assert r.json()["replayed"] is True

    r = client.get(f"{API}/fulfillment-tracking")
    assert r.status_code == 200
    ft_items = r.json()["items"]
    if ft_items:
        ft_id = ft_items[0]["id"]
        r = client.patch(f"{API}/fulfillment-tracking/{ft_id}", json={"status": "PICKED_UP"})
        assert r.status_code == 200
