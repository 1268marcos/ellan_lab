from __future__ import annotations

API = "/api/v1/privacy-compliance-admin"


def test_ecosystem_players_and_relations(client):
    client.post(f"{API}/seed")

    r = client.get(f"{API}/ecosystem/meta")
    assert r.status_code == 200
    meta = r.json()
    assert meta["player_count"] >= 77
    assert meta["relation_count"] >= 55
    assert "PARCEL_LOCKER" in meta["player_segments"]
    assert "FOOD_DELIVERY" in meta["player_segments"]
    assert "AGGREGATOR" in meta["player_segments"]

    r = client.get(f"{API}/ecosystem/players?player_segment=FOOD_DELIVERY")
    assert r.status_code == 200
    food = r.json()
    assert food["total"] >= 5
    codes = {p["code"] for p in food["items"]}
    assert "IFOOD" in codes
    assert "UBER_EATS" in codes

    r = client.get(f"{API}/ecosystem/players?regulation_code=LGPD")
    assert r.status_code == 200
    lgpd = r.json()
    assert lgpd["total"] >= 15
    lgpd_codes = {p["code"] for p in lgpd["items"]}
    for expected in ("MAGALU", "MELI", "CORREIOS", "SHOPEE", "IFOOD", "OCA", "PICKIT", "REDPACK"):
        assert expected in lgpd_codes

    r = client.get(f"{API}/ecosystem/players?regulation_code=PDPA_SG")
    assert r.status_code == 200
    pdpa_codes = {p["code"] for p in r.json()["items"]}
    for expected in ("LAZADA", "TOKOPEDIA", "SHOPEE", "JT_EXPRESS"):
        assert expected in pdpa_codes

    r = client.get(f"{API}/ecosystem/players?regulation_code=APPI")
    assert r.status_code == 200
    appi_codes = {p["code"] for p in r.json()["items"]}
    for expected in ("YAMATO", "YAMATO_PACK", "SAGAWA", "RAKUTEN"):
        assert expected in appi_codes

    r = client.get(f"{API}/ecosystem/relations?player_code=MELI")
    assert r.status_code == 200
    rels = r.json()
    assert rels["total"] >= 5
    meli_targets = {x["to_player_code"] for x in rels["items"]}
    assert "CORREIOS" in meli_targets
    assert "OCA" in meli_targets
    assert "PICKIT" in meli_targets

    r = client.get(f"{API}/ecosystem/relations?player_code=LAZADA")
    assert r.status_code == 200
    lazada_rels = r.json()
    assert lazada_rels["total"] >= 2
    lazada_targets = {x["to_player_code"] for x in lazada_rels["items"]}
    assert "CAINIAO" in lazada_targets
    assert "JT_EXPRESS" in lazada_targets

    r = client.get(f"{API}/ecosystem/relations?player_code=IFOOD")
    assert r.status_code == 200
    ifood_rels = r.json()
    assert ifood_rels["total"] >= 2
    ifood_targets = {x["to_player_code"] for x in ifood_rels["items"]}
    assert "MAGALU" in ifood_targets
    assert "WORTEN" in ifood_targets

    r = client.get(f"{API}/locker-networks?regulation_code=GDPR&player_segment=CARRIER")
    assert r.status_code == 200
    carriers = r.json()
    assert carriers["total"] >= 5
    assert "UPS" in {p["code"] for p in carriers["items"]}
