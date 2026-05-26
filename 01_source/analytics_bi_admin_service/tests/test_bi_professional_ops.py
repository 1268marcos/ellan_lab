from __future__ import annotations

API = "/api/v1/analytics-bi-admin"


def test_professional_ops_seed_and_readiness(client):
    client.post(f"{API}/seed")
    r = client.post(f"{API}/ops-intelligence/seed-professional")
    assert r.status_code == 200
    assert r.json()["readiness_recomputed"] >= 1

    r = client.get(f"{API}/data-readiness")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert "bands" in body

    r = client.get(f"{API}/ops-intelligence/summary")
    assert r.status_code == 200
    assert r.json()["readiness_rows"] >= 1


def test_mart_refresh_lineage_export(client):
    client.post(f"{API}/seed")

    r = client.post(
        f"{API}/mart-refresh-jobs",
        json={"mart_name": "locker_pnl", "triggered_by": "pytest"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "SUCCESS"

    r = client.get(f"{API}/data-lineage")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(f"{API}/export-jobs", json={"dataset_code": "LOCKER_PNL_MONTHLY"})
    assert r.status_code == 200
    assert r.json()["status"] == "SUCCESS"


def test_tier1_global_players_coverage(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/bi-locker-network-players/tier1-coverage")
    assert r.status_code == 200
    body = r.json()
    assert body["tier1_present"] == body["tier1_required"] == 12
    assert body["coverage_pct"] == 100.0
    for code in ("INPOST", "DHL", "MAGALU", "MERCADOLIVRE", "WORTEN", "EL_CORTE_INGLES"):
        assert code in body["tier1_codes"]


def test_taxonomy_and_market_presence(client):
    client.post(f"{API}/seed")

    r = client.get(f"{API}/player-segment-taxonomy")
    assert r.status_code == 200
    assert r.json()["total"] >= 5

    r = client.get(f"{API}/player-market-presence")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/unified-domain-links")
    assert r.status_code == 200
    codes = {x["domain_code"] for x in r.json()["links"]}
    assert "ML" in codes
    assert "BI" in codes
