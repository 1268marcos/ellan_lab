from __future__ import annotations

API = "/api/v1/money-cambio-admin"


def test_global_dashboard_after_seed(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/global-ops/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["countries"] >= 10
    assert body["corridors"] >= 1
    assert body["locker_players"] >= 70
    assert body.get("ecosystem_segments", 0) >= 8
    assert body.get("player_relations", 0) >= 25
    assert body["readiness_grade"] in ("A", "B", "C", "D")


def test_locker_players_and_ecosystem_matrix(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/locker-players")
    assert r.status_code == 200
    codes = {x["player_code"] for x in r.json()["items"]}
    assert "INPOST" in codes
    assert "MAGALU" in codes
    assert "DHL" in codes
    assert "CORREIOS" in codes
    assert "WORTEN" in codes

    r = client.get(f"{API}/ecosystem-matrix")
    assert r.status_code == 200
    assert r.json()["total"] >= 70
    magalu = next(x for x in r.json()["items"] if x["player_code"] == "MAGALU")
    assert magalu["fiscal_corridor_code"] == "BR-MAGALU-LOCKER"
    assert magalu["finance_catalog_code"] == "MAGALU"


def test_ecosystem_segments_relations_and_food(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/ecosystem-segments")
    assert r.status_code == 200
    seg_codes = {x["code"] for x in r.json()["items"]}
    assert "FOOD_DELIVERY" in seg_codes
    assert "COLLECTION_POINT" in seg_codes

    r = client.get(f"{API}/player-relations")
    assert r.status_code == 200
    assert r.json()["total"] >= 25
    assert any(x["from_player_code"] == "MAGALU" and x["to_player_code"] == "PONTO_MAGALU" for x in r.json()["items"])

    r = client.get(f"{API}/locker-players?segment=FOOD_DELIVERY")
    codes = {x["player_code"] for x in r.json()["items"]}
    assert "IFOOD" in codes
    assert "UBER_EATS" in codes


def test_operating_country_and_corridor(client):
    client.post(f"{API}/seed")
    r = client.post(
        f"{API}/operating-countries",
        json={
            "country_code": "ZA",
            "name": "África do Sul",
            "default_currency_code": "ZAR",
            "regulatory_zone": "MEA",
        },
    )
    assert r.status_code == 201

    r = client.post(
        f"{API}/payment-corridors",
        json={
            "corridor_code": "ZA-EU-TEST",
            "name": "ZA to EU test",
            "origin_country_code": "ZA",
            "destination_country_code": "DE",
            "transaction_currency": "ZAR",
            "settlement_currency": "EUR",
            "default_spread_bps": 80,
        },
    )
    assert r.status_code == 201

    r = client.get(f"{API}/payment-corridors?origin_country_code=BR")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_method_matrix_and_compliance(client):
    client.post(f"{API}/seed")
    r = client.post(
        f"{API}/method-country-matrix",
        json={
            "country_code": "PT",
            "payment_method_code": "CREDIT_CARD",
            "min_amount_cents": 50,
            "is_instant_settlement": False,
        },
    )
    assert r.status_code == 201

    r = client.get(f"{API}/method-country-matrix?country_code=BR")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/compliance-limits?country_code=BR")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
