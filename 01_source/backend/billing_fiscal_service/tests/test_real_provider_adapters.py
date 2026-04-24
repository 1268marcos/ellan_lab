from app.models.invoice_model import Invoice
from app.services import at_pt_real_adapter as at
from app.services import sefaz_svrs_real_adapter as br


def _inv(country: str) -> Invoice:
    i = Invoice()
    i.id = "inv_x_123456"
    i.order_id = "ord_x"
    i.country = country
    i.currency = "BRL" if country == "BR" else "EUR"
    i.amount_cents = 1234
    i.payment_method = "PIX"
    i.tax_breakdown_json = {"lines": []}
    i.order_snapshot = {"order": {"id": "ord_x"}}
    return i


def test_br_real_adapter_normalizes_issue(monkeypatch):
    monkeypatch.setattr(
        br,
        "provider_issue_invoice",
        lambda *_args, **_kwargs: {
            "status": "AUTHORIZED",
            "number": "9001",
            "series": "S-1",
            "chave": "AKBR",
            "protocol_number": "P-1",
        },
    )
    out = br.issue_invoice_real_or_fallback(_inv("BR"))
    assert out["provider"] == "svrs_real"
    assert out["status"] == "ISSUED"
    assert out["invoice_number"] == "9001"
    assert out["access_key"] == "AKBR"


def test_br_real_adapter_fallback_on_error(monkeypatch):
    monkeypatch.setattr(
        br,
        "provider_issue_invoice",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            br.RealProviderClientError(
                code="PROVIDER_TEST_ERROR",
                message="boom",
                retryable=False,
                attempts=1,
            )
        ),
    )
    monkeypatch.setattr(br, "sefaz_sp_issue_invoice", lambda *_: {"provider": "sefaz_sp", "government_response": {"raw": {}}})
    out = br.issue_invoice_real_or_fallback(_inv("BR"))
    assert out["provider"] == "sefaz_sp"
    assert out["government_response"]["raw"]["provider_adapter"] == "svrs_real_adapter_fallback"


def test_pt_real_adapter_normalizes_issue(monkeypatch):
    monkeypatch.setattr(
        at,
        "provider_issue_invoice",
        lambda *_args, **_kwargs: {"status": "ACCEPTED", "number": "AT-77", "series": "PT-1", "hash": "AKPT"},
    )
    out = at.issue_invoice_real_or_fallback(_inv("PT"))
    assert out["provider"] == "at_real"
    assert out["status"] == "ISSUED"
    assert out["access_key"] == "AKPT"
