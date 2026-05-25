from __future__ import annotations

SEC = "/api/v1/partner-admin/security-admin"
PRIORITY = {
    "INPOST",
    "DHL",
    "DPD",
    "MAGALU",
    "MERCADOLIVRE",
    "AMAZON_BR",
    "CORREIOS",
    "CTT",
    "WORTEN",
    "EL_CORTE_INGLES",
}


def test_locker_player_registry_worldwide(client):
    client.post("/api/v1/partner-admin/seed")

    r = client.get(f"{SEC}/locker-players")
    assert r.status_code == 200
    codes = {x["player_code"] for x in r.json()["items"]}
    assert PRIORITY.issubset(codes)

    r = client.get(f"{SEC}/locker-players/priority")
    assert r.status_code == 200
    assert r.json()["priority_count"] >= len(PRIORITY)

    r = client.get(f"{SEC}/locker-players/INPOST/security-profile")
    assert r.status_code == 200
    assert r.json()["player"]["name"] == "InPost"
    assert "HARDWARE" in r.json()["player"]["related_domains"]

    r = client.get(f"{SEC}/user-player-access", params={"user_id": "usr-admin-ops"})
    assert r.status_code == 200
    assert r.json()["total"] >= 3

    s = client.get(f"{SEC}/summary")
    assert s.json()["locker_players"] >= len(PRIORITY)
