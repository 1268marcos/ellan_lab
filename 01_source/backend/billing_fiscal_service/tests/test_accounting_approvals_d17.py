from __future__ import annotations

from app.api import routes_admin_fiscal as raf


def test_compute_diff_empty_when_identical_payloads():
    p = {"approval": {"owner": "a", "status": "S", "eta": ""}, "d13_critical_checklist": {"done_items": 1, "total_items": 3}}
    assert raf._compute_accounting_approval_changed(p, p) == []


def test_compute_diff_detects_owner_change():
    cur = {"approval": {"owner": "x", "status": "S", "eta": ""}, "d13_critical_checklist": {"done_items": 0, "total_items": 0}}
    prev = {"approval": {"owner": "y", "status": "S", "eta": ""}, "d13_critical_checklist": {"done_items": 0, "total_items": 0}}
    ch = raf._compute_accounting_approval_changed(cur, prev)
    assert any(x.get("field") == "approval.owner" for x in ch)


def test_fingerprint_stable_for_same_diff():
    cur = {"approval": {"owner": "x", "status": "S", "eta": ""}, "d13_critical_checklist": {"done_items": 0, "total_items": 0}}
    prev = {"approval": {"owner": "y", "status": "S", "eta": ""}, "d13_critical_checklist": {"done_items": 0, "total_items": 0}}
    ch = raf._compute_accounting_approval_changed(cur, prev)
    fp1 = raf._fingerprint_accounting_diff(ch)
    fp2 = raf._fingerprint_accounting_diff(raf._compute_accounting_approval_changed(cur, prev))
    assert fp1 == fp2
    assert fp1 != ""


def test_payload_json_as_dict_parses_string():
    raw = '{"approval": {"owner": "u", "status": "PENDING_REVIEW", "eta": ""}}'
    d = raf._payload_json_as_dict(raw)
    assert d.get("approval", {}).get("owner") == "u"
