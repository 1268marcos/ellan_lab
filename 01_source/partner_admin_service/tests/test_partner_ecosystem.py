from __future__ import annotations

API = "/api/v1/partner-admin"
DEMO = "partner_demo_001"

PRIORITY_EXPECTED = {
    "INPOST",
    "DHL",
    "DPD",
    "CTT",
    "CORREIOS",
    "MAGALU",
    "MERCADOLIVRE",
    "AMAZON_BR",
    "WORTEN",
    "EL_CORTE_INGLES",
}


def test_sync_catalog_and_priority_players(client):
    r = client.post(f"{API}/ecosystem/players/sync-catalog")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= len(PRIORITY_EXPECTED)

    r2 = client.get(f"{API}/ecosystem/players", params={"priority_only": True})
    assert r2.status_code == 200
    codes = {p["code"] for p in r2.json()["items"]}
    assert PRIORITY_EXPECTED.issubset(codes)


def test_demo_ecosystem_links_after_seed(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/partners/{DEMO}/ecosystem-links")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 8
    codes = {x["player_code"] for x in data["items"]}
    assert "INPOST" in codes
    assert "MERCADOLIVRE" in codes
    assert "WORTEN" in codes


def test_partner_360_includes_ecosystem_counts(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/partners/{DEMO}/360", params={"partner_type": "ECOMMERCE"})
    assert r.status_code == 200
    body = r.json()
    assert body["ecosystem_links"] >= 8
    assert body["ecosystem_priority_links"] >= 8


def test_priority_partner_records_after_seed(client):
    client.post(f"{API}/seed")
    ec = client.get(f"{API}/ecommerce-partners").json()
    lg = client.get(f"{API}/logistics-partners").json()
    ec_codes = {p["code"] for p in ec["partners"]}
    lg_codes = {p["code"] for p in lg["partners"]}
    assert "MELI" in ec_codes
    assert "MAGALU" in ec_codes
    assert "AMAZON-BR" in ec_codes
    assert "WORTEN" in ec_codes
    assert "INPOST" in lg_codes
    assert "DHL" in lg_codes
    assert "CORREIOS" in lg_codes
    magalu = next(p for p in ec["partners"] if p["code"] == "MAGALU")
    r = client.get(f"{API}/partners/{magalu['id']}/ecosystem-links")
    assert r.status_code == 200
    assert any(x["player_code"] == "MAGALU" for x in r.json()["items"])


def test_create_and_delete_ecosystem_link(client):
    client.post(f"{API}/ecosystem/players/sync-catalog")
    client.post(f"{API}/seed")
    players = client.get(f"{API}/ecosystem/players", params={"priority_only": True}).json()["items"]
    dpd = next(p for p in players if p["code"] == "DPD")
    r = client.post(
        f"{API}/partners/lg-demo-001/ecosystem-links",
        json={
            "ecosystem_player_id": dpd["id"],
            "partner_type": "LOGISTICS",
            "link_role": "CARRIER",
            "integration_status": "LIVE",
        },
    )
    assert r.status_code == 200
    link_id = r.json()["id"]
    del_r = client.delete(f"{API}/partners/lg-demo-001/ecosystem-links/{link_id}")
    assert del_r.status_code == 204
