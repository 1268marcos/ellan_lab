from app.api.routes_admin_fiscal import _build_danfe_pdf_stub_base64
from app.models.invoice_model import Invoice
import base64


def test_build_danfe_pdf_stub_base64_contains_pdf_signature():
    inv = Invoice(
        id="inv_pdf",
        order_id="ord_pdf",
        country="BR",
        invoice_type="NFCE",
        amount_cents=1234,
    )
    b64 = _build_danfe_pdf_stub_base64(inv)
    assert isinstance(b64, str) and len(b64) > 20
    assert b64.startswith("JVBER")  # "%PDF" em base64
    raw = base64.b64decode(b64)
    assert raw.startswith(b"%PDF-1.4")
    assert b"startxref" in raw and raw.rstrip().endswith(b"%%EOF")
