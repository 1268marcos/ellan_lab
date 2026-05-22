from __future__ import annotations

API = "/api/v1/payment-gateway-admin"
METHODS = f"{API}/payment-method-catalog"
PROVIDERS = f"{API}/payment-provider-partners"


def test_seed_and_method_crud(client):
    client.post(f"{API}/seed")
    r = client.get(METHODS)
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(
        METHODS,
        json={"code": "DEBIT_CARD", "name": "Cartão débito", "is_card": True},
    )
    assert r.status_code == 201
    item_id = r.json()["id"]

    r = client.patch(f"{METHODS}/{item_id}", json={"is_active": False})
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    r = client.delete(f"{METHODS}/{item_id}")
    assert r.status_code == 204


def test_provider_webhook_and_api_key(client):
    client.post(f"{API}/seed")
    r = client.post(
        PROVIDERS,
        json={
            "id": "pg-test-01",
            "name": "Test PSP",
            "code": "TEST-PSP",
            "provider_type": "OTHER",
            "region_code": "BR",
        },
    )
    assert r.status_code == 201

    r = client.put(
        f"{PROVIDERS}/pg-test-01/webhook",
        json={"url": "https://hooks.example/payments", "secret": "whsec_test"},
    )
    assert r.status_code == 200

    r = client.post(f"{PROVIDERS}/pg-test-01/api-keys/rotate")
    assert r.status_code == 200
    assert r.json()["api_key"].startswith("pg_")
