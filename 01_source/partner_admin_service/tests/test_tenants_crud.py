from __future__ import annotations

TENANTS_API = "/api/v1/partner-admin/tenants"


def test_tenant_domains_and_links(client):
    client.post("/api/v1/partner-admin/seed")
    r = client.post(
        TENANTS_API,
        json={
            "tenant_id": "tenant-test-1",
            "cnpj": "11.222.333/0001-44",
            "razao_social": "Tenant Teste",
            "regime": "SIMPLES",
            "crt": "1",
        },
    )
    assert r.status_code == 201

    r = client.post(
        f"{TENANTS_API}/tenant-test-1/domains",
        json={"domain": "test1.ops.ellanlab.local", "verified": True},
    )
    assert r.status_code == 201

    r = client.get(f"{TENANTS_API}/tenant-test-1/domains")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    ec = client.get("/api/v1/partner-admin/ecommerce-partners").json()["partners"]
    if ec:
        r = client.post(
            f"{TENANTS_API}/tenant-test-1/partner-links",
            json={"partner_id": ec[0]["id"], "partner_type": "ECOMMERCE", "is_default": True},
        )
        assert r.status_code == 201

    r = client.delete(f"{TENANTS_API}/tenant-test-1")
    assert r.status_code == 204
