from __future__ import annotations

API = "/api/v1/money-cambio-admin"


def test_pricing_preview_after_seed(client):
    client.post(f"{API}/seed")
    r = client.post(
        f"{API}/pricing/preview",
        json={
            "amount_cents": 100000,
            "player_code": "MAGALU",
            "country_code": "BR",
            "payment_method_code": "PIX",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["player_code"] == "MAGALU"
    assert body["settlement_cents"] > 0
    assert len(body["lines"]) >= 4
    assert body["rail_allowed"] is True


def test_payment_rails_and_treasury(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/payment-rails?player_code=MAGALU")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/treasury/dashboard")
    assert r.status_code == 200
    assert r.json()["players_active"] >= 70
    assert len(r.json()["exposures"]) >= 1


def test_fx_lock(client):
    client.post(f"{API}/seed")
    r = client.post(
        f"{API}/fx-locks",
        json={"corridor_code": "BR-MAGALU-LOCKER", "amount_cents_ref": 50000, "ttl_hours": 12},
    )
    assert r.status_code == 201
    ref = r.json()["lock_reference"]
    assert r.json()["status"] == "ACTIVE"

    r = client.get(f"{API}/fx-locks")
    assert any(x["lock_reference"] == ref for x in r.json()["items"])
