"""Sprint 2 D13/D14: POST accounting-approval + GET latest — rotas admin fiscal com DB fake."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.api.routes_admin_fiscal import get_latest_accounting_approval, post_accounting_approval


class _MappingsResult:
    def __init__(self, rows: list | None = None, first: dict | None = None):
        self._rows = [] if rows is None else rows
        self._first = first

    def mappings(self):
        return self

    def all(self):
        return self._rows

    def first(self):
        return self._first


class _FakeDBPostLatest:
    """Garante tabela, grava INSERT em memória, devolve a última linha no SELECT latest."""

    def __init__(self):
        self._last_row: dict | None = None

    def execute(self, statement, params=None):
        s = str(statement)
        if "CREATE TABLE IF NOT EXISTS fiscal_accounting_approvals" in s:
            return _MappingsResult()
        if "CREATE INDEX IF NOT EXISTS ix_fiscal_accounting_approvals_created_at" in s:
            return _MappingsResult()
        if "CREATE INDEX IF NOT EXISTS ix_fiscal_accounting_approvals_status" in s:
            return _MappingsResult()
        if "INSERT INTO fiscal_accounting_approvals" in s:
            p = params or {}
            raw = p.get("payload_json")
            payload_obj = json.loads(raw) if isinstance(raw, str) else (raw or {})
            now = p["created_at"]
            self._last_row = {
                "id": p["id"],
                "owner": p["owner"],
                "eta": p.get("eta"),
                "status": p["status"],
                "payload_json": payload_obj,
                "created_at": now,
                "updated_at": now,
            }
            return _MappingsResult()
        if "ORDER BY created_at DESC" in s and "LIMIT 1" in s and "SELECT id, owner" in s.replace("\n", " "):
            return _MappingsResult(first=self._last_row)
        raise AssertionError(f"SQL inesperado (post/latest): {s[:380]}")

    def commit(self) -> None:
        return None


def test_get_latest_when_empty_returns_null_item():
    db = _FakeDBPostLatest()
    out = get_latest_accounting_approval(db=db, _=None)
    assert out["ok"] is True
    assert out["item"] is None


def test_post_accounting_approval_then_latest_roundtrip():
    db = _FakeDBPostLatest()
    body = {
        "approval": {"owner": "contabil", "status": "DRAFT", "eta": ""},
        "d13_critical_checklist": {"done_items": 0, "total_items": 3},
    }
    created = post_accounting_approval(payload=body, db=db, _=None)
    assert created["ok"] is True
    assert str(created["id"]).startswith("faa_")
    assert created["owner"] == "contabil"
    assert created["status"] == "DRAFT"

    latest = get_latest_accounting_approval(db=db, _=None)
    assert latest["ok"] is True
    assert latest["item"]["id"] == created["id"]
    assert latest["item"]["owner"] == "contabil"
    assert latest["item"]["payload_json"] == body


def test_post_accounting_approval_rejects_invalid_eta():
    db = _FakeDBPostLatest()
    with pytest.raises(HTTPException) as ei:
        post_accounting_approval(
            payload={"approval": {"owner": "x", "status": "S", "eta": "não-é-iso"}},
            db=db,
            _=None,
        )
    assert ei.value.status_code == 400
