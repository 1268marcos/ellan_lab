from app.api.routes_admin_fiscal import _build_danfe_pdf_stub_base64
from app.models.invoice_model import Invoice


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
