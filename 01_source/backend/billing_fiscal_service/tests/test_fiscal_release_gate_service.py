from __future__ import annotations

import app.core.config as cfg
from app.services.fiscal_release_gate_service import build_fiscal_release_gate_payload


def test_release_gate_payload_shape(monkeypatch):
    monkeypatch.setattr(cfg.settings, "fiscal_real_provider_br_enabled", False)
    monkeypatch.setattr(cfg.settings, "fiscal_real_provider_pt_enabled", False)
    monkeypatch.setattr(cfg.settings, "fiscal_a1_dry_run_enabled", False)
    monkeypatch.setattr(cfg.settings, "invoice_smtp_enabled", False)
    p = build_fiscal_release_gate_payload()
    assert p["scope"] == "RELEASE_GATE_FISCAL_ENV"
    assert p["stub_only_recommended"] is True
    assert "rollback_hints" in p
    assert "providers" in p


def test_release_gate_risk_when_br_real_without_url(monkeypatch):
    monkeypatch.setattr(cfg.settings, "fiscal_real_provider_br_enabled", True)
    monkeypatch.setattr(cfg.settings, "fiscal_real_provider_base_url_br", None)
    monkeypatch.setattr(cfg.settings, "fiscal_real_provider_pt_enabled", False)
    p = build_fiscal_release_gate_payload()
    assert "BR_REAL_ENABLED_SEM_BASE_URL_BR" in p["risk_flags"]
