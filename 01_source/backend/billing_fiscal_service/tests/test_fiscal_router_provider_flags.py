from app.models.invoice_model import Invoice
from app.services import fiscal_router_service as fr


def _inv(country: str = "BR") -> Invoice:
    inv = Invoice()
    inv.id = "inv_test"
    inv.order_id = "ord_test"
    inv.country = country
    return inv


def test_route_issue_br_stub_when_flag_off(monkeypatch):
    monkeypatch.setattr(fr.settings, "fiscal_real_provider_br_enabled", False)
    monkeypatch.setattr(fr, "sefaz_sp_issue_invoice", lambda _: {"provider": "sefaz_sp"})
    out = fr.route_issue_invoice(_inv("BR"))
    assert out["provider"] == "sefaz_sp"


def test_route_issue_br_real_adapter_when_flag_on(monkeypatch):
    monkeypatch.setattr(fr.settings, "fiscal_real_provider_br_enabled", True)
    monkeypatch.setattr(fr, "svrs_issue_real_or_fallback", lambda _: {"provider": "svrs_real_adapter"})
    out = fr.route_issue_invoice(_inv("BR"))
    assert out["provider"] == "svrs_real_adapter"


def test_route_issue_pt_real_adapter_when_flag_on(monkeypatch):
    monkeypatch.setattr(fr.settings, "fiscal_real_provider_pt_enabled", True)
    monkeypatch.setattr(fr, "at_issue_real_or_fallback", lambda _: {"provider": "at_real_adapter"})
    out = fr.route_issue_invoice(_inv("PT"))
    assert out["provider"] == "at_real_adapter"
