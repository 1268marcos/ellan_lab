from __future__ import annotations

API = "/api/v1/fiscal-admin"


def test_global_ops_seed_and_summary(client):
    client.post(f"{API}/seed")
    r = client.post(f"{API}/fiscal-global-ops/seed-global")
    assert r.status_code == 200
    assert r.json().get("jurisdictions", 0) >= 0

    s = client.get(f"{API}/fiscal-global-ops/summary")
    assert s.status_code == 200
    body = s.json()
    assert body["jurisdictions"] >= 8
    assert body["corridors"] >= 1

    j = client.get(f"{API}/fiscal-global-ops/jurisdictions")
    assert j.status_code == 200
    assert j.json()["total"] >= 8

    c = client.get(f"{API}/fiscal-global-ops/corridors")
    assert c.status_code == 200
    assert c.json()["total"] >= 1

    client.post(f"{API}/fiscal-global-ops/integration-readiness/recompute")
    rd = client.get(f"{API}/fiscal-global-ops/integration-readiness")
    assert rd.status_code == 200
    assert rd.json()["total"] >= 1
