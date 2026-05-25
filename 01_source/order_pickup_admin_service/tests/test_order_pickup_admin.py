from __future__ import annotations

API = "/api/v1/order-pickup-admin"
EC = f"{API}/ecommerce-partners"
ORDERS = f"{API}/orders"
OUTBOX = f"{API}/integration-outbox"
LIFECYCLE = API


def test_seed_and_partner_crud(client):
    client.post(f"{API}/seed")
    r = client.get(EC)
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(
        EC,
        json={
            "id": "ec-test-99",
            "name": "Test EC",
            "code": "TEST-EC-99",
            "integration_type": "REST",
            "status": "ACTIVE",
        },
    )
    assert r.status_code == 201

    r = client.put(
        f"{API}/partners/ec-test-99/webhook?partner_type=ECOMMERCE",
        json={"url": "https://hooks.example/orders", "secret": "whsec_test"},
    )
    assert r.status_code == 200

    r = client.post(f"{API}/partners/ec-test-99/api-keys/rotate?partner_type=ECOMMERCE")
    assert r.status_code == 200
    assert r.json()["api_key"].startswith("pt_ec_")


def test_omnichannel_and_fulfillment_orders_crud(client):
    client.post(f"{API}/seed")
    r = client.post(
        f"{API}/omnichannel-orders",
        json={
            "order_id": "ord-seed-demo-001",
            "store_id": "store-test-01",
            "pickup_type": "STORE_PICKUP",
            "status": "PENDING",
        },
    )
    assert r.status_code == 201
    omni_id = r.json()["id"]

    r = client.post(
        f"{API}/fulfillment-orders",
        json={
            "order_id": "ord-seed-demo-001",
            "fulfillment_center_id": "fc-test-01",
            "status": "PENDING",
            "carrier": "CORREIOS",
        },
    )
    assert r.status_code == 201
    fo_id = r.json()["id"]

    r = client.get(f"{API}/hub/summary")
    assert r.status_code == 200
    assert r.json()["omnichannel"] >= 1
    assert r.json()["fulfillment_orders"] >= 1

    r = client.patch(f"{API}/omnichannel-orders/{omni_id}", json={"status": "READY"})
    assert r.status_code == 200
    assert r.json()["status"] == "READY"

    r = client.delete(f"{API}/fulfillment-orders/{fo_id}")
    assert r.status_code == 204


def test_order_360_timeline_sla_disputes_prompt5(client):
    client.post(f"{API}/seed")
    oid = "ord-seed-demo-001"
    r = client.get(f"{API}/orders/{oid}/360")
    assert r.status_code == 200
    body = r.json()
    assert body["order_id"] == oid
    assert body["health_score"] >= 0
    assert body["counts"]["pickups"] >= 1
    assert len(body["timeline"]) >= 1
    assert "risk_flags" in body

    r = client.get(f"{API}/sla-watches?order_id={oid}")
    assert r.status_code == 200

    r = client.post(f"{API}/sla-watches/sync")
    assert r.status_code == 200

    r = client.get(f"{API}/order-disputes?order_id={oid}")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(
        f"{API}/orders/{oid}/timeline",
        json={"order_id": oid, "title": "Nota OPS manual", "event_type": "OPS_NOTE"},
    )
    assert r.status_code == 201

    r = client.get(f"{API}/integration-health")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/hub/summary")
    assert r.json()["disputes_open"] >= 1
    assert r.json()["timeline_events"] >= 1


def test_orders_advanced_returns_notifications_holds_recon_prompt7(client):
    client.post(f"{API}/seed")
    oid = "ord-seed-demo-001"
    r = client.get(f"{API}/order-returns?order_id={oid}")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/order-notifications?order_id={oid}")
    assert r.status_code == 200
    assert r.json()["total"] >= 3

    r = client.get(f"{API}/order-holds?order_id={oid}&status=ACTIVE")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(f"{API}/payment-reconciliation/run", json={"order_id": oid})
    assert r.status_code == 200

    r = client.get(f"{API}/payment-reconciliation?order_id={oid}")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/orders/{oid}/360")
    body = r.json()
    assert "RETURN_IN_PROGRESS" in body["risk_flags"] or body["counts"].get("returns", 0) >= 1
    assert "OPS_HOLD_ACTIVE" in body["risk_flags"]

    r = client.get(f"{API}/hub/summary")
    assert r.json()["returns_open"] >= 1
    assert r.json()["ops_holds_active"] >= 1
    assert r.json()["notifications_sent"] >= 3


def test_substitutions_gift_gateway_reconciliation(client):
    client.post(f"{API}/seed")
    oid = "ord-seed-demo-001"

    r = client.get(f"{API}/item-substitutions?order_id={oid}")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/gift-pickups?order_id={oid}")
    assert r.status_code == 200
    assert r.json()["items"][0]["pickup_authorization_code"] == "GIFT8DEMO"

    r = client.get(f"{API}/payment-transactions?order_id={oid}")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    assert r.json()["items"][0]["status"] == "APPROVED"

    r = client.post(f"{API}/payment-reconciliation/run", json={"order_id": oid})
    assert r.status_code == 200
    assert r.json()["used_gateway"] >= 1

    r = client.get(f"{API}/payment-reconciliation?order_id={oid}")
    assert r.json()["items"][0]["status"] == "MATCHED"
    assert r.json()["items"][0]["captured_cents"] == 4990

    r = client.get(f"{API}/orders/{oid}/360")
    flags = r.json()["risk_flags"]
    assert "SUBSTITUTION_PENDING" in flags
    assert "GIFT_PENDING_VERIFICATION" in flags

    r = client.patch(
        f"{API}/gift-pickups/gift-seed-demo-001",
        json={"status": "AUTHORIZED"},
    )
    assert r.status_code == 200

    r = client.post(
        f"{API}/item-substitutions",
        json={
            "order_id": oid,
            "original_sku_id": "SKU-X",
            "substitute_sku_id": "SKU-Y",
            "reason_code": "UPGRADE",
        },
    )
    assert r.status_code == 201


def test_prompt4_players_food_delivery_and_catalog(client):
    r = client.post(f"{API}/integration-channels/sync-world-players")
    assert r.status_code == 200
    body = r.json()
    assert body["channels_created"] + body["channels_updated"] >= 28

    r = client.get(f"{API}/integration-channels/world-review")
    assert r.status_code == 200
    review = r.json()
    assert review["prompt4_total"] == 18
    assert review["prompt4_complete"] is True
    assert review["catalog_total"] == 28
    assert review["by_type"].get("FOOD_DELIVERY", 0) >= 5
    assert review["by_type"].get("AGGREGATOR", 0) >= 6
    assert review["by_type"].get("LOCKER_NETWORK", 0) >= 7

    codes = {p["code"] for p in review["players"]}
    for expected in ("IFOOD", "RAPPI", "MELHOR_ENVIO", "BLOQIT", "VINTED_GO", "CAINIAO"):
        assert expected in codes

    client.post(f"{API}/seed")
    r = client.get(f"{API}/food-delivery-orders?order_id=ord-seed-demo-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    assert r.json()["items"][0]["platform_code"] == "IFOOD"

    r = client.post(
        f"{API}/food-delivery-orders",
        json={"order_id": "ord-seed-demo-001", "platform_code": "RAPPI", "status": "PLACED"},
    )
    assert r.status_code == 201


def test_world_players_prompt3_review(client):
    r = client.post(f"{API}/integration-channels/sync-world-players")
    assert r.status_code == 200
    body = r.json()
    assert body["channels_created"] + body["channels_updated"] >= 10
    assert body["ecommerce"] >= 5
    assert body["logistics"] >= 8

    r = client.get(f"{API}/integration-channels/world-review")
    assert r.status_code == 200
    review = r.json()
    assert review["prompt3_total"] == 10
    assert review["prompt3_complete"] is True
    codes = {p["code"] for p in review["players"]}
    assert "MAGALU" in codes
    assert "MERCADOLIVRE" in codes
    assert "INPOST" in codes
    assert "DHL" in codes
    assert "CORREIOS" in codes
    assert "CTT" in codes
    assert "WORTEN" in codes
    assert "EL_CORTE_INGLES" in codes
    magalu = next(p for p in review["players"] if p["code"] == "MAGALU")
    assert magalu["configured"] is True
    assert magalu["review_status"] == "READY"
    assert magalu["ecommerce_partner_code"] == "MAGALU-EC"
    assert magalu["logistics_partner_code"] == "CORREIOS-MAGALU"

    r = client.get(f"{API}/integration-channels?player_type=MARKETPLACE")
    assert r.status_code == 200
    assert r.json()["total"] >= 3


def test_allocations_manifests_channels_commissions_deadlines(client):
    client.post(f"{API}/seed")
    r = client.get(f"{API}/integration-channels")
    assert r.status_code == 200
    assert r.json()["total"] >= 10

    r = client.get(f"{API}/allocations?order_id=ord-seed-demo-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/logistics-manifests")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/logistics-manifests/items?manifest_id=mf-seed-demo-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/marketplace-commissions?order_id=ord-seed-demo-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{API}/lifecycle-deadlines?order_id=ord-seed-demo-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(
        f"{API}/order-items",
        json={
            "order_id": "ord-seed-demo-001",
            "sku_id": "SKU-EXTRA",
            "quantity": 2,
            "unit_amount_cents": 1000,
        },
    )
    assert r.status_code == 201

    r = client.get(f"{API}/hub/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["allocations"] >= 1
    assert body["integration_channels"] >= 10


def test_orders_pickups_outbox_and_lifecycle(client):
    client.post(f"{API}/seed")
    r = client.get(ORDERS)
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.post(
        ORDERS,
        json={
            "id": "ord-test-01",
            "amount_cents": 1200,
            "ecommerce_partner_id": "ec-ops-001",
            "status": "PENDING",
            "payment_status": "PENDING",
        },
    )
    assert r.status_code == 201

    r = client.post(
        f"{API}/pickups",
        json={"id": "pkp-test-01", "order_id": "ord-test-01", "locker_id": "L1", "status": "PENDING"},
    )
    assert r.status_code == 201

    r = client.get(f"{API}/pickups/pkp-test-01")
    assert r.status_code == 200

    r = client.post(
        f"{API}/credits",
        json={"order_id": "ord-test-01", "user_id": "usr-1", "amount_cents": 300, "type": "REFUND"},
    )
    assert r.status_code == 201

    r = client.get(f"{LIFECYCLE}/order-items?order_id=ord-seed-demo-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{LIFECYCLE}/pickup-events?pickup_id=pkp-seed-demo-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{LIFECYCLE}/pickup-tokens?order_id=ord-seed-demo-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{LIFECYCLE}/pickup-attempts?order_id=ord-seed-demo-001")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{LIFECYCLE}/domain-event-outbox")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.get(f"{OUTBOX}?status=PENDING")
    assert r.status_code == 200
    items = r.json()["items"]
    if items:
        ob_id = items[0]["id"]
        r = client.post(f"{OUTBOX}/{ob_id}/replay")
        assert r.status_code == 200
        assert r.json()["replayed"] is True

    r = client.get(f"{API}/fulfillment-tracking")
    assert r.status_code == 200
    ft_items = r.json()["items"]
    if ft_items:
        ft_id = ft_items[0]["id"]
        r = client.patch(f"{API}/fulfillment-tracking/{ft_id}", json={"status": "PICKED_UP"})
        assert r.status_code == 200
