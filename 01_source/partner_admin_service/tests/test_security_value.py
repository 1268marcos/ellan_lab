from __future__ import annotations

VAL = "/api/v1/partner-admin/security-admin/value"


def test_security_value_layer(client):
    client.post("/api/v1/partner-admin/seed")

    r = client.get(f"{VAL}/intelligence")
    assert r.status_code == 200
    body = r.json()
    assert body["overall_posture"] in ("HEALTHY", "ELEVATED", "CRITICAL")
    assert len(body["recommendations"]) >= 1

    r = client.get(f"{VAL}/role-templates")
    assert r.status_code == 200
    codes = {t["code"] for t in r.json()["items"]}
    assert "tpl-carrier-ops" in codes

    r = client.post(
        f"{VAL}/role-templates/apply",
        json={"user_id": "usr-suporte", "template_code": "tpl-auditor", "granted_by": "usr-admin-ops"},
    )
    assert r.status_code == 200

    r = client.get(f"{VAL}/access-reviews")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{VAL}/alerts")
    assert r.status_code == 200

    r = client.get(f"{VAL}/compliance")
    assert r.status_code == 200
    assert r.json()["coverage_pct"] > 0

    r = client.get(f"{VAL}/access-matrix")
    assert r.status_code == 200
    assert len(r.json()["cells"]) >= 1

    r = client.get(f"{VAL}/risk-scores", params={"tier": "CRITICAL"})
    assert r.status_code == 200
