"""Sprint 2 D17: GET divergence-health + POST retention — rotas admin fiscal com DB fake."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.api.routes_admin_fiscal import get_accounting_approvals_divergence_health, post_accounting_approvals_retention


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


class _FakeDBEnsureOnly:
    def execute(self, statement, params=None):
        s = str(statement)
        if "CREATE TABLE IF NOT EXISTS fiscal_accounting_approvals" in s:
            return _MappingsResult()
        if "CREATE INDEX IF NOT EXISTS ix_fiscal_accounting_approvals_created_at" in s:
            return _MappingsResult()
        if "CREATE INDEX IF NOT EXISTS ix_fiscal_accounting_approvals_status" in s:
            return _MappingsResult()
        raise AssertionError(f"SQL inesperado (ensure): {s[:350]}")

    def commit(self) -> None:
        return None


class _FakeDBDivergenceSingleRow(_FakeDBEnsureOnly):
    def execute(self, statement, params=None):
        s = str(statement)
        if "LIMIT :lim" in s and "ORDER BY created_at DESC" in s and "fiscal_accounting_approvals" in s:
            return _MappingsResult(
                rows=[
                    {
                        "id": "only",
                        "owner": "a",
                        "eta": None,
                        "status": "S",
                        "payload_json": {},
                        "created_at": datetime.now(timezone.utc),
                    }
                ]
            )
        return super().execute(statement, params)


def test_divergence_health_under_two_snapshots_returns_note():
    db = _FakeDBDivergenceSingleRow()
    out = get_accounting_approvals_divergence_health(window=8, prolonged_edges=3, db=db, _=None)
    assert out["ok"] is True
    assert out["snapshots_considered"] == 1
    assert out["edges"] == []
    assert out["prolonged_identical_diff"] is False
    assert "Menos de dois" in out["note"]


def _payload(owner: str) -> dict:
    return {"approval": {"owner": owner, "status": "S", "eta": ""}, "d13_critical_checklist": {"done_items": 0, "total_items": 0}}


class _FakeDBDivergenceTwoRows(_FakeDBEnsureOnly):
    def execute(self, statement, params=None):
        s = str(statement)
        if "LIMIT :lim" in s and "ORDER BY created_at DESC" in s and "fiscal_accounting_approvals" in s:
            ts = datetime(2026, 5, 3, 10, 0, 0, tzinfo=timezone.utc)
            return _MappingsResult(
                rows=[
                    {"id": "n0", "owner": "o", "eta": None, "status": "S", "payload_json": _payload("x"), "created_at": ts},
                    {"id": "n1", "owner": "o", "eta": None, "status": "S", "payload_json": _payload("y"), "created_at": ts},
                ]
            )
        return super().execute(statement, params)


def test_divergence_health_two_snapshots_builds_edges_and_policy():
    """Uma aresta; diff não vazio no par mais recente; «prolonged» exige ≥2 arestas com o mesmo fingerprint."""
    db = _FakeDBDivergenceTwoRows()
    out = get_accounting_approvals_divergence_health(window=8, prolonged_edges=3, db=db, _=None)
    assert out["ok"] is True
    assert out["snapshots_considered"] == 2
    assert len(out["edges"]) == 1
    assert out["edges"][0]["newer_id"] == "n0"
    assert out["edges"][0]["older_id"] == "n1"
    assert out["latest_pair_has_diff"] is True
    assert out["prolonged_identical_diff"] is False
    assert out["policy"] == {"window": 8, "prolonged_edges": 3}


class _FakeDBRetentionDryRun(_FakeDBEnsureOnly):
    def execute(self, statement, params=None):
        s = str(statement)
        if "SELECT COUNT(*)::INT AS c FROM fiscal_accounting_approvals" in s.replace("\n", " ") and "WHERE" not in s:
            return _MappingsResult(first={"c": 12})
        if "WHERE created_at < :cutoff" in s and "COUNT(*)" in s:
            return _MappingsResult(first={"c": 5})
        if "SELECT id" in s and "WHERE created_at < :cutoff" in s and "ORDER BY created_at ASC" in s:
            return _MappingsResult(rows=[])
        return super().execute(statement, params)


def test_retention_dry_run_no_delete_selected_when_max_deletable_zero():
    """keep_minimum acima do total → max_deletable 0 → nada selecionado."""
    db = _FakeDBRetentionDryRun()
    out = post_accounting_approvals_retention(
        payload={"older_than_days": 90, "keep_minimum": 50, "dry_run": True},
        db=db,
        _=None,
    )
    assert out["ok"] is True
    assert out["dry_run"] is True
    assert out["total_rows_before"] == 12
    assert out["max_deletable_respecting_keep_minimum"] == 0
    assert out["selected_for_delete"] == 0


def test_retention_rejects_older_than_days_out_of_range():
    db = _FakeDBEnsureOnly()
    with pytest.raises(HTTPException) as ei:
        post_accounting_approvals_retention(payload={"older_than_days": 3, "keep_minimum": 10, "dry_run": True}, db=db, _=None)
    assert ei.value.status_code == 400


def test_retention_rejects_keep_minimum_out_of_range():
    db = _FakeDBEnsureOnly()
    with pytest.raises(HTTPException) as ei:
        post_accounting_approvals_retention(
            payload={"older_than_days": 90, "keep_minimum": 20_000, "dry_run": True},
            db=db,
            _=None,
        )
    assert ei.value.status_code == 400
