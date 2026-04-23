from datetime import datetime, timedelta, timezone

from app.services.cancellation_policy_service import (
    CancelPolicyAction,
    resolve_cancel_policy,
)


def test_br_void_within_30m():
    issued = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)
    now = issued + timedelta(minutes=15)
    r = resolve_cancel_policy(issued_at=issued, now=now, country="BR", fiscal_doc_subtype="NFC_E_65")
    assert r.action == CancelPolicyAction.VOID_NFCE


def test_br_correction_window():
    issued = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)
    now = issued + timedelta(hours=2)
    r = resolve_cancel_policy(issued_at=issued, now=now, country="BR", fiscal_doc_subtype="NFC_E_65")
    assert r.action == CancelPolicyAction.CORRECTION_LETTER_REQUIRED


def test_br_complementary_after_24h():
    issued = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)
    now = issued + timedelta(hours=30)
    r = resolve_cancel_policy(issued_at=issued, now=now, country="BR", fiscal_doc_subtype="NFC_E_65")
    assert r.action == CancelPolicyAction.COMPLEMENTARY_INVOICE_REQUIRED


def test_non_br_manual():
    issued = datetime(2026, 4, 23, 12, 0, tzinfo=timezone.utc)
    now = issued + timedelta(minutes=5)
    r = resolve_cancel_policy(issued_at=issued, now=now, country="PT", fiscal_doc_subtype="SAFT_PT")
    assert r.action == CancelPolicyAction.MANUAL_REVIEW
