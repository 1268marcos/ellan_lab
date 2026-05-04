import json

import pytest


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_partner(client):
    r = client.post(
        "/partners",
        json={
            "name": "Acme",
            "partner_type": "ECOMMERCE",
            "legal_name": "Acme LTDA",
            "contact_email": "ops@acme.example",
            "status": "ACTIVE",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Acme"
    assert data["partner_type"] == "ECOMMERCE"
    assert "id" in data


def test_get_partner(client):
    c = client.post("/partners", json={"name": "B"}).json()
    r = client.get(f"/partners/{c['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == c["id"]


def test_get_partner_not_found(client):
    r = client.get("/partners/00000000-0000-0000-0000-000000000099")
    assert r.status_code == 404


def test_list_partners_empty(client):
    r = client.get("/partners")
    assert r.status_code == 200
    assert r.json() == []


def test_list_partners(client):
    client.post("/partners", json={"name": "P1"})
    client.post("/partners", json={"name": "P2"})
    r = client.get("/partners?limit=10&skip=0")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_update_partner(client):
    pid = client.post("/partners", json={"name": "Old"}).json()["id"]
    r = client.patch(
        f"/partners/{pid}",
        json={
            "name": "New",
            "legal_name": "New LTDA",
            "contact_email": "new@acme.example",
            "status": "SUSPENDED",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "New"
    assert body["legal_name"] == "New LTDA"
    assert body["contact_email"] == "new@acme.example"
    assert body["status"] == "SUSPENDED"


def test_update_partner_not_found(client):
    r = client.patch(
        "/partners/00000000-0000-0000-0000-000000000099",
        json={"name": "X"},
    )
    assert r.status_code == 404


def test_delete_partner(client):
    pid = client.post("/partners", json={"name": "D"}).json()["id"]
    r = client.delete(f"/partners/{pid}")
    assert r.status_code == 204
    assert client.get(f"/partners/{pid}").status_code == 404


def test_delete_partner_not_found(client):
    r = client.delete("/partners/00000000-0000-0000-0000-000000000099")
    assert r.status_code == 404


def test_patch_webhook(client):
    pid = client.post("/partners", json={"name": "W"}).json()["id"]
    r = client.patch(
        f"/partners/{pid}/webhook",
        json={
            "webhook_url": "https://hooks.example.com/p",
            "webhook_secret": "supersecretvalue",
            "webhook_events_json": json.dumps(["order.created"]),
            "webhook_api_version": "v2",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["webhook_url"] == "https://hooks.example.com/p"
    assert body["webhook_events_json"] == '["order.created"]'
    assert body["webhook_api_version"] == "v2"


def test_patch_webhook_not_found(client):
    r = client.patch(
        "/partners/00000000-0000-0000-0000-000000000099/webhook",
        json={"webhook_url": "https://x.example"},
    )
    assert r.status_code == 404


def test_patch_webhook_invalid_json(client):
    pid = client.post("/partners", json={"name": "Bad"}).json()["id"]
    r = client.patch(
        f"/partners/{pid}/webhook",
        json={"webhook_events_json": "not-json"},
    )
    assert r.status_code == 422


def test_rotate_api_key_first(client):
    pid = client.post("/partners", json={"name": "K"}).json()["id"]
    r = client.post(f"/partners/{pid}/api-keys/rotate", json={"label": "primary"})
    assert r.status_code == 200
    data = r.json()
    assert data["partner_id"] == pid
    assert data["key_prefix"]
    assert len(data["api_key"]) > 20


def test_rotate_api_key_revokes_previous(client):
    pid = client.post("/partners", json={"name": "K2"}).json()["id"]
    first = client.post(f"/partners/{pid}/api-keys/rotate", json={}).json()
    second = client.post(f"/partners/{pid}/api-keys/rotate", json={}).json()
    assert first["api_key"] != second["api_key"]
