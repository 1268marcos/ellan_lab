from __future__ import annotations

API = "/api/v1/marketplace-admin"


def test_seller_operations_flow(client):
    client.post(f"{API}/seed")
    client.post(f"{API}/seller-operations/seed")

    summary = client.get(f"{API}/sellers/mk-seller-demo-001/operations-summary").json()
    assert summary["onboarding_progress_pct"] >= 50
    assert summary["sku_maps"] >= 2
    assert summary["has_fulfillment_prefs"] is True

    onboarding = client.get(f"{API}/sellers/mk-seller-demo-001/onboarding-tasks").json()
    assert onboarding["total"] >= 8
    pending = [t for t in onboarding["tasks"] if t["status"] == "PENDING"]
    if pending:
        done = client.post(
            f"{API}/onboarding-tasks/{pending[0]['id']}/complete",
            json={"completed_by": "test"},
        )
        assert done.status_code == 200

    maps = client.get(f"{API}/sellers/mk-seller-demo-001/channel-sku-maps").json()
    assert maps["total"] >= 2

    preview = client.get(
        f"{API}/sellers/mk-seller-demo-001/pricing-preview",
        params={"internal_sku": "DEMO-001", "base_price_cents": 4990, "channel_partner_id": "mcp-meli"},
    ).json()
    assert preview["final_price_cents"] >= preview["base_price_cents"]

    alloc = client.get(f"{API}/sellers/mk-seller-demo-001/inventory-allocations").json()
    assert alloc["total"] >= 1

    fulfill = client.get(f"{API}/sellers/mk-seller-demo-001/fulfillment-preferences").json()
    assert fulfill["handoff_mode"] == "LOCKER_FIRST"

    notifs = client.get(f"{API}/sellers/mk-seller-demo-001/notification-subscriptions").json()
    assert notifs["total"] >= 2

    r = client.post(
        f"{API}/seller-channel-sku-maps",
        json={
            "seller_id": "mk-seller-demo-001",
            "channel_partner_id": "mcp-shopee",
            "internal_sku": "DEMO-002",
            "channel_sku": "SHOPEE-DEMO-002",
        },
    )
    assert r.status_code == 201
