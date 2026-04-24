from app.api.routes_invoice import _derive_previous_receipt_code
from app.models.invoice_model import Invoice


def test_derive_previous_receipt_prefers_protocol():
    inv = Invoice(
        id="inv_1",
        order_id="ord_1",
        country="BR",
        invoice_type="NFCE",
        access_key="AK123",
        government_response={"protocol_number": "PROTO_ABC"},
    )
    assert _derive_previous_receipt_code(inv) == "PROTO_ABC"


def test_derive_previous_receipt_fallback_access_key():
    inv = Invoice(
        id="inv_2",
        order_id="ord_2",
        country="BR",
        invoice_type="NFCE",
        access_key="AK_ONLY",
        government_response={},
    )
    assert _derive_previous_receipt_code(inv) == "AK_ONLY"
