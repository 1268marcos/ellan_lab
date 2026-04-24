from __future__ import annotations

from app.services.fiscal_read_adapter import (
    extract_attempt_from_fiscal_payload,
    fiscal_read_view_from_billing_invoice,
)


def test_fiscal_read_view_from_billing_minimal():
    inv = {
        "id": "inv_abc",
        "order_id": "ord-1",
        "status": "ISSUED",
        "invoice_type": "NFE",
        "amount_cents": 1500,
        "currency": "BRL",
        "region": "SP",
        "access_key": "ABC123KEY",
        "order_snapshot": {
            "order": {"id": "ord-1", "totem_id": "T1", "channel": "KIOSK", "region": "SP"},
            "pickup": {"locker_id": "L1", "slot": 2},
        },
    }
    v = fiscal_read_view_from_billing_invoice(inv)
    assert v.source == "billing"
    assert v.receipt_code.startswith("BR-")
    assert v.order_id == "ord-1"
    assert v.payload_json["pickup"]["locker_id"] == "L1"
    assert v.payload_json["receipt_code_full"] == "ABC123KEY"
    assert v.payload_json["receipt_lookup_supported"] is True
    assert v.print_site_path is None


def test_extract_attempt_from_payload():
    assert extract_attempt_from_fiscal_payload({"receipt_code": "X-ATT02"}) == 2
    assert extract_attempt_from_fiscal_payload({"receipt_code": "NONE"}) == 1
