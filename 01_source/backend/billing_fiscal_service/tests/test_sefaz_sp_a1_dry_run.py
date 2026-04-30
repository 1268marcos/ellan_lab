from __future__ import annotations

import pytest

import app.core.config as cfg
from app.models.invoice_model import Invoice
from app.services.sefaz_sp_service import sefaz_sp_issue_invoice


@pytest.fixture
def br_nfce_invoice():
    return Invoice(
        id="inv_a1dry",
        order_id="ord_a1dry",
        country="BR",
        region="SP",
        currency="BRL",
        payment_method="PIX",
        fiscal_doc_subtype="NFC_E_65",
        emitter_cnpj="12.345.678/0001-99",
        consumer_cpf="123.456.789-09",
        amount_cents=1000,
        order_snapshot={"order": {"sku_id": "sku-a1"}},
    )


def test_sefaz_stub_pending_when_dry_run_disabled(monkeypatch, br_nfce_invoice):
    monkeypatch.setattr(cfg.settings, "fiscal_a1_dry_run_enabled", False)
    out = sefaz_sp_issue_invoice(br_nfce_invoice)
    sig = out["xml_content"]["signature"]
    assert sig["mode"] == "A1_STUB_PENDING"
    assert "dry_run_signature_b64" not in sig


def test_sefaz_dry_run_metadata_when_enabled(monkeypatch, br_nfce_invoice):
    monkeypatch.setattr(cfg.settings, "fiscal_a1_dry_run_enabled", True)
    monkeypatch.setattr(cfg.settings, "fiscal_a1_dry_run_hmac_secret", "pytest-hmac-secret")
    monkeypatch.setattr(cfg.settings, "fiscal_a1_dry_run_cert_ref", "TEST-CERT-REF")
    out = sefaz_sp_issue_invoice(br_nfce_invoice)
    sig = out["xml_content"]["signature"]
    assert sig["mode"] == "A1_DRY_RUN"
    assert sig.get("dry_run_local_verification_ok") is True
    assert sig.get("dry_run_signature_b64")
    assert sig.get("dry_run_content_sha256_hex")
