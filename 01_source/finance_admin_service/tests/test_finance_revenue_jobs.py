from __future__ import annotations

from datetime import date, timedelta

API = "/api/v1/finance-admin"


def test_revenue_recognition_and_jobs(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/revenue-schedules")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/revenue-recognition-entries")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(f"{API}/revenue-recognition/run", params={"sync_fiscal": False})
    assert r.status_code == 200
    assert r.json()["entries_created"] >= 0

    r = client.post(f"{API}/jobs/run/DUNNING_SCAN")
    assert r.status_code == 200
    assert r.json()["status"] in ("COMPLETED", "FAILED")

    r = client.get(f"{API}/jobs/runs")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_emit_fiscal_stub_and_close_cycle(client):
    client.post(f"{API}/seed")
    partners = client.get(f"{API}/finance-partners").json()["items"]
    magalu = next(p for p in partners if p["code"] == "MAGALU")
    cycles = client.get(f"{API}/billing-cycles", params={"partner_id": magalu["id"]}).json()["items"]
    assert cycles
    cy = cycles[0]
    if cy["status"] != "CLOSED":
        cr = client.post(f"{API}/billing-cycles/{cy['id']}/close", params={"create_revenue_schedule": True})
        assert cr.status_code == 200
        assert cr.json().get("tax_cents") is not None

    invs = client.get(f"{API}/b2b-invoices", params={"partner_id": magalu["id"]}).json()["items"]
    assert invs
    emit = client.post(f"{API}/b2b-invoices/{invs[0]['id']}/emit-fiscal")
    assert emit.status_code == 200
    body = emit.json()
    assert body.get("access_key") or body.get("already_issued")
