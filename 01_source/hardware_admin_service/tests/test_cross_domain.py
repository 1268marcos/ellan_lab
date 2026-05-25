from __future__ import annotations

API = "/api/v1/hardware-admin"
CROSS = f"{API}/cross-domain"


def test_cross_domain_seed_and_dashboard(client):
    r = client.post(f"{API}/seed")
    assert r.status_code == 200
    body = r.json()
    assert body["ecosystem_players"] >= 20
    assert body["marketplace_links"] >= 8
    assert body["payment_bindings"] >= 2
    assert body["carrier_bindings"] >= 5
    assert body["domain_references"] >= 5
    assert body["capex"] >= 1
    assert body["opex"] >= 2
    assert body["locker_features"] >= 1
    assert body["locker_slots"] >= 4

    r = client.get(f"{CROSS}/dashboard")
    assert r.status_code == 200
    dash = r.json()
    assert dash["ecosystem_players"] >= 20
    assert dash["marketplace_links"] >= 8


def test_cross_domain_crud(client):
    client.post(f"{API}/seed")

    r = client.post(
        f"{CROSS}/ecosystem-players",
        json={
            "player_code": "TEST-PLAYER",
            "name": "Test Player",
            "segment": "LOCKER_NETWORK",
            "primary_country": "BR",
            "marketplace_channel_code": "TEST",
        },
    )
    assert r.status_code == 201

    r = client.post(
        f"{CROSS}/payment-bindings",
        json={
            "locker_id": "LOCKER-TEST-99",
            "payment_method_code": "PIX",
            "payment_provider_code": "MERCADOPAGO",
        },
    )
    assert r.status_code == 201

    r = client.get(f"{CROSS}/payment-bindings?locker_id=LOCKER-TEST-99")
    assert r.status_code == 200
    assert r.json()["total"] == 1


def test_finance_topology(client):
    client.post(f"{API}/seed")

    r = client.get(f"{API}/locker-capex")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/locker-opex")
    assert r.status_code == 200
    assert r.json()["total"] >= 2

    r = client.get(f"{API}/locker-features/LOCKER-DEMO-01")
    assert r.status_code == 200
    assert r.json()["supports_kiosk"] is True

    r = client.get(f"{API}/locker-slots?locker_id=LOCKER-DEMO-01")
    assert r.status_code == 200
    assert r.json()["total"] >= 4
