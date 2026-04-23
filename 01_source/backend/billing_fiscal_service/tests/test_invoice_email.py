from app.models.invoice_model import Invoice
from app.services.invoice_email_service import build_danfe_email_content, extract_receipt_email
from app.services.sefaz_sp_service import build_cce_xml_event_preview, sefaz_sp_cc_e_stub


def test_extract_receipt_email_from_order_snapshot():
    inv = Invoice(
        id="inv_1",
        order_id="ord_1",
        country="BR",
        order_snapshot={
            "order": {
                "id": "ord_1",
                "receipt_email": "  buyer@example.com ",
            }
        },
    )
    assert extract_receipt_email(inv) == "buyer@example.com"


def test_extract_receipt_email_guest_fallback():
    inv = Invoice(
        id="inv_2",
        order_id="ord_2",
        country="BR",
        order_snapshot={"order": {"guest_email": "g@example.org"}},
    )
    assert extract_receipt_email(inv) == "g@example.org"


def test_extract_receipt_email_none_when_missing():
    inv = Invoice(
        id="inv_3",
        order_id="ord_3",
        country="BR",
        order_snapshot={"order": {"id": "ord_3"}},
    )
    assert extract_receipt_email(inv) is None


def test_build_danfe_email_content_issued():
    inv = Invoice(
        id="inv_x",
        order_id="ord_x",
        country="BR",
        access_key="35200123456789012345678901234567890123456789",
        invoice_type="NFCE",
    )
    subj, body = build_danfe_email_content(invoice=inv, template="issued")
    assert "ord_x" in subj and "ord_x" in body
    assert "35200123456789012345678901234567890123456789" in body


def test_build_cce_xml_event_preview_escapes_text():
    xml = build_cce_xml_event_preview(
        access_key="35200123456789012345678901234567890123456789",
        sequence=3,
        correction_text="Correção com <tag> & ampersand",
        protocol_number="PROT123",
    )
    assert "110110" in xml
    assert "<tag>" not in xml or "&lt;tag&gt;" in xml
    assert "xml_event_preview" not in xml  # raw string, not key
    assert "&amp;" in xml


def test_sefaz_sp_cc_e_stub_includes_xml_preview():
    inv = Invoice(
        id="inv_cce",
        order_id="ord_cce",
        country="BR",
        access_key="35200123456789012345678901234567890123456789",
        government_response={"cce_events": [{"sequence": 1}]},
    )
    out = sefaz_sp_cc_e_stub(inv, "Texto da correção")
    assert out.get("xml_event_preview")
    assert "xCorrecao" in out["xml_event_preview"]
    assert out["sequence"] == 2
    assert out["raw"].get("xml_event_preview") == out["xml_event_preview"]
