from __future__ import annotations

from datetime import date, datetime, timezone

API = "/api/v1/finance-admin"


def test_extended_settlements_treasury_and_pnl(client):
    client.post(f"{API}/seed")

    r = client.post(
        f"{API}/finance-partners",
        json={"code": "EXT_FIN", "name": "Extended Finance Co", "partner_type": "CARRIER"},
    )
    assert r.status_code == 201
    partner_id = r.json()["id"]

    r = client.post(
        f"{API}/billing-plans",
        json={
            "partner_id": partner_id,
            "plan_name": "Per Use EU",
            "billing_model": "PER_USE",
            "valid_from": str(date.today()),
            "fee_per_delivery_cents": 400,
        },
    )
    plan_id = r.json()["id"]

    r = client.post(
        f"{API}/billing-cycles",
        json={
            "partner_id": partner_id,
            "billing_plan_id": plan_id,
            "period_start": str(date.today().replace(day=1)),
            "period_end": str(date.today()),
            "total_amount_cents": 50000,
        },
    )
    cycle_id = r.json()["id"]

    r = client.post(
        f"{API}/billing-line-items",
        json={
            "cycle_id": cycle_id,
            "partner_id": partner_id,
            "line_type": "DELIVERY_FEE",
            "description": "Deliveries DE corridor",
            "unit_price_cents": 400,
            "quantity": "100",
        },
    )
    assert r.status_code == 201
    line_id = r.json()["id"]

    r = client.post(
        f"{API}/settlement-batches",
        json={
            "partner_id": partner_id,
            "period_start": str(date.today().replace(day=1)),
            "period_end": str(date.today()),
            "gross_revenue_cents": 100000,
            "revenue_share_pct": "0.05",
        },
    )
    assert r.status_code == 201
    batch_id = r.json()["id"]

    r = client.post(
        f"{API}/settlement-items",
        json={
            "batch_id": batch_id,
            "order_id": "ord-ext-1",
            "order_date": datetime.now(timezone.utc).isoformat(),
            "gross_cents": 10000,
            "share_pct": "0.05",
        },
    )
    assert r.status_code == 201

    r = client.post(
        f"{API}/credit-notes",
        json={
            "partner_id": partner_id,
            "reason_code": "HARDWARE_DOWNTIME",
            "description": "Locker offline 4h",
            "amount_cents": 8000,
        },
    )
    assert r.status_code == 201

    r = client.post(
        f"{API}/payment-holds",
        json={"partner_id": partner_id, "invoice_id": "inv-hold-1", "hold_amount_cents": 20000},
    )
    assert r.status_code == 201

    r = client.post(
        f"{API}/commission-structures",
        json={
            "partner_id": partner_id,
            "commission_percentage": "3.25",
            "effective_from": str(date.today()),
        },
    )
    assert r.status_code == 201

    r = client.post(
        f"{API}/cost-centers",
        json={"locker_id": "LCK-EXT-01", "network_code": "INPOST", "region_code": "GB"},
    )
    assert r.status_code == 201

    r = client.post(
        f"{API}/cost-center-monthly",
        json={
            "locker_id": "LCK-EXT-01",
            "month": str(date.today().replace(day=1)),
            "rent_cents": 10000,
            "energy_cents": 5000,
        },
    )
    assert r.status_code == 201
    assert r.json()["total_opex_cents"] == 15000

    r = client.post(
        f"{API}/fiscal-reconciliation-gaps",
        json={
            "dedupe_key": "ext-gap-001",
            "gap_type": "AMOUNT_MISMATCH",
            "severity": "MEDIUM",
            "order_id": "ord-ext-1",
        },
    )
    assert r.status_code == 201
    gap_id = r.json()["id"]

    r = client.patch(f"{API}/fiscal-reconciliation-gaps/{gap_id}", json={"status": "RESOLVED"})
    assert r.status_code == 200

    r = client.get(f"{API}/settlement-batches?partner_id={partner_id}")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.delete(f"{API}/billing-line-items/{line_id}")
    assert r.status_code == 204

    r = client.get(f"{API}/webhook-deliveries?failed_only=true")
    assert r.status_code == 200
