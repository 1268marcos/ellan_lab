from __future__ import annotations

API = "/api/v1/privacy-compliance-admin"


def test_extended_rota_processors_breaches_dpia(client):
    client.post(f"{API}/seed")

    r = client.get(f"{API}/regulations/GDPR/hub")
    assert r.status_code == 200
    hub = r.json()
    assert hub["regulation_code"] == "GDPR"
    assert hub["processing_activities"] >= 2
    assert hub["legal_bases"] >= 3

    r = client.get(f"{API}/processing-activities?regulation_code=LGPD")
    assert r.status_code == 200
    assert r.json()["total"] >= 2

    r = client.get(f"{API}/legal-bases?regulation_code=CCPA")
    assert r.status_code == 200
    assert r.json()["total"] >= 2

    r = client.get(f"{API}/processors?regulation_code=GDPR")
    assert r.status_code == 200
    assert r.json()["total"] >= 2

    r = client.get(f"{API}/processor-agreements?regulation_code=LGPD")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/breach-incidents")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/impact-assessments?regulation_code=CCPA")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/transfer-records?regulation_code=GDPR")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/dashboard")
    assert r.status_code == 200
    d = r.json()
    assert d["processing_activities"] >= 9
    assert d["processors"] >= 10
    assert d["open_breaches"] >= 1
    assert d["dpia_pending"] >= 1

    r = client.get(f"{API}/locker-networks?regulation_code=LGPD")
    assert r.status_code == 200
    net = r.json()
    assert net["total"] >= 15
    codes = {p["code"] for p in net["items"]}
    assert "CORREIOS" in codes
    assert "MAGALU" in codes
    assert "MELI" in codes
    assert "INTELIPOST" in codes

    r = client.get(f"{API}/locker-networks?regulation_code=GDPR")
    assert r.status_code == 200
    eu_codes = {p["code"] for p in r.json()["items"]}
    assert "INPOST" in eu_codes
    assert "CTT" in eu_codes
    assert "WORTEN" in eu_codes
    assert "ECI" in eu_codes

    r = client.post(
        f"{API}/processing-activities",
        json={
            "regulation_code": "GDPR",
            "code": "KYC_OPS",
            "name": "Seller KYC verification",
            "purpose": "Marketplace seller onboarding compliance",
            "data_categories": ["IDENTITY"],
            "recipients": ["marketplace_admin"],
            "retention_days": 365,
        },
    )
    assert r.status_code == 201
