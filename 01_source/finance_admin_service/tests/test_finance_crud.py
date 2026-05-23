from __future__ import annotations

from datetime import date

API = "/api/v1/finance-admin"


def test_finance_full_crud_webhook_and_seed(client):
    client.post(f"{API}/seed")

    r = client.post(
        f"{API}/finance-partners",
        json={
            "code": "TEST_FIN",
            "name": "Finance Test Partner",
            "partner_type": "ECOMMERCE",
            "country_code": "BR",
        },
    )
    assert r.status_code == 201
    partner_id = r.json()["id"]

    r = client.post(
        f"{API}/billing-plans",
        json={
            "partner_id": partner_id,
            "plan_name": "Plano Teste",
            "billing_model": "PER_USE",
            "valid_from": str(date.today()),
            "fee_per_delivery_cents": 300,
        },
    )
    assert r.status_code == 201
    plan_id = r.json()["id"]

    r = client.post(
        f"{API}/billing-cycles",
        json={
            "partner_id": partner_id,
            "billing_plan_id": plan_id,
            "period_start": str(date.today().replace(day=1)),
            "period_end": str(date.today()),
            "total_amount_cents": 10000,
        },
    )
    assert r.status_code == 201
    cycle_id = r.json()["id"]

    r = client.post(
        f"{API}/b2b-invoices",
        json={
            "cycle_id": cycle_id,
            "partner_id": partner_id,
            "amount_cents": 10000,
            "status": "DRAFT",
        },
    )
    assert r.status_code == 201
    invoice_id = r.json()["id"]

    r = client.put(
        f"{API}/finance-partners/{partner_id}/webhook",
        json={"url": "https://hooks.test/finance", "secret": "whsec-test"},
    )
    assert r.status_code == 200

    r = client.post(f"{API}/finance-partners/{partner_id}/api-keys/rotate")
    assert r.status_code == 200
    assert "api_key" in r.json()

    r = client.post(f"{API}/wallet-providers", json={"code": "TEST_WALLET", "name": "Test Wallet"})
    assert r.status_code == 201

    r = client.post(
        f"{API}/wallet-transactions",
        json={
            "wallet_id": "w-test",
            "type": "DEBIT",
            "amount_cents": 500,
            "balance_after_cents": 4500,
        },
    )
    assert r.status_code == 201

    r = client.post(
        f"{API}/ops-invoices",
        json={"order_id": "ord-fin-1", "country": "BR", "invoice_type": "NFC_E", "status": "PENDING"},
    )
    assert r.status_code == 201

    r = client.get(f"{API}/finance-partners")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.patch(f"{API}/b2b-invoices/{invoice_id}", json={"status": "ISSUED"})
    assert r.status_code == 200
    assert r.json()["status"] == "ISSUED"

    r = client.get(f"{API}/billing-processed-events")
    assert r.status_code == 200
