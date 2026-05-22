from __future__ import annotations

from datetime import date

API = "/api/v1/marketplace-admin"


def test_extended_categories_settlements_kyc_disputes(client):
    client.post(f"{API}/seed")

    r = client.post(
        f"{API}/categories",
        json={"code": "HOME", "name": "Casa e decoracao", "sort_order": 40},
    )
    assert r.status_code == 201
    cat_id = r.json()["id"]

    r = client.post(
        f"{API}/seller-category-links",
        json={"seller_id": "mk-seller-demo-001", "category_id": cat_id, "is_primary": False},
    )
    assert r.status_code == 201

    r = client.post(
        f"{API}/seller-contacts",
        json={
            "seller_id": "mk-seller-demo-001",
            "name": "Suporte Seller",
            "email": "suporte@seller.local",
            "contact_type": "SUPPORT",
        },
    )
    assert r.status_code == 201

    r = client.post(
        f"{API}/seller-payout-accounts",
        json={
            "seller_id": "mk-seller-demo-001",
            "account_type": "PIX",
            "pix_key": "test@pix.local",
            "holder_name": "Loja Demo",
        },
    )
    assert r.status_code == 201
    account_id = r.json()["id"]

    r = client.post(f"{API}/seller-payout-accounts/{account_id}/verify")
    assert r.status_code == 200
    assert r.json()["verified"] is True

    r = client.post(
        f"{API}/seller-settlement-batches",
        json={
            "seller_id": "mk-seller-demo-001",
            "period_start": str(date.today().replace(day=1)),
            "period_end": str(date.today()),
            "fees_cents": 50,
        },
    )
    assert r.status_code == 201
    batch_id = r.json()["id"]
    assert r.json()["commission_count"] >= 1

    r = client.get(f"{API}/seller-settlement-batches/{batch_id}/items")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r = client.patch(f"{API}/seller-settlement-batches/{batch_id}", json={"status": "PAID", "settlement_ref": "PIX-001"})
    assert r.status_code == 200

    r = client.post(
        f"{API}/seller-commission-disputes",
        json={
            "commission_id": "mk-comm-demo-001",
            "seller_id": "mk-seller-demo-001",
            "reason": "Valor da comissao divergente do contrato",
        },
    )
    assert r.status_code == 201
    dispute_id = r.json()["id"]

    r = client.patch(
        f"{API}/seller-commission-disputes/{dispute_id}",
        json={"status": "RESOLVED", "resolution_notes": "Ajuste manual aplicado"},
    )
    assert r.status_code == 200

    r = client.get(f"{API}/dashboard")
    assert r.status_code == 200
    dash = r.json()
    assert dash["sellers_total"] >= 2
    assert "commissions_pending" in dash
