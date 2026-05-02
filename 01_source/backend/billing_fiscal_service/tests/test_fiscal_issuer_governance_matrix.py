"""P0 Fiscal ELLAN LAB: GET /admin/fiscal/issuer-governance-matrix."""

from __future__ import annotations

from app.api.routes_admin_fiscal import get_fiscal_issuer_governance_matrix
from app.services.fiscal_issuer_governance_matrix_service import (
    SCOPE_FISCAL_ISSUER_GOVERNANCE_MATRIX,
    build_fiscal_issuer_governance_matrix,
)


def test_build_fiscal_issuer_governance_matrix_rows(monkeypatch):
    monkeypatch.setattr(
        "app.services.fiscal_issuer_governance_matrix_service.list_provider_status",
        lambda _db: [
            {
                "country": "BR",
                "enabled": False,
                "mode": "stub",
                "last_status": "SKIPPED",
                "last_latency_ms": None,
                "checked_at": None,
            },
            {
                "country": "PT",
                "enabled": True,
                "mode": "real",
                "last_status": "OK",
                "last_latency_ms": 120,
                "checked_at": "2026-05-01T00:00:00+00:00",
            },
        ],
    )
    out = build_fiscal_issuer_governance_matrix(None)
    assert out["scope"] == SCOPE_FISCAL_ISSUER_GOVERNANCE_MATRIX
    assert out["summary"]["matrix_rows"] == 3
    assert out["summary"]["governance_complete"] is True
    br = next(x for x in out["matrix"] if x["country"] == "BR" and x["tenant_id"] == "*")
    assert br["effective_mode"] == "stub"
    pt = next(x for x in out["matrix"] if x["country"] == "PT" and x["tenant_id"] == "*")
    assert pt["effective_mode"] == "real"


def test_get_fiscal_issuer_governance_matrix_route(monkeypatch):
    monkeypatch.setattr(
        "app.services.fiscal_issuer_governance_matrix_service.list_provider_status",
        lambda _db: [{"country": "BR", "enabled": False, "mode": "stub", "last_status": "NEVER_TESTED"}],
    )
    r = get_fiscal_issuer_governance_matrix(db=None, _=None)
    assert r["ok"] is True
    assert r["scope"] == SCOPE_FISCAL_ISSUER_GOVERNANCE_MATRIX
