from __future__ import annotations

import pytest

from app.core.config import settings
from app.models.invoice_model import Invoice
from app.services.fiscal_consumer_gate import (
    ConsumerFiscalIncompleteError,
    assert_consumer_fiscal_ready_for_real_issue,
    order_snapshot_consumer_ready_for_real,
    uses_real_fiscal_route,
)


def _inv(*, country: str = "BR", emission_mode: str = "ONLINE", snapshot: dict | None, payload: dict | None):
    inv = Invoice(
        id="inv_test",
        order_id="ord_test",
        country=country,
        invoice_type="NFE",
        emission_mode=emission_mode,
        fiscal_doc_subtype="NFC_E_65",
    )
    inv.order_snapshot = snapshot
    inv.payload_json = payload
    return inv


def test_order_snapshot_legacy_br_ok():
    snap = {
        "consumer_cpf": "12345678909",
        "consumer_name": "Fulano",
        "order": {"receipt_email": "a@b.co"},
    }
    assert order_snapshot_consumer_ready_for_real(snap, country="BR") is True


def test_order_snapshot_profile_br_ok():
    snap = {
        "consumer_fiscal_profile": {
            "fiscal_data_consent": True,
            "tax_country": "BR",
            "tax_document_type": "CPF",
            "tax_document_value": "12345678909",
            "fiscal_email": "a@b.co",
            "fiscal_address_line1": "Rua A 1",
            "fiscal_address_city": "São Paulo",
            "fiscal_address_state": "SP",
            "fiscal_address_postal_code": "01310100",
            "fiscal_address_country": "BR",
        },
    }
    assert order_snapshot_consumer_ready_for_real(snap, country="BR") is True


def test_order_snapshot_br_incomplete():
    assert order_snapshot_consumer_ready_for_real({"consumer_name": "X"}, country="BR") is False


def test_assert_gate_skipped_for_stub_scenario(monkeypatch):
    monkeypatch.setattr(settings, "fiscal_require_complete_consumer_for_real_issue", True)
    monkeypatch.setattr(settings, "fiscal_real_provider_br_enabled", True)
    inv = _inv(
        snapshot={"consumer_name": "only"},
        payload={"stub_scenario": "timeout"},
    )
    assert_consumer_fiscal_ready_for_real_issue(inv)


def test_assert_gate_raises_when_real_and_incomplete(monkeypatch):
    monkeypatch.setattr(settings, "fiscal_require_complete_consumer_for_real_issue", True)
    monkeypatch.setattr(settings, "fiscal_real_provider_br_enabled", True)
    monkeypatch.setattr(settings, "fiscal_real_provider_pt_enabled", False)
    inv = _inv(snapshot={"consumer_name": "only"}, payload={})
    with pytest.raises(ConsumerFiscalIncompleteError):
        assert_consumer_fiscal_ready_for_real_issue(inv)


def test_uses_real_false_for_contingency(monkeypatch):
    monkeypatch.setattr(settings, "fiscal_real_provider_br_enabled", True)
    inv = _inv(country="BR", emission_mode="CONTINGENCY_SVRS", snapshot={}, payload={})
    assert uses_real_fiscal_route(inv) is False
