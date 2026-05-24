from __future__ import annotations

API = "/api/v1/fiscal-admin"


def _seed(client):
    client.post(f"{API}/seed")
    client.post(f"{API}/fiscal-global-ops/seed-global")
    client.post(f"{API}/fiscal-intelligence/seed-demo")
    client.post(f"{API}/fiscal-global-ops/integration-readiness/recompute")


def test_fiscal_intelligence_analyze_and_dashboard(client):
    _seed(client)
    r = client.post(f"{API}/fiscal-intelligence/analyze")
    assert r.status_code == 200
    body = r.json()
    assert body["insights_open"] >= 1

    d = client.get(f"{API}/fiscal-intelligence/dashboard")
    assert d.status_code == 200
    dash = d.json()
    assert "open_insights" in dash
    assert dash["certs_expiring_90d"] >= 0

    ins = client.get(f"{API}/fiscal-intelligence/insights")
    assert ins.status_code == 200
    assert ins.json()["total"] >= 1


def test_corridor_detail(client):
    _seed(client)
    c = client.get(f"{API}/fiscal-global-ops/corridors")
    code = c.json()["items"][0]["corridor_code"]
    d = client.get(f"{API}/fiscal-global-ops/corridors/{code}")
    assert d.status_code == 200
    body = d.json()
    assert body["corridor_code"] == code
    assert "tax_rules" in body


def test_certifications_enriched(client):
    _seed(client)
    r = client.get(f"{API}/fiscal-global-ops/certifications", params={"enriched": True})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1
    assert "expiry_severity" in items[0]


def test_classify_sku(client):
    _seed(client)
    r = client.post(
        f"{API}/fiscal-global-ops/classification-rules/test-classify",
        params={"sku": "SKU-LOCKER-RENT-01", "country": "BR"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["matched"] is True
    assert body["ncm_code"]


def test_contingency_lifecycle(client):
    _seed(client)
    r = client.post(
        f"{API}/fiscal-intelligence/contingency-events",
        json={
            "country": "BR",
            "authority": "SEFAZ-SP",
            "contingency_mode": "EPEC",
            "reason": "test",
            "region_code": "SP",
            "issuer_code": "SEFAZ-BR-SP",
        },
    )
    assert r.status_code == 200
    evt_id = r.json()["id"]
    assert r.json()["active"] is True

    close = client.post(f"{API}/fiscal-intelligence/contingency-events/{evt_id}/close")
    assert close.status_code == 200
    assert close.json()["active"] is False


def test_webhook_retry(client):
    _seed(client)
    wh = client.get(f"{API}/fiscal-global-ops/webhook-deliveries", params={"failed_only": True})
    assert wh.status_code == 200
    items = wh.json()["items"]
    if not items:
        return
    delivery_id = items[0]["id"]
    retry = client.post(f"{API}/fiscal-global-ops/webhook-deliveries/{delivery_id}/retry")
    assert retry.status_code == 200
    assert retry.json()["delivery_status"] == "PENDING"
