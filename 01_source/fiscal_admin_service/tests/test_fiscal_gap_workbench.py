from __future__ import annotations

from unittest.mock import patch

import pytest

API = "/api/v1/fiscal-admin"


def test_workbench_admin_only(client, monkeypatch):
    monkeypatch.setenv("BILLING_FISCAL_LIVE_ENABLED", "false")
    from app.core.config import get_settings

    get_settings.cache_clear()
    client.post(f"{API}/seed")
    r = client.get(f"{API}/fiscal-ops/reconciliation-gaps/workbench")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["admin_count"] >= 1
    assert body["summary"]["billing_count"] == 0
    assert body["billing_available"] is False
    assert any(i["source"] == "admin" for i in body["items"])


def test_workbench_merges_billing(client, monkeypatch):
    monkeypatch.setenv("BILLING_FISCAL_LIVE_ENABLED", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()
    client.post(f"{API}/seed")

    billing_payload = {
        "count": 1,
        "items": [
            {
                "id": "frg_test_billing_01",
                "dedupe_key": "paid_without_invoice:ORD-99",
                "gap_type": "PAID_WITHOUT_INVOICE",
                "severity": "ERROR",
                "status": "OPEN",
                "order_id": "ORD-99",
                "invoice_id": None,
                "details_json": {"message": "test"},
                "first_detected_at": "2026-05-23T10:00:00+00:00",
                "last_detected_at": "2026-05-23T10:00:00+00:00",
                "resolved_at": None,
            }
        ],
    }

    with patch(
        "app.services.fiscal_gap_workbench_service.billing_fiscal_client.fetch_reconciliation_gaps",
        return_value=billing_payload,
    ):
        r = client.get(f"{API}/fiscal-ops/reconciliation-gaps/workbench")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["billing_count"] == 1
    assert body["billing_available"] is True
    sources = {i["source"] for i in body["items"]}
    assert "billing" in sources
    assert "admin" in sources


def test_workbench_resolve_billing(client, monkeypatch):
    monkeypatch.setenv("BILLING_FISCAL_LIVE_ENABLED", "true")
    from app.core.config import get_settings

    get_settings.cache_clear()

    resolved = {
        "id": "frg_test_billing_01",
        "dedupe_key": "k",
        "gap_type": "PAID_WITHOUT_INVOICE",
        "severity": "ERROR",
        "status": "RESOLVED",
        "order_id": "ORD-99",
        "invoice_id": None,
        "details_json": {},
        "first_detected_at": "2026-05-23T10:00:00+00:00",
        "last_detected_at": "2026-05-23T10:00:00+00:00",
        "resolved_at": "2026-05-23T11:00:00+00:00",
    }
    with patch(
        "app.services.fiscal_gap_workbench_service.billing_fiscal_client.resolve_reconciliation_gap",
        return_value=resolved,
    ):
        r = client.patch(
            f"{API}/fiscal-ops/reconciliation-gaps/workbench/frg_test_billing_01",
            params={"source": "billing"},
            json={"status": "RESOLVED"},
        )
    assert r.status_code == 200
    assert r.json()["status"] == "RESOLVED"
    assert r.json()["source"] == "billing"
