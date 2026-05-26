from __future__ import annotations

API = "/api/v1/ml-admin"
EFF = f"{API}/efficiency"


def test_ml_efficiency_seed_and_scorecard(client):
    client.post(f"{API}/seed")
    r = client.get(f"{EFF}/scorecard")
    assert r.status_code == 200
    body = r.json()
    assert body["efficiency_score"] >= 0
    assert "inference_requests_7d" in body


def test_inference_usage_and_breaches(client):
    client.post(f"{API}/seed")
    r = client.get(f"{EFF}/inference-usage")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{EFF}/freshness-breaches")
    assert r.status_code == 200


def test_recommendations_generate_and_dismiss(client):
    client.post(f"{API}/seed")
    r = client.post(f"{EFF}/recommendations/generate")
    assert r.status_code == 200

    r = client.get(f"{EFF}/recommendations")
    assert r.status_code == 200
    items = r.json()["recommendations"]
    assert items
    rec_id = items[0]["id"]
    r = client.post(f"{EFF}/recommendations/{rec_id}/dismiss")
    assert r.status_code == 200
    assert r.json()["status"] == "DISMISSED"
