from __future__ import annotations

API = "/api/v1/analytics-bi-admin"
EFF = f"{API}/efficiency"


def test_efficiency_seed_and_scorecard(client):
    client.post(f"{API}/seed")
    r = client.get(f"{EFF}/scorecard")
    assert r.status_code == 200
    body = r.json()
    assert "efficiency_score" in body
    assert body["bookmarks_count"] >= 1


def test_dq_checks_and_anomalies(client):
    client.post(f"{API}/seed")
    r = client.post(f"{EFF}/data-quality-checks/run")
    assert r.status_code == 200
    assert r.json()["total"] >= 3

    r = client.get(f"{EFF}/data-quality-checks")
    assert r.status_code == 200
    assert r.json()["total"] >= 3

    r = client.post(f"{EFF}/anomaly-signals/scan")
    assert r.status_code == 200

    r = client.get(f"{EFF}/anomaly-signals")
    assert r.status_code == 200


def test_scheduled_exports_and_pipeline(client):
    client.post(f"{API}/seed")
    r = client.get(f"{EFF}/scheduled-exports")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(f"{EFF}/scheduled-exports/tick")
    assert r.status_code == 200

    r = client.get(f"{EFF}/pipeline-sync")
    assert r.status_code == 200
    assert len(r.json()) >= 1

    r = client.get(f"{API}/integration-hub/unified-efficiency")
    assert r.status_code == 200
    assert "bi" in r.json()


def test_bookmarks_create(client):
    client.post(f"{API}/seed")
    r = client.post(
        f"{EFF}/bookmarks",
        json={
            "label": "Test bookmark",
            "route_path": "/ops/bi-analytics/admin",
            "query_json": {"tab": "efficiency"},
        },
    )
    assert r.status_code == 201
    assert r.json()["label"] == "Test bookmark"
