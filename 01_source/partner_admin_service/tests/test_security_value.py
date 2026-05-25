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


def test_access_review_revoke_and_break_glass(client):
    client.post("/api/v1/partner-admin/seed")

    camps = client.get(f"{VAL}/access-reviews").json()["items"]
    assert camps
    camp_id = camps[0]["id"]

    items = client.get(f"{VAL}/access-reviews/{camp_id}/items", params={"pending_only": True}).json()["items"]
    assert items
    grant_item = next((i for i in items if i["subject_type"] == "CrossDomainGrant"), None)
    role_item = next((i for i in items if i["subject_type"] == "UserRole"), None)

    if grant_item:
        r = client.post(
            f"{VAL}/access-reviews/items/{grant_item['id']}/decide",
            json={"decision": "REVOKE", "reviewer_id": "usr-admin-ops", "notes": "certificacao"},
        )
        assert r.status_code == 200
        assert r.json()["decision"] == "REVOKE"

    if role_item:
        r = client.post(
            f"{VAL}/access-reviews/items/{role_item['id']}/decide",
            json={"decision": "APPROVE", "reviewer_id": "usr-admin-ops"},
        )
        assert r.status_code == 200

    bg = client.post(
        f"{VAL}/break-glass",
        json={
            "user_id": "usr-suporte",
            "reason": "incidente P1",
            "granted_roles": ["auditoria"],
            "approved_by": "usr-admin-ops",
            "duration_hours": 2,
        },
    )
    assert bg.status_code == 201
    ev_id = bg.json()["id"]

    listed = client.get(f"{VAL}/break-glass").json()["items"]
    assert any(x["id"] == ev_id for x in listed)

    rev = client.post(f"{VAL}/break-glass/{ev_id}/revoke", json={"revoked_by": "usr-admin-ops"})
    assert rev.status_code == 200
    assert rev.json()["status"] == "REVOKED"
