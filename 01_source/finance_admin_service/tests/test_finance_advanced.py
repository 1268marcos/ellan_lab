from __future__ import annotations

from datetime import date, timedelta

API = "/api/v1/finance-admin"


def test_advanced_domain_seed_and_fx(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/commercial-tiers")
    assert r.status_code == 200
    codes = {t["tier_code"] for t in r.json()["items"]}
    assert "STANDARD" in codes
    assert "ENTERPRISE" in codes

    r = client.get(f"{API}/fx-rates")
    assert r.status_code == 200
    assert r.json()["total"] >= 3

    r = client.get(f"{API}/fx-rates/convert", params={"amount_cents": 10000, "from": "USD", "to": "BRL"})
    assert r.status_code == 200
    assert r.json()["converted_cents"] > 10000


def test_dunning_tax_audit_and_settlement_reconcile(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/tax-corridors")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/payment-terms")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/invoice-documents")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    # force overdue for dunning scan
    partners = client.get(f"{API}/finance-partners").json()["items"]
    magalu = next(p for p in partners if p["code"] == "MAGALU")
    invs = client.get(f"{API}/b2b-invoices", params={"partner_id": magalu["id"]}).json()["items"]
    if invs:
        inv_id = invs[0]["id"]
        client.patch(
            f"{API}/b2b-invoices/{inv_id}",
            json={
                "status": "ISSUED",
                "due_date": (date.today() - timedelta(days=20)).isoformat(),
            },
        )
    r = client.post(f"{API}/dunning/scan")
    assert r.status_code == 200

    r = client.get(f"{API}/audit-log", params={"entity_type": "billing_cycle"})
    assert r.status_code == 200

    batches = client.get(f"{API}/settlement-batches").json()["items"]
    if batches:
        rec = client.post(f"{API}/settlement-batches/{batches[0]['id']}/reconcile")
        assert rec.status_code == 200
        assert rec.json()["run"]["matched_count"] >= 0
