from __future__ import annotations

EC_API = "/api/v1/partner-admin/ecommerce-partners"
LG_API = "/api/v1/partner-admin/logistics-partners"


def test_ecommerce_crud(client):
    client.post("/api/v1/partner-admin/seed")
    r = client.post(
        EC_API,
        json={"id": "ec-test-1", "name": "Test EC", "code": "TEST-EC", "status": "ACTIVE"},
    )
    assert r.status_code == 201
    assert r.json()["code"] == "TEST-EC"

    r = client.get(EC_API)
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.patch(f"{EC_API}/ec-test-1", json={"active": False})
    assert r.status_code == 200
    assert r.json()["active"] is False

    r = client.delete(f"{EC_API}/ec-test-1")
    assert r.status_code == 204


def test_logistics_crud(client):
    client.post("/api/v1/partner-admin/seed")
    r = client.post(
        LG_API,
        json={"id": "lg-test-1", "name": "Test LG", "code": "TEST-LG"},
    )
    assert r.status_code == 201

    r = client.get(f"{LG_API}/lg-test-1")
    assert r.status_code == 200

    r = client.delete(f"{LG_API}/lg-test-1")
    assert r.status_code == 204
