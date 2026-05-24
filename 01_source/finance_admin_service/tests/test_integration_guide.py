from __future__ import annotations

API = "/api/v1/finance-admin"


def test_integration_guide_and_readiness_job(client):
    client.post(f"{API}/locker-network-catalog/sync")

    r = client.get(f"{API}/locker-network-catalog/players/INPOST/integration-guide")
    assert r.status_code == 200
    guide = r.json()
    assert guide["catalog_code"] == "INPOST"
    assert guide["blueprint"] is not None
    assert guide["blueprint"]["primary_capability"]
    assert len(guide["integration_steps"]) >= 3
    assert "cross_refs" in guide

    r = client.post(f"{API}/partner-readiness/recompute")
    assert r.status_code == 200
    assert r.json()["recomputed"] >= 90

    r = client.get(f"{API}/locker-network-catalog/players/INPOST/integration-guide")
    assert r.json()["readiness"] is not None
    assert r.json()["readiness"]["integration_blueprint_code"]

    r = client.post(f"{API}/jobs/run/READINESS_RECOMPUTE")
    assert r.status_code == 200
    assert r.json()["status"] == "COMPLETED"
    assert r.json()["recomputed"] >= 90
