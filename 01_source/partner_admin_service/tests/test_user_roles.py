from __future__ import annotations

ROLES_API = "/api/v1/partner-admin/user-roles"


def test_user_roles_lifecycle(client):
    client.post("/api/v1/partner-admin/seed")
    r = client.post(
        ROLES_API,
        json={"user_id": "usr-admin-ops", "role": "auditoria", "scope_type": "GLOBAL"},
    )
    assert r.status_code == 201
    role_id = r.json()["id"]

    r = client.get(ROLES_API, params={"user_id": "usr-admin-ops"})
    assert r.status_code == 200
    assert r.json()["total"] >= 2

    r = client.post(f"{ROLES_API}/{role_id}/revoke")
    assert r.status_code == 200
    assert r.json()["revoked_at"] is not None

    r = client.delete(f"{ROLES_API}/{role_id}")
    assert r.status_code == 204
