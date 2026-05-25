from __future__ import annotations

API = "/api/v1/hardware-admin"
CROSS = f"{API}/cross-domain"

REQUIRED_PLAYERS = {
    "INPOST",
    "DHL-PACKSTATION",
    "MAGALU",
    "MERCADOLIVRE",
    "AMAZON-HUB-US",
    "AMAZON-BR",
    "DPD-LOCKER",
    "CORREIOS",
    "CTT",
    "WORTEN",
    "EL-CORTE-INGLES",
}


def test_global_locker_players_in_seed(client):
    client.post(f"{API}/seed")
    r = client.get(f"{CROSS}/ecosystem-players")
    assert r.status_code == 200
    codes = {p["player_code"] for p in r.json()["items"]}
    missing = REQUIRED_PLAYERS - codes
    assert not missing, f"missing players: {missing}"


def test_seed_catalog_idempotent(client):
    client.post(f"{API}/seed")
    r1 = client.get(f"{CROSS}/ecosystem-players")
    total1 = r1.json()["total"]
    r2 = client.post(f"{CROSS}/ecosystem-players/seed-catalog")
    assert r2.status_code == 200
    assert r2.json()["inserted"] == 0
    r3 = client.get(f"{CROSS}/ecosystem-players")
    assert r3.json()["total"] == total1
