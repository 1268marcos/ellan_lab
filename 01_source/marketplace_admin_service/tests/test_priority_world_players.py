from __future__ import annotations

from app.data.priority_locker_marketplace_players import PRIORITY_PLAYER_CODES

API = "/api/v1/marketplace-admin"

REQUIRED = {
    "INPOST",
    "DHL",
    "MAGALU",
    "MERCADOLIVRE",
    "AMAZON_BR",
    "DPD",
    "CORREIOS",
    "CTT",
    "WORTEN",
    "EL_CORTE_INGLES",
}


def test_priority_world_players_catalog_and_seller_coverage(client):
    client.post(f"{API}/seed")
    client.post(f"{API}/channel-partners/seed-players")

    world = client.get(f"{API}/priority-players/world-locker-marketplace").json()
    assert world["total"] == len(PRIORITY_PLAYER_CODES)
    codes = {p["code"] for p in world["players"]}
    assert REQUIRED <= codes
    inpost = next(p for p in world["players"] if p["code"] == "INPOST")
    assert inpost["in_catalog"] is True
    assert inpost["supports_lockers"] is True

    cov = client.get(f"{API}/sellers/mk-seller-demo-001/player-coverage").json()
    assert cov["priority_players_total"] >= 10
    assert cov["coverage_complete_count"] >= 8
    assert cov["coverage_pct"] >= 70

    dpd = next(p for p in cov["players"] if p["partner_code"] == "DPD")
    assert dpd["has_locker_network"] is True
    meli = next(p for p in cov["players"] if p["partner_code"] == "MERCADOLIVRE")
    assert meli["has_marketplace_listing"] is True

    dpd_partner = client.get(f"{API}/channel-partners/mcp-dpd").json()
    assert len(dpd_partner["capabilities"]) >= 4

    worten = client.get(f"{API}/channel-partners/mcp-worten").json()
    assert worten["supports_lockers"] is True
    assert len(worten["capabilities"]) >= 2
