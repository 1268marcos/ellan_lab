from __future__ import annotations

API = "/api/v1/finance-admin"


def test_ecosystem_intelligence_scan(client):
    client.post(f"{API}/locker-network-catalog/sync")
    client.post(f"{API}/partner-readiness/recompute")

    r = client.post(f"{API}/ecosystem-intelligence/analyze")
    assert r.status_code == 200
    body = r.json()
    assert body["benchmarks_computed"] >= 90
    assert body["health_checks_run"] >= 1
    assert body["insights_created"] + body["insights_updated"] >= 1

    r = client.get(f"{API}/ecosystem-intelligence/dashboard")
    assert r.status_code == 200
    dash = r.json()
    assert dash["players_analyzed"] >= 90
    assert "health_summary" in dash

    r = client.get(f"{API}/ecosystem-intelligence/insights?severity=HIGH")
    assert r.status_code == 200
    assert r.json()["total"] >= 0

    r = client.get(f"{API}/ecosystem-intelligence/benchmarks?limit=5")
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 5

    r = client.get(f"{API}/ecosystem-intelligence/recommendations/MAGALU")
    assert r.status_code == 200
    assert r.json()["catalog_code"] == "MAGALU"

    r = client.post(f"{API}/ecosystem-intelligence/generate-milestones/INPOST")
    assert r.status_code == 200
    # Pode ser 0 se milestones já gerados pelo analyze

    ms = client.get(f"{API}/integration-milestones?catalog_code=INPOST")
    assert ms.json()["total"] >= 1

    r = client.post(f"{API}/jobs/run/ECOSYSTEM_INTELLIGENCE_SCAN")
    assert r.status_code == 200
    assert r.json()["status"] == "COMPLETED"
