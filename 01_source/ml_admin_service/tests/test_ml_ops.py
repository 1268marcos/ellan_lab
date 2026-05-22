from __future__ import annotations

API = "/api/v1/ml-admin"


def test_seed_use_cases_and_registry(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/ml-use-cases")
    assert r.status_code == 200
    assert r.json()["total"] >= 8

    uc = r.json()["items"][0]
    r2 = client.post(
        f"{API}/ml-model-registry",
        json={
            "use_case_id": uc["id"],
            "model_version": "rf-v2-test",
            "algorithm": "XGBoost",
            "stage": "STAGING",
        },
    )
    assert r2.status_code == 201
    entry_id = r2.json()["id"]

    r3 = client.post(f"{API}/ml-model-registry/{entry_id}/promote", json={"actor_id": "ops-test"})
    assert r3.status_code == 200
    assert r3.json()["stage"] == "PRODUCTION"


def test_training_drift_slo_alerts(client):
    client.post(f"{API}/seed")
    uc = client.get(f"{API}/ml-use-cases").json()["items"][0]

    r = client.post(
        f"{API}/ml-training-runs",
        json={"use_case_id": uc["id"], "run_name": "manual-test-run"},
    )
    assert r.status_code == 201
    run_id = r.json()["id"]

    r2 = client.post(
        f"{API}/ml-training-runs/{run_id}/complete",
        json={"ok": True, "model_version": "rf-manual-1", "metrics": {"auc": 0.9}},
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "SUCCEEDED"

    r3 = client.post(
        f"{API}/ml-drift-reports",
        json={
            "use_case_id": uc["id"],
            "model_version": "rf-manual-1",
            "psi_score": 0.31,
            "status": "WARNING",
        },
    )
    assert r3.status_code == 201

    r4 = client.put(
        f"{API}/ml-inference-slo",
        json={"use_case_id": uc["id"], "p95_latency_ms": 400},
    )
    assert r4.status_code == 200

    dash = client.get(f"{API}/dashboard").json()
    assert dash["use_cases"] >= 1
    assert "drift_critical" in dash
