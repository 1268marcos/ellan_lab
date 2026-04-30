from __future__ import annotations

import pytest

import app.core.config as cfg
from app.services import fiscal_a1_dry_run_service as dr


def test_digest_and_signature_roundtrip(monkeypatch):
    monkeypatch.setattr(cfg.settings, "fiscal_a1_dry_run_hmac_secret", "unit-test-secret")
    xml = '<?xml version="1.0"?><NFe><infNFe Id="NFeX">a</infNFe></NFe>'
    ext = dr.build_a1_dry_run_signature_extensions(xml_preview=xml, access_key="k1")
    assert ext["dry_run_content_sha256_hex"] == dr.compute_content_digest_sha256(xml)
    assert dr.verify_a1_dry_run_signature(xml_preview=xml, signature_block=ext) is True


def test_verify_fails_on_tampered_xml(monkeypatch):
    monkeypatch.setattr(cfg.settings, "fiscal_a1_dry_run_hmac_secret", "unit-test-secret")
    xml = "<a/>"
    ext = dr.build_a1_dry_run_signature_extensions(xml_preview=xml, access_key="k")
    assert dr.verify_a1_dry_run_signature(xml_preview="<a/> ", signature_block=ext) is False


def test_status_payload_flags(monkeypatch):
    monkeypatch.setattr(cfg.settings, "fiscal_a1_dry_run_enabled", True)
    monkeypatch.setattr(cfg.settings, "fiscal_a1_dry_run_cert_ref", "CERT-REF-1")
    monkeypatch.setattr(cfg.settings, "fiscal_a1_dry_run_hmac_secret", "s")
    st = dr.build_a1_dry_run_status_payload()
    assert st["fiscal_a1_dry_run_enabled"] is True
    assert st["fiscal_a1_dry_run_hmac_secret_configured"] is True
    assert st["fiscal_a1_dry_run_cert_ref"] == "CERT-REF-1"
