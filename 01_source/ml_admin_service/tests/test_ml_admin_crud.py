from __future__ import annotations

API = "/api/v1/ml-admin"
PARTNERS = f"{API}/ml-data-partners"
MODELS = f"{API}/ml-model-metadata"
FEATURES = f"{API}/ml-features-daily"
PREDICTIONS = f"{API}/ml-predictions-log"


def test_seed_and_dashboard(client):
    r = client.post(f"{API}/seed")
    assert r.status_code == 200
    assert r.json()["partners"] >= 1

    r = client.get(f"{API}/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["active_models"] >= 1
    assert body["partners"] >= 1


def test_partner_webhook_and_api_key(client):
    client.post(f"{API}/seed")
    r = client.post(
        PARTNERS,
        json={
            "id": "ml-partner-test",
            "name": "Scoring Lab",
            "code": "SCORING-LAB",
            "partner_type": "SCORING",
        },
    )
    assert r.status_code == 201

    r = client.put(
        f"{PARTNERS}/ml-partner-test/webhook",
        json={"url": "https://hooks.example/ml/scoring", "secret": "whsec_ml"},
    )
    assert r.status_code == 200

    r = client.post(f"{PARTNERS}/ml-partner-test/api-keys/rotate")
    assert r.status_code == 200
    assert r.json()["api_key"].startswith("ml_")


def test_model_features_predictions(client):
    client.post(f"{API}/seed")

    r = client.post(
        MODELS,
        json={"model_version": "rf-v2-test", "metrics": {"auc": 0.9}, "status": "ACTIVE"},
    )
    assert r.status_code == 201
    model_id = r.json()["id"]

    r = client.post(
        FEATURES,
        json={
            "locker_id": "locker-xyz",
            "feature_date": "2026-05-20",
            "battery_min": 65.0,
            "door_failures_7d": 2,
            "usage_events_7d": 10,
            "uptime_hours_7d": 100,
            "failure_label_7d": 0,
        },
    )
    assert r.status_code == 201

    r = client.post(
        PREDICTIONS,
        json={
            "locker_id": "locker-xyz",
            "failure_probability": 0.25,
            "health_score": 75.0,
            "model_version": "rf-v2-test",
        },
    )
    assert r.status_code == 201

    r = client.patch(f"{MODELS}/{model_id}", json={"status": "STALE"})
    assert r.status_code == 200

    r = client.post(f"{API}/ops/validate-feedback")
    assert r.status_code == 200

    r = client.get(f"{API}/ml-prediction-feedback")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
