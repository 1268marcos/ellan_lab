from __future__ import annotations

PREFIX = "/api/v1/capability-admin"


def test_global_ecosystem_seed(client):
    assert client.post(f"{PREFIX}/seed").status_code == 200

    seg = client.get(f"{PREFIX}/ecosystem/segments")
    assert seg.status_code == 200
    assert seg.json()["total"] >= 7

    carriers = client.get(f"{PREFIX}/ecosystem/players", params={"segment_code": "CARRIER"})
    assert carriers.status_code == 200
    assert carriers.json()["total"] >= 10

    food = client.get(f"{PREFIX}/ecosystem/players", params={"segment_code": "FOOD_DELIVERY"})
    assert food.json()["total"] >= 4

    modes = client.get(f"{PREFIX}/ecosystem/integration-modes")
    assert modes.status_code == 200
    assert modes.json()["total"] >= 7

    integrations = client.get(f"{PREFIX}/ecosystem/player-integrations", params={"player_code": "INPOST"})
    assert integrations.status_code == 200
    assert integrations.json()["total"] >= 2

    relations = client.get(f"{PREFIX}/ecosystem/player-relations", params={"from_code": "MAGALU"})
    assert relations.status_code == 200
    assert relations.json()["total"] >= 1

    dash = client.get(f"{PREFIX}/dashboard").json()
    assert dash["ecosystem_players"] >= 46


def test_correios_ctt_players(client):
    client.post(f"{PREFIX}/seed")
    all_players = client.get(f"{PREFIX}/ecosystem/players").json()["items"]
    codes = {p["code"] for p in all_players}
    assert "CORREIOS" in codes
    assert "CTT" in codes
    assert "WORTEN" in codes
    assert "EL_CORTE_INGLES" in codes
