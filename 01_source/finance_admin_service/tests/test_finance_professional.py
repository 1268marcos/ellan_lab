from __future__ import annotations

API = "/api/v1/finance-admin"


def test_ecosystem_summary_and_readiness(client):
    client.post(f"{API}/seed")
    r = client.post(f"{API}/partner-readiness/recompute")
    assert r.status_code == 200
    assert r.json()["recomputed"] >= 80

    r = client.get(f"{API}/locker-network-catalog/ecosystem-summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total_players"] >= 85
    assert body["total_relations"] >= 1
    assert body["readiness_average"] > 0

    r = client.get(f"{API}/partner-readiness?grade=A")
    assert r.status_code == 200
    assert r.json()["total"] >= 0


def test_contracts_milestones_sla_and_cycle_close(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/commercial-contracts")
    assert r.status_code == 200
    assert r.json()["total"] >= 5

    r = client.get(f"{API}/integration-milestones?catalog_code=MAGALU")
    assert r.status_code == 200
    assert r.json()["total"] >= 4

    r = client.get(f"{API}/sla-definitions")
    assert r.status_code == 200
    slas = r.json()["items"]
    assert len(slas) >= 1

    partners = client.get(f"{API}/finance-partners").json()["items"]
    magalu = next(p for p in partners if p["code"] == "MAGALU")
    cycles = client.get(f"{API}/billing-cycles", params={"partner_id": magalu["id"]}).json()["items"]
    if cycles:
        cy = cycles[0]
        if cy["status"] != "CLOSED":
            cr = client.post(f"{API}/billing-cycles/{cy['id']}/close")
            assert cr.status_code == 200
            assert cr.json()["status"] == "CLOSED"

    failed = client.get(f"{API}/webhook-deliveries", params={"failed_only": True}).json()["items"]
    if failed:
        rep = client.post(f"{API}/webhook-deliveries/{failed[0]['id']}/replay")
        assert rep.status_code == 200
        assert rep.json()["status"] == "DELIVERED"
