from __future__ import annotations

DEMO = "partner_demo_001"
BASE = "/api/v1/partner-admin"


def test_partner_extended_observability_and_billing(client):
    client.post(f"{BASE}/seed")

    r = client.get(f"{BASE}/partners/{DEMO}/360?partner_type=ECOMMERCE")
    assert r.status_code == 200
    body = r.json()
    assert body["onboarding_progress_pct"] >= 0
    assert "integration_status" in body

    r = client.get(f"{BASE}/partners/{DEMO}/onboarding")
    assert r.status_code == 200
    assert r.json()["total"] >= 7
    milestone_id = r.json()["items"][3]["id"]

    r = client.patch(
        f"{BASE}/partners/{DEMO}/onboarding/{milestone_id}",
        json={"status": "DONE", "completed_by": "usr-admin-ops"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "DONE"

    r = client.get(f"{BASE}/partners/{DEMO}/webhook-deliveries")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(f"{BASE}/partners/{DEMO}/integration-health/probe?partner_type=ECOMMERCE")
    assert r.status_code == 200
    assert r.json()["status"] in ("UP", "DEGRADED")

    r = client.get(f"{BASE}/partners/{DEMO}/outbox")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{BASE}/partners/{DEMO}/invoices")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{BASE}/partners/{DEMO}/billing-line-items?cycle_id=cycle-demo-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{BASE}/partners/{DEMO}/credit-notes")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{BASE}/partners/{DEMO}/payment-holds")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{BASE}/partners/{DEMO}/commissions")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
