from __future__ import annotations

SEC = "/api/v1/partner-admin/security-admin"


def test_professional_security_layer(client):
    client.post("/api/v1/partner-admin/seed")

    r = client.get(f"{SEC}/domain-catalog")
    assert r.status_code == 200
    assert r.json()["total"] >= 8

    r = client.get(f"{SEC}/role-catalog")
    assert r.status_code == 200
    assert any(x["code"] == "admin_operacao" for x in r.json()["items"])

    r = client.get(f"{SEC}/cross-domain/health")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{SEC}/cross-domain-grants")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{SEC}/users/usr-admin-ops/360")
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"] == "usr-admin-ops"
    assert "admin_operacao" in body["roles"]

    r = client.get(f"{SEC}/sessions")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{SEC}/identity-providers")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(
        f"{SEC}/cross-domain-grants",
        json={
            "user_id": "usr-suporte",
            "domain_code": "MARKETPLACE",
            "entity_type": "Seller",
            "entity_id": "seller-worten-demo",
            "entity_label": "Worten PT",
            "permission_key": "marketplace.read",
        },
    )
    assert r.status_code == 201

    r = client.post(
        f"{SEC}/policy-snapshots",
        json={"version_label": "v-test-snapshot", "created_by": "usr-admin-ops"},
    )
    assert r.status_code == 201
