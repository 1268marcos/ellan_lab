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


def test_build_trail_multi_partner_presencial_rollups():
    ts = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    rows = [
        SimpleNamespace(
            id="a",
            gap_type="PAID_WITHOUT_INVOICE",
            severity="ERROR",
            status="OPEN",
            order_id="o1",
            invoice_id=None,
            details_json={"partner_id": "BR-1", "batch_id": "b1"},
            last_detected_at=ts,
        ),
        SimpleNamespace(
            id="b",
            gap_type="PAID_WITHOUT_INVOICE",
            severity="WARN",
            status="OPEN",
            order_id="o2",
            invoice_id=None,
            details_json={
                "partner_id": "PT-9",
                "batch_id": "b2",
                "presencial_signoff": {"operator": "ops-1", "signed_at": "2026-05-01T10:00:00+00:00", "location": "LIS"},
            },
            last_detected_at=ts,
        ),
        SimpleNamespace(
            id="c",
            gap_type="ISSUED_WITHOUT_PAID",
            severity="ERROR",
            status="OPEN",
            order_id="o3",
            invoice_id="inv-3",
            details_json={"partner_id": "BR-1", "batch_id": "b3"},
            last_detected_at=ts,
        ),
    ]
    out = build_sprint3_e2e_audit_trail(rows, status_filter="OPEN", date_filter=None, limit=50)
    assert out["audit_version"] == AUDIT_VERSION
    rr = out["trail_rollups"]
    assert rr["distinct_partner_count"] == 2
    assert set(rr["distinct_partner_ids"]) == {"BR-1", "PT-9"}
    assert rr["presencial_signed_rows"] == 1
    assert rr["presencial_pending_rows"] == 2
    assert rr["presencial_completion_rate"] == pytest.approx(0.3333, rel=1e-3)
    signed_item = next(i for i in out["items"] if i["id"] == "b")
    assert signed_item["presencial"]["status"] == "SIGNED"
    assert signed_item["presencial"]["operator"] == "ops-1"
    pending = next(i for i in out["items"] if i["id"] == "a")
    assert pending["presencial"]["status"] == "PENDING"
    hz = out["handoff_evidence"]["daily_zip_attachment"]
    assert "SPRINT3_E2E_AUDIT_TRAIL" in hz["filenames_pattern"][0]
    assert "P0_1B_PARTNER_RECONCILIATION" in hz["filenames_pattern"][1]
    assert "appendP01bSignedZipEntries" in hz["source"]


def test_presencial_signoff_incomplete_operator_is_pending():
    ts = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    row = SimpleNamespace(
        id="x",
        gap_type="PAID_WITHOUT_INVOICE",
        severity="ERROR",
        status="OPEN",
        order_id="o9",
        invoice_id=None,
        details_json={
            "partner_id": "p9",
            "batch_id": "b9",
            "presencial_signoff": {"operator": "", "signed_at": "2026-05-01T11:00:00+00:00"},
        },
        last_detected_at=ts,
    )
    out = build_sprint3_e2e_audit_trail([row], status_filter="OPEN", date_filter=None, limit=10)
    assert out["items"][0]["presencial"]["status"] == "PENDING"
    assert out["trail_rollups"]["presencial_signed_rows"] == 0
