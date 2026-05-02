"""Sprint 3 P0-1: GET /admin/fiscal/global/sprint3/e2e-audit-trail + serviço de trilha."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.routes_admin_fiscal import get_sprint3_e2e_audit_trail
from app.services.sprint3_e2e_audit_trail_service import (
    AUDIT_VERSION,
    SCOPE_SPRINT3_E2E_AUDIT_TRAIL,
    build_sprint3_e2e_audit_trail,
)


def test_build_sprint3_e2e_audit_trail_empty():
    out = build_sprint3_e2e_audit_trail([], status_filter="OPEN", date_filter=None, limit=200)
    assert out["scope"] == SCOPE_SPRINT3_E2E_AUDIT_TRAIL
    assert out["audit_version"] == AUDIT_VERSION
    assert out["decision"] == "GO"
    assert out["coverage"]["total"] == 0
    assert out["trail_rollups"]["total_gaps"] == 0
    assert out["items"] == []


def test_build_trail_paid_without_invoice_marks_emissao_gap():
    ts = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    row = SimpleNamespace(
        id="g1",
        gap_type="PAID_WITHOUT_INVOICE",
        severity="ERROR",
        status="OPEN",
        order_id="ord-1",
        invoice_id=None,
        details_json={"partner_id": "partner_x", "batch_id": "batch_y"},
        last_detected_at=ts,
    )
    out = build_sprint3_e2e_audit_trail([row], status_filter="OPEN", date_filter=None, limit=50)
    assert len(out["items"]) == 1
    item = out["items"][0]
    assert item["trail"]["pedido"]["status"] == "OK"
    assert item["trail"]["emissao"]["status"] == "GAP"
    assert "GAP_REGISTERED" in str(item["trail"]["reconciliacao"]["status"])
    assert out["trail_rollups"]["pedido_traceable_ok"] == 1
    assert out["trail_rollups"]["emissao_consistent_ok"] == 0
    assert out["trail_rollups"]["pedido_emissao_operational_keys_ok"] == 0


def test_build_trail_issued_without_paid_chain_when_keys_present():
    ts = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    row = SimpleNamespace(
        id="g2",
        gap_type="ISSUED_WITHOUT_PAID",
        severity="ERROR",
        status="OPEN",
        order_id="ord-2",
        invoice_id="inv-2",
        details_json={"partner_id": "p1", "batch_id": "b1"},
        last_detected_at=ts,
    )
    out = build_sprint3_e2e_audit_trail([row], status_filter="OPEN", date_filter=None, limit=50)
    item = out["items"][0]
    assert item["trail"]["emissao"]["status"] == "OK"
    assert out["trail_rollups"]["pedido_emissao_operational_keys_ok"] == 1
    assert out["trail_rollups"]["pedido_emissao_rate"] == 1.0


def test_get_sprint3_e2e_audit_trail_invalid_date():
    with pytest.raises(HTTPException) as ei:
        get_sprint3_e2e_audit_trail(
            date="not-a-date",
            status="OPEN",
            limit=10,
            refresh=False,
            db=None,
            _=None,
        )
    assert ei.value.status_code == 400
