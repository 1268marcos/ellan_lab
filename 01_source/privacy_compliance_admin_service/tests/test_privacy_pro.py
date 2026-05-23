from __future__ import annotations

API = "/api/v1/privacy-compliance-admin"


def test_compliance_score_and_compare(client):
    client.post(f"{API}/seed")

    r = client.get(f"{API}/compliance/score?regulation_code=GDPR")
    assert r.status_code == 200
    score = r.json()
    assert score["regulation_code"] == "GDPR"
    assert 0 <= score["score_pct"] <= 100
    assert score["grade"] in ("A", "B", "C", "D", "F")
    assert len(score["dimensions"]) >= 8

    r = client.get(f"{API}/compliance/compare?codes=GDPR,LGPD,CCPA")
    assert r.status_code == 200
    cmp = r.json()
    assert len(cmp["scores"]) == 3
    assert "policy" in cmp["matrix"]


def test_audit_analytics_health(client):
    client.post(f"{API}/seed")

    r = client.get(f"{API}/audit-events?limit=20")
    assert r.status_code == 200
    audit = r.json()
    assert audit["total"] >= 5

    r = client.get(f"{API}/analytics/consents?regulation_code=GDPR&days=90")
    assert r.status_code == 200
    analytics = r.json()
    assert "by_channel" in analytics
    assert "daily" in analytics

    r = client.get(f"{API}/ecosystem/health")
    assert r.status_code == 200
    health = r.json()
    assert health["total"] >= 5
    assert health["avg_score_pct"] >= 0


def test_ropa_graph_breach_timeline_dsr(client):
    client.post(f"{API}/seed")

    r = client.get(f"{API}/ropa/graph?regulation_code=GDPR")
    assert r.status_code == 200
    graph = r.json()
    assert graph["regulation_code"] == "GDPR"
    assert len(graph["nodes"]) >= 1

    breaches = client.get(f"{API}/breach-incidents").json()["items"]
    assert breaches
    bid = breaches[0]["id"]
    r = client.get(f"{API}/breach-incidents/{bid}/timeline")
    assert r.status_code == 200
    timeline = r.json()
    assert timeline["breach_id"] == bid
    assert len(timeline["items"]) >= 4
    assert timeline["regulatory_deadline_hours"] == 72

    dsars = client.get(f"{API}/subject-requests").json()["items"]
    assert dsars
    rid = dsars[0]["id"]
    r = client.get(f"{API}/subject-requests/{rid}/tasks")
    assert r.status_code == 200
    tasks = r.json()
    assert tasks["subject_request_id"] == rid
    assert len(tasks["items"]) >= 3
    assert 0 <= tasks["progress_pct"] <= 100

    task_id = tasks["items"][0]["id"]
    r = client.patch(f"{API}/dsr-tasks/{task_id}", json={"status": "COMPLETED", "assignee": "dpo@ellan.lab"})
    assert r.status_code == 200
    assert r.json()["status"] == "COMPLETED"
