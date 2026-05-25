from __future__ import annotations

API = "/api/v1/hardware-admin"
PRO = f"{API}/professional-ops"


def test_professional_ops_seed_and_summary(client):
    r = client.post(f"{API}/seed")
    assert r.status_code == 200
    body = r.json()
    assert body.get("playbooks", 0) >= 3
    assert body.get("certifications", 0) >= 6
    assert body.get("corridors", 0) >= 3
    assert body.get("incidents", 0) >= 2
    assert body.get("webhooks", 0) >= 3
    assert body.get("onboarding_runs", 0) >= 1

    r = client.get(f"{PRO}/summary")
    assert r.status_code == 200
    summary = r.json()
    assert summary["readiness_rows"] >= 20
    assert summary["certifications"] >= 6
    assert summary["corridors"] >= 3
    assert summary["open_incidents"] >= 2
    assert summary["onboarding_runs_active"] >= 1
    assert summary["capability_webhooks"] >= 3


def test_professional_ops_readiness_and_corridors(client):
    client.post(f"{API}/seed")

    r = client.get(f"{PRO}/readiness?band=GO_LIVE")
    assert r.status_code == 200
    assert r.json()["total"] >= 3

    r = client.post(f"{PRO}/readiness/recompute")
    assert r.status_code == 200
    assert r.json()["updated"] >= 20

    r = client.get(f"{PRO}/corridors")
    assert r.status_code == 200
    corridors = r.json()
    assert len(corridors) >= 3
    br = next(c for c in corridors if c["corridor_code"] == "BR-BR-INPOST-MAGALU")

    r = client.get(f"{PRO}/corridors/{br['id']}/steps")
    assert r.status_code == 200
    assert len(r.json()) >= 3

    r = client.get(f"{PRO}/corridor-sla")
    assert r.status_code == 200
    assert len(r.json()) >= 3


def test_professional_ops_onboarding_and_audit(client):
    client.post(f"{API}/seed")

    r = client.get(f"{PRO}/onboarding/playbooks")
    assert r.status_code == 200
    assert len(r.json()) >= 3

    r = client.get(f"{PRO}/onboarding/runs")
    assert r.status_code == 200
    runs = r.json()
    assert len(runs) >= 1

    r = client.get(f"{PRO}/onboarding/runs/{runs[0]['id']}/milestones")
    assert r.status_code == 200
    assert len(r.json()) >= 4

    r = client.get(f"{PRO}/certifications?player_code=INPOST")
    assert r.status_code == 200
    assert r.json()["total"] >= 2

    r = client.get(f"{PRO}/audit-log")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{PRO}/capability-webhooks")
    assert r.status_code == 200
    assert r.json()["total"] >= 3
