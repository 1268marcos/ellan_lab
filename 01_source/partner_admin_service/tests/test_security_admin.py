from __future__ import annotations

SEC = "/api/v1/partner-admin/security-admin"
USERS = "/api/v1/partner-admin/users"


def test_security_admin_lifecycle(client):
    client.post("/api/v1/partner-admin/seed")

    r = client.get(f"{SEC}/summary")
    assert r.status_code == 200
    assert r.json()["users"] >= 3
    assert r.json()["permission_groups"] >= 3

    r = client.post(
        USERS,
        json={"full_name": "Ops Tester", "email": "ops.tester@ellanlab.com", "is_active": True},
    )
    assert r.status_code == 201
    user_id = r.json()["id"]

    r = client.post(
        f"{SEC}/api-keys/rotate",
        json={"user_id": user_id, "label": "test-key", "scopes": ["ops:read"]},
    )
    assert r.status_code == 200
    assert r.json()["api_key"].startswith("sec_")

    r = client.post(
        f"{SEC}/webhook-endpoints",
        json={"url": "https://hooks.test.example/v1", "events": ["user.created"]},
    )
    assert r.status_code == 201
    wh_id = r.json()["id"]

    r = client.post(f"{SEC}/webhook-endpoints/{wh_id}/rotate-secret")
    assert r.status_code == 200
    assert r.json()["webhook_secret"]

    r = client.post(
        f"{SEC}/domain-links",
        json={
            "user_id": user_id,
            "domain": "LOCKER",
            "entity_type": "Locker",
            "entity_id": "locker-test-001",
            "relation": "OPERATOR",
        },
    )
    assert r.status_code == 201

    r = client.get(f"{SEC}/audit-logs")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(f"{USERS}/{user_id}/deactivate")
    assert r.status_code == 200
    assert r.json()["is_active"] is False


def test_permission_group_create(client):
    client.post("/api/v1/partner-admin/seed")
    r = client.post(
        f"{SEC}/permission-groups",
        json={"name": "Custom Test Group", "description": "test"},
    )
    assert r.status_code == 201
    gid = r.json()["id"]
    r = client.post(
        f"{SEC}/permissions",
        json={"group_id": gid, "object_key": "ops.test.read"},
    )
    assert r.status_code == 201
