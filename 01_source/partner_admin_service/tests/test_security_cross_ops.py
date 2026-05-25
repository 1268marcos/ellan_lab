from __future__ import annotations

CROSS = "/api/v1/partner-admin/security-admin/cross-ops"


def test_security_cross_ops(client):
    client.post("/api/v1/partner-admin/seed")

    r = client.post(
        f"{CROSS}/access-requests",
        json={
            "requester_id": "usr-suporte",
            "user_id": "usr-suporte",
            "domain_code": "HARDWARE",
            "entity_type": "LockerFleet",
            "entity_id": "INPOST-EU",
            "permission_key": "hardware.fleet.read",
            "justification": "Suporte locker InPost",
        },
    )
    assert r.status_code == 201
    req_id = r.json()["id"]

    r = client.post(
        f"{CROSS}/access-requests/{req_id}/decide",
        json={"decision": "APPROVE", "reviewer_id": "usr-admin-ops"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "APPROVED"
    assert r.json()["grant_id"]

    r = client.post(
        f"{CROSS}/jit-grants",
        json={
            "user_id": "usr-auditoria",
            "domain_code": "PARTNER",
            "entity_type": "LogisticsPartner",
            "entity_id": "DPD",
            "permission_key": "ops.partner.read",
            "reason": "JIT auditoria",
            "duration_hours": 2,
            "approved_by": "usr-admin-ops",
        },
    )
    assert r.status_code == 201

    r = client.post(
        f"{CROSS}/delegations",
        json={
            "delegate_user_id": "usr-suporte",
            "target_domain": "MARKETPLACE",
            "target_entity_type": "ChannelPartner",
            "target_entity_id": "ML-BR",
            "reason": "Act-as ML suporte",
            "duration_hours": 1,
            "approved_by": "usr-admin-ops",
        },
    )
    assert r.status_code == 201
    sid = r.json()["id"]

    r = client.post(f"{CROSS}/entitlements/sync")
    assert r.status_code == 200
    assert r.json()["total"] >= 0

    r = client.get(f"{CROSS}/users/usr-suporte/domain-access-report")
    assert r.status_code == 200
    assert "active_grants" in r.json()

    r = client.post(f"{CROSS}/delegations/{sid}/close", params={"actor_id": "usr-admin-ops"})
    assert r.status_code == 200
    assert r.json()["status"] == "CLOSED"
