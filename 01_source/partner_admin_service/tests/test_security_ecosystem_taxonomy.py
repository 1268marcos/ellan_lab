from __future__ import annotations

SEC = "/api/v1/partner-admin/security-admin"

FOOD = {"IFOOD", "UBER_EATS", "GLOVO", "RAPPI"}
PUDO = {"PONTO_MAGALU", "ML_PICKUP_POINT", "AMAZON_HUB"}
AGG = {"MELHOR_ENVIO", "EASYPOST", "SENDCLOUD", "CAINIAO"}


def test_ecosystem_taxonomy_worldwide(client):
    client.post("/api/v1/partner-admin/seed")

    r = client.get(f"{SEC}/ecosystem-taxonomy/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total_players"] >= 50
    assert body["total_relations"] >= 10
    assert body["total_integrations"] >= 10
    assert FOOD.issubset(set(body["food_delivery_players"]))
    assert PUDO.issubset(set(body["collection_point_players"]))

    r = client.get(f"{SEC}/player-segments")
    assert r.status_code == 200
    codes = {x["code"] for x in r.json()["items"]}
    assert "FOOD_DELIVERY" in codes
    assert "COLLECTION_POINT" in codes
    assert "LOCKER_OPERATOR" in codes

    r = client.get(f"{SEC}/player-relations", params={"from_code": "MERCADOLIVRE"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{SEC}/locker-players", params={"segment": "FOOD_DELIVERY"})
    assert r.status_code == 200
    codes = {x["player_code"] for x in r.json()["items"]}
    assert "IFOOD" in codes

    r = client.get(f"{SEC}/locker-players/IFOOD/security-profile")
    assert r.status_code == 200
    assert r.json()["player"]["segment"] == "FOOD_DELIVERY"
