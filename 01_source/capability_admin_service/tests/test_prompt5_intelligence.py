from __future__ import annotations

PREFIX = "/api/v1/capability-admin"


def test_intelligence_after_seed(client):
    client.post(f"{PREFIX}/seed")

    flags = client.get(f"{PREFIX}/intelligence/feature-flags")
    assert flags.status_code == 200
    assert flags.json()["total"] >= 5

    corridors = client.get(f"{PREFIX}/intelligence/corridors")
    assert corridors.status_code == 200
    assert corridors.json()["total"] >= 4

    readiness = client.get(f"{PREFIX}/intelligence/readiness")
    assert readiness.status_code == 200
    assert readiness.json()["total"] >= 5
    first = readiness.json()["items"][0]
    assert "score" in first
    assert "grade" in first

    insights = client.get(f"{PREFIX}/intelligence/insights")
    assert insights.status_code == 200

    recs = client.get(f"{PREFIX}/intelligence/recommendations")
    assert recs.status_code == 200

    report = client.get(f"{PREFIX}/intelligence/world-report")
    assert report.status_code == 200
    body = report.json()
    assert "dashboard" in body
    assert body["readiness"]["profiles_scored"] >= 5
    assert "matrix_coverage_pct" in body


def test_recompute_and_flag_patch(client):
    client.post(f"{PREFIX}/seed")
    r = client.post(f"{PREFIX}/intelligence/recompute")
    assert r.status_code == 200
    assert r.json()["readiness_profiles"] >= 5

    patch = client.patch(
        f"{PREFIX}/intelligence/feature-flags/MATRIX_STRICT_MODE",
        json={"is_enabled": True},
    )
    assert patch.status_code == 200
    assert patch.json()["is_enabled"] is True
