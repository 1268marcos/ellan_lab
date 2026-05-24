from __future__ import annotations

API = "/api/v1/payments-admin"


def test_seed_and_transaction_crud(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/payment-transactions")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(
        f"{API}/payment-transactions",
        json={
            "order_id": "ORD-TEST-002",
            "gateway": "MERCADOPAGO",
            "amount_cents": 2500,
            "payment_method": "CREDIT_CARD",
            "status": "INITIATED",
        },
    )
    assert r.status_code == 201
    tx_id = r.json()["id"]

    r = client.patch(f"{API}/payment-transactions/{tx_id}", json={"status": "APPROVED"})
    assert r.status_code == 200
    assert r.json()["status"] == "APPROVED"

    r = client.delete(f"{API}/payment-transactions/{tx_id}")
    assert r.status_code == 204


def test_webhook_rotate_secret(client):
    client.post(f"{API}/seed")
    r = client.post(
        f"{API}/webhook-endpoints",
        json={
            "id": "wh-test-01",
            "partner_type": "MARKETPLACE",
            "partner_id": "partner-test",
            "url": "https://hooks.example/test",
        },
    )
    assert r.status_code == 201

    r = client.post(f"{API}/webhook-endpoints/wh-test-01/rotate-secret")
    assert r.status_code == 200
    assert r.json()["secret"].startswith("whsec_")


def test_payment_splits_and_gateway_events(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/payment-splits?order_id=ORD-DEMO-INPOST-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/gateway-events")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
