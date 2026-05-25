from __future__ import annotations

import pytest

BASE = "/api/v1/security"


@pytest.fixture(autouse=True)
def seed_baseline(client):
    client.post(f"{BASE}/seed")
    yield


def test_users_crud(client):
    r = client.post(
        f"{BASE}/users",
        json={"full_name": "Test User", "email": "test.crud@ellanlab.com", "is_active": True},
    )
    assert r.status_code == 201
    uid = r.json()["id"]
    assert client.get(f"{BASE}/users/{uid}").status_code == 200
    assert client.patch(f"{BASE}/users/{uid}", json={"full_name": "Test Updated"}).status_code == 200
    assert client.delete(f"{BASE}/users/{uid}").status_code == 204


def test_roles_crud(client):
    r = client.post(f"{BASE}/roles", json={"user_id": "usr-admin", "role": "partner"})
    assert r.status_code == 201
    rid = r.json()["id"]
    assert client.get(f"{BASE}/roles/{rid}").status_code == 200
    assert client.delete(f"{BASE}/roles/{rid}").status_code == 204


def test_permissions_matrix(client):
    r = client.get(f"{BASE}/permissions/matrix")
    assert r.status_code == 200
    assert "groups" in r.json()


def test_api_key_rotate(client):
    r = client.post(f"{BASE}/api-keys/rotate", json={"user_id": "usr-admin"})
    assert r.status_code == 200
    assert "api_key" in r.json()


def test_webhook_config(client):
    r = client.post(f"{BASE}/webhook-config", json={"url": "https://example.com/hook", "events": ["order.paid"]})
    assert r.status_code == 200
    assert r.json()["endpoint"]["url"] == "https://example.com/hook"
