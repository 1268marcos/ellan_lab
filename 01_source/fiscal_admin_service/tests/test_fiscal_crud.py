from __future__ import annotations

API = "/api/v1/fiscal-admin"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["service"] == "fiscal-admin"


def test_seed_and_issuer_crud(client):
    r = client.post(f"{API}/seed")
    assert r.status_code == 200
    assert r.json()["issuers"] >= 1

    r = client.get(f"{API}/fiscal-issuer-partners")
    assert r.status_code == 200
    issuers = r.json()["issuers"]
    assert len(issuers) >= 2
    issuer_id = issuers[0]["id"]

    r = client.put(
        f"{API}/fiscal-issuer-partners/{issuer_id}/webhook",
        json={"url": "https://hooks.example/fiscal", "secret": "whsec_test"},
    )
    assert r.status_code == 200

    r = client.post(f"{API}/fiscal-issuer-partners/{issuer_id}/api-keys/rotate")
    assert r.status_code == 200
    assert "api_key" in r.json()
    assert r.json()["api_key"].startswith("fc_")


def test_documents_and_gaps(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/fiscal-documents")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/fiscal-ops/reconciliation-gaps")
    assert r.status_code == 200
    gaps = r.json()["items"]
    assert gaps
    gap_id = gaps[0]["id"]
    r = client.patch(f"{API}/fiscal-ops/reconciliation-gaps/{gap_id}", json={"status": "RESOLVED"})
    assert r.status_code == 200
    assert r.json()["status"] == "RESOLVED"


def test_tenant_product_health(client):
    client.post(f"{API}/seed")
    assert client.get(f"{API}/fiscal-ops/tenant-config").json()["total"] >= 1
    assert client.get(f"{API}/fiscal-ops/product-fiscal-config").json()["total"] >= 1
    assert client.get(f"{API}/fiscal-ops/provider-health").json()["total"] >= 1
