from __future__ import annotations

from datetime import date

BASE = "/api/v1/partner-admin"
DEMO = "partner_demo_001"


def test_partner_domain_settlements_and_service_areas(client):
    client.post(f"{BASE}/seed")

    r = client.get(f"{BASE}/partners/{DEMO}/settlements")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    batch_id = r.json()["items"][0]["id"]

    r = client.get(f"{BASE}/partners/{DEMO}/settlements/{batch_id}/items")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(
        f"{BASE}/partners/{DEMO}/settlements/generate",
        json={
            "period_start": "2026-05-01",
            "period_end": "2026-05-15",
            "revenue_share_pct": 0.12,
            "fees_cents": 1000,
            "total_orders": 3,
            "gross_revenue_cents": 30000,
        },
    )
    assert r.status_code == 200
    new_batch = r.json()["id"]

    r = client.patch(
        f"{BASE}/partners/{DEMO}/settlements/{new_batch}/approve",
        json={"settlement_ref": "PIX-TEST-001"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "APPROVED"

    r = client.get(f"{BASE}/partners/{DEMO}/performance?limit=3")
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 1

    r = client.get(f"{BASE}/partners/{DEMO}/service-areas")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(
        f"{BASE}/partners/{DEMO}/service-areas",
        json={
            "locker_id": "locker_sp_002",
            "priority": 80,
            "valid_from": str(date(2026, 5, 1)),
        },
    )
    assert r.status_code == 200


def test_partner_ops_dashboard_and_stores(client):
    client.post(f"{BASE}/seed")

    r = client.get(f"{BASE}/partners/ops/dashboard?partner_id={DEMO}")
    assert r.status_code == 200
    assert "kpis" in r.json()
    assert r.json()["kpis"]["total_events"] >= 1

    r = client.get(f"{BASE}/partner-stores")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{BASE}/partners/{DEMO}/billing-plans")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{BASE}/partners/{DEMO}/billing-cycles")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{BASE}/partners/{DEMO}/sla-agreements")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{BASE}/partners/{DEMO}/status-history")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
