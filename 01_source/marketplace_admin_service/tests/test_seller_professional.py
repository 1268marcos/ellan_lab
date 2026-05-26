from __future__ import annotations

API = "/api/v1/marketplace-admin"


def test_seller_professional_seed_and_crud(client):
    client.post(f"{API}/seed")
    r = client.post(f"{API}/seller-professional/seed")
    assert r.status_code == 200

    tiers = client.get(f"{API}/seller-tier-definitions").json()
    assert tiers["total"] >= 3
    assert any(t["code"] == "ENTERPRISE" for t in tiers["tiers"])

    enroll = client.get(f"{API}/seller-tier-enrollments", params={"seller_id": "mk-seller-demo-001"}).json()
    assert enroll["total"] >= 1

    comp = client.get(f"{API}/seller-compliance-profiles", params={"seller_id": "mk-seller-demo-001"}).json()
    assert comp["total"] >= 2
    eu = next(p for p in comp["profiles"] if p["country"] == "ES")
    assert eu["ioss_number"]

    perf = client.get(f"{API}/seller-performance-monthly", params={"seller_id": "mk-seller-demo-001"}).json()
    assert perf["total"] >= 1

    agr = client.get(f"{API}/seller-agreements", params={"seller_id": "mk-seller-demo-001"}).json()
    assert agr["total"] >= 2

    risk = client.get(f"{API}/seller-risk-assessments", params={"seller_id": "mk-seller-demo-001"}).json()
    assert risk["total"] >= 1
    assert risk["assessments"][0]["risk_band"] == "LOW"

    summary = client.get(f"{API}/seller-professional/summary", params={"seller_id": "mk-seller-demo-001"}).json()
    assert summary["agreements_signed"] >= 2
    assert summary["latest_risk_band"] == "LOW"

    r = client.post(
        f"{API}/seller-risk-assessments",
        json={
            "seller_id": "mk-seller-demo-002",
            "risk_score": 72,
            "risk_band": "HIGH",
            "factors_json": '[{"code":"PENDING_KYC","weight":20}]',
        },
    )
    assert r.status_code == 201
