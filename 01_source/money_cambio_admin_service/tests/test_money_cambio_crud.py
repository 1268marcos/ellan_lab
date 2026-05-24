from __future__ import annotations

API = "/api/v1/money-cambio-admin"
CURRENCIES = f"{API}/currencies"
METHODS = f"{API}/payment-method-catalog"
FX = f"{API}/fx-rates"
PARTNERS = f"{API}/integration-partners"


def test_seed_and_currency_crud(client):
    client.post(f"{API}/seed")
    r = client.get(CURRENCIES)
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(
        CURRENCIES,
        json={"code": "CHF", "name": "Franco suíço", "symbol": "CHF", "minor_units": 2},
    )
    assert r.status_code == 201
    item_id = r.json()["id"]

    r = client.patch(f"{CURRENCIES}/{item_id}", json={"is_active": False})
    assert r.status_code == 200
    assert r.json()["is_active"] is False

    r = client.delete(f"{CURRENCIES}/{item_id}")
    assert r.status_code == 204


def test_fx_convert(client):
    client.post(f"{API}/seed")
    r = client.post(
        FX,
        json={
            "base_currency": "USD",
            "quote_currency": "TEST",
            "rate_date": "2026-05-24",
            "rate": "2.5",
        },
    )
    assert r.status_code == 201

    r = client.post(
        f"{FX}/convert",
        json={"amount_cents": 10000, "from_currency": "USD", "to_currency": "TEST", "on_date": "2026-05-24"},
    )
    assert r.status_code == 200
    assert r.json()["to_amount_cents"] == 25000


def test_integration_webhook_and_api_key(client):
    client.post(f"{API}/seed")
    r = client.post(
        PARTNERS,
        json={
            "id": "mc-test-01",
            "name": "Test FX Hub",
            "code": "TEST-FX",
            "partner_type": "FX_FEED",
            "country": "BR",
            "default_currency": "BRL",
        },
    )
    assert r.status_code == 201

    r = client.put(
        f"{PARTNERS}/mc-test-01/webhook",
        json={"url": "https://hooks.example/money", "secret": "whsec_test"},
    )
    assert r.status_code == 200

    r = client.post(f"{PARTNERS}/mc-test-01/api-keys/rotate")
    assert r.status_code == 200
    assert r.json()["api_key"].startswith("mc_")


def test_payment_method_list(client):
    client.post(f"{API}/seed")
    r = client.get(METHODS)
    assert r.status_code == 200
    assert r.json()["total"] >= 1
