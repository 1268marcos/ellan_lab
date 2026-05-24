from __future__ import annotations

API = "/api/v1/payments-admin"


def test_cross_domain_hub_seed_and_registry(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/cross-domain/registry")
    assert r.status_code == 200
    codes = {i["code"] for i in r.json()["items"]}
    assert "FINANCE" in codes
    assert "MARKETPLACE" in codes
    assert "ORDER_PICKUP" in codes


def test_external_refs_and_obligations(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/cross-domain/external-references?order_id=ORD-DEMO-INPOST-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 5
    domains = {i["external_domain"] for i in r.json()["items"]}
    assert "FISCAL" in domains
    assert "MARKETPLACE" in domains

    r = client.get(f"{API}/cross-domain/obligations?order_id=ORD-DEMO-INPOST-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 2


def test_order_360_and_gaps(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/cross-domain/order-360/ORD-DEMO-INPOST-001")
    assert r.status_code == 200
    body = r.json()
    assert body["order_id"] == "ORD-DEMO-INPOST-001"
    assert body["external_refs_total"] >= 5
    assert len(body["domains"]) >= 3

    r = client.get(f"{API}/cross-domain/gaps")
    assert r.status_code == 200


def test_cross_domain_crud(client):
    client.post(f"{API}/seed")
    r = client.post(
        f"{API}/cross-domain/external-references",
        json={
            "order_id": "ORD-TEST-XD-001",
            "payment_entity_type": "ORDER",
            "payment_entity_id": "ORD-TEST-XD-001",
            "external_domain": "FINANCE",
            "external_entity_type": "INVOICE",
            "external_entity_id": "inv-test-001",
        },
    )
    assert r.status_code == 201
    rid = r.json()["id"]
    r = client.delete(f"{API}/cross-domain/external-references/{rid}")
    assert r.status_code == 204

    r = client.post(
        f"{API}/cross-domain/obligations",
        json={
            "order_id": "ORD-TEST-XD-001",
            "domain_code": "FISCAL",
            "obligation_type": "EMIT_NFE",
            "blocking_payment": True,
        },
    )
    assert r.status_code == 201
    oid = r.json()["id"]
    r = client.patch(f"{API}/cross-domain/obligations/{oid}", json={"status": "DONE"})
    assert r.status_code == 200
    assert r.json()["status"] == "DONE"


def test_intelligence_cross_domain_kpis(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/intelligence/summary")
    assert r.status_code == 200
    assert r.json()["external_references_total"] >= 10
    assert r.json()["cross_domain_events_pending"] >= 1
