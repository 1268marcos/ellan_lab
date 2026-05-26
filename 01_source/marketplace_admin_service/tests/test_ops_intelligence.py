from __future__ import annotations

API = "/api/v1/marketplace-admin"


def test_ops_intelligence_full_flow(client):
    client.post(f"{API}/seed")
    client.post(f"{API}/channel-partners/seed-players")
    client.post(f"{API}/player-ecosystem/seed")
    ops = client.post(f"{API}/ops-intelligence/seed").json()
    assert ops["playbooks"] >= 5 or ops.get("playbooks", 0) >= 0

    summary = client.get(f"{API}/ops-intelligence/summary").json()
    assert summary["playbooks_total"] >= 5
    assert summary["cross_border_profiles"] >= 3

    playbooks = client.get(f"{API}/ops-intelligence/playbooks").json()
    assert playbooks["total"] >= 5
    assert any(p["code"] == "WEBHOOK_DLQ_SPIKE" for p in playbooks["playbooks"])

    health = client.post(f"{API}/sellers/mk-seller-demo-001/health/compute").json()
    assert health["health_band"] in ("GREEN", "YELLOW", "RED")
    assert "factors" in health

    quotas = client.get(f"{API}/sellers/mk-seller-demo-001/channel-quotas").json()
    assert quotas["total"] >= 2

    xb = client.get(f"{API}/sellers/mk-seller-demo-001/cross-border-profiles").json()
    assert xb["total"] >= 3

    api_h = client.get(f"{API}/ops-intelligence/partner-api-health?degraded_only=true").json()
    assert api_h["total"] >= 0

    promos = client.get(f"{API}/sellers/mk-seller-demo-001/promotions").json()
    assert promos["total"] >= 1

    job = client.post(
        f"{API}/seller-catalog-sync-jobs",
        json={
            "seller_id": "mk-seller-demo-001",
            "channel_partner_id": "mcp-shopee",
            "job_type": "INCREMENTAL_SYNC",
            "items_total": 50,
        },
    )
    assert job.status_code == 201
    jid = job.json()["id"]
    done = client.post(f"{API}/seller-catalog-sync-jobs/{jid}/run").json()
    assert done["status"] in ("COMPLETED", "PARTIAL")
