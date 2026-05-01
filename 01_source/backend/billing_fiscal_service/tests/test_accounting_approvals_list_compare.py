"""Sprint 2 D15/D16: GET list + GET compare (rotas admin fiscal) com DB fake — paridade com frontend fiscalAccountingApprovalsHistory."""

from __future__ import annotations

from datetime import datetime, timezone

from app.api.routes_admin_fiscal import compare_accounting_approval_snapshots, list_accounting_approvals


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


class _FakeDBList:
    """Responde a _ensure_* + SELECT paginado + COUNT do list_accounting_approvals."""

    def __init__(self, rows: list[dict], total: int):
        self._rows = rows
        self._total = total

    def execute(self, statement, params=None):
        s = str(statement)
        if "CREATE TABLE IF NOT EXISTS fiscal_accounting_approvals" in s:
            return _MappingsResult()
        if "CREATE INDEX IF NOT EXISTS ix_fiscal_accounting_approvals_created_at" in s:
            return _MappingsResult()
        if "CREATE INDEX IF NOT EXISTS ix_fiscal_accounting_approvals_status" in s:
            return _MappingsResult()
        if "COUNT(*)" in s and "fiscal_accounting_approvals" in s:
            return _MappingsResult(first={"total": self._total})
        if "FROM fiscal_accounting_approvals" in s and "LIMIT :limit OFFSET :offset" in s:
            return _MappingsResult(rows=list(self._rows))
        raise AssertionError(f"SQL inesperado (list): {s[:400]}")

    def commit(self) -> None:
        return None


class _FakeDBListCapture(_FakeDBList):
    """Guarda parâmetros SQL do SELECT paginado e do COUNT quando há filtros."""

    def __init__(self, rows: list[dict], total: int):
        super().__init__(rows, total)
        self.list_params: dict | None = None
        self.count_params: dict | None = None

    def execute(self, statement, params=None):
        s = str(statement)
        if "COUNT(*)" in s and "fiscal_accounting_approvals" in s:
            self.count_params = dict(params or {})
            return _MappingsResult(first={"total": self._total})
        if "FROM fiscal_accounting_approvals" in s and "LIMIT :limit OFFSET :offset" in s:
            self.list_params = dict(params or {})
            return _MappingsResult(rows=list(self._rows))
        return super().execute(statement, params)


def test_list_accounting_approvals_owner_filter_wraps_like_pattern():
    db = _FakeDBListCapture(rows=[], total=0)
    list_accounting_approvals(
        owner="  ops-br  ",
        status=None,
        date_from=None,
        date_to=None,
        limit=10,
        offset=0,
        db=db,
        _=None,
    )
    assert db.list_params is not None
    assert db.count_params is not None
    assert db.list_params.get("owner") == "%ops-br%"
    assert db.count_params.get("owner") == "%ops-br%"


def test_list_accounting_approvals_status_and_dates_trimmed_in_params():
    db = _FakeDBListCapture(rows=[], total=0)
    list_accounting_approvals(
        owner=None,
        status="  REVIEW  ",
        date_from=" 2026-03-10 ",
        date_to=" 2026-03-11 ",
        limit=5,
        offset=0,
        db=db,
        _=None,
    )
    assert db.list_params.get("status") == "REVIEW"
    assert db.list_params.get("date_from") == "2026-03-10"
    assert db.list_params.get("date_to") == "2026-03-11"
    assert db.count_params.get("status") == "REVIEW"


def test_list_accounting_approvals_returns_items_total_and_ok():
    ts = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
    rows = [
        {
            "id": "snap-a",
            "owner": "ops",
            "eta": None,
            "status": "PENDING_REVIEW",
            "payload_json": {"approval": {"owner": "ops", "notes": "n"}},
            "created_at": ts,
            "updated_at": ts,
        },
        {
            "id": "snap-b",
            "owner": "ops2",
            "eta": ts,
            "status": "OK",
            "payload_json": {},
            "created_at": ts,
            "updated_at": ts,
        },
    ]
    db = _FakeDBList(rows=rows, total=2)
    out = list_accounting_approvals(owner=None, status=None, date_from=None, date_to=None, limit=20, offset=0, db=db, _=None)
    assert out["ok"] is True
    assert out["total"] == 2
    assert out["count"] == 2
    assert len(out["items"]) == 2
    assert out["items"][0]["id"] == "snap-a"
    assert out["items"][0]["created_at"] == ts.isoformat()
    assert out["items"][1]["eta"] == ts.isoformat()


class _FakeDBCompareEmpty:
    def execute(self, statement, params=None):
        s = str(statement)
        if "CREATE TABLE IF NOT EXISTS fiscal_accounting_approvals" in s:
            return _MappingsResult()
        if "CREATE INDEX IF NOT EXISTS ix_fiscal_accounting_approvals_created_at" in s:
            return _MappingsResult()
        if "CREATE INDEX IF NOT EXISTS ix_fiscal_accounting_approvals_status" in s:
            return _MappingsResult()
        if "FROM fiscal_accounting_approvals" in s and "WHERE id = :id" in s:
            return _MappingsResult(first=None)
        if "FROM fiscal_accounting_approvals" in s and "ORDER BY created_at DESC" in s:
            return _MappingsResult(first=None)
        raise AssertionError(f"SQL inesperado (compare empty): {s[:400]}")

    def commit(self) -> None:
        return None


def test_compare_accounting_approvals_empty_table_returns_sem_snapshots():
    db = _FakeDBCompareEmpty()
    out = compare_accounting_approval_snapshots(current_id=None, previous_id=None, db=db, _=None)
    assert out["ok"] is True
    assert out["current"] is None
    assert out["previous"] is None
    assert "Sem snapshots" in out["diff"]["summary"]


class _FakeDBComparePair:
    """Dois snapshots por ORDER BY OFFSET 0 e 1."""

    def __init__(self):
        self.ts = datetime(2026, 5, 2, 8, 0, 0, tzinfo=timezone.utc)
        self.cur = {
            "id": "c1",
            "owner": "a",
            "eta": None,
            "status": "S1",
            "payload_json": {"approval": {"owner": "x", "status": "S", "eta": ""}, "d13_critical_checklist": {"done_items": 1, "total_items": 3}},
            "created_at": self.ts,
        }
        self.prev = {
            "id": "p1",
            "owner": "a",
            "eta": None,
            "status": "S0",
            "payload_json": {"approval": {"owner": "y", "status": "S", "eta": ""}, "d13_critical_checklist": {"done_items": 0, "total_items": 0}},
            "created_at": self.ts,
        }

    def execute(self, statement, params=None):
        s = str(statement)
        if "CREATE TABLE IF NOT EXISTS fiscal_accounting_approvals" in s:
            return _MappingsResult()
        if "CREATE INDEX IF NOT EXISTS ix_fiscal_accounting_approvals_created_at" in s:
            return _MappingsResult()
        if "CREATE INDEX IF NOT EXISTS ix_fiscal_accounting_approvals_status" in s:
            return _MappingsResult()
        if "FROM fiscal_accounting_approvals" in s and "ORDER BY created_at DESC" in s:
            off = (params or {}).get("offset", 0)
            if int(off) == 0:
                return _MappingsResult(first=self.cur)
            return _MappingsResult(first=self.prev)
        raise AssertionError(f"SQL inesperado (compare pair): {s[:400]}")

    def commit(self) -> None:
        return None


def test_compare_two_latest_snapshots_reports_changed_fields():
    db = _FakeDBComparePair()
    out = compare_accounting_approval_snapshots(current_id=None, previous_id=None, db=db, _=None)
    assert out["ok"] is True
    assert out["current"]["id"] == "c1"
    assert out["previous"]["id"] == "p1"
    assert out["diff"]["changed"]
    assert any(c.get("field") == "approval.owner" for c in out["diff"]["changed"])


class _FakeDBCompareExplicitIds:
    """Respostas a SELECT … WHERE id = :id para current_id e previous_id."""

    def __init__(self, ts: datetime):
        self.ts = ts

    def execute(self, statement, params=None):
        s = str(statement)
        if "CREATE TABLE IF NOT EXISTS fiscal_accounting_approvals" in s:
            return _MappingsResult()
        if "CREATE INDEX IF NOT EXISTS ix_fiscal_accounting_approvals_created_at" in s:
            return _MappingsResult()
        if "CREATE INDEX IF NOT EXISTS ix_fiscal_accounting_approvals_status" in s:
            return _MappingsResult()
        if "FROM fiscal_accounting_approvals" in s and "WHERE id = :id" in s:
            rid = str((params or {}).get("id", ""))
            if rid == "snap-cur":
                return _MappingsResult(
                    first={
                        "id": "snap-cur",
                        "owner": "o1",
                        "eta": None,
                        "status": "S1",
                        "payload_json": {"approval": {"owner": "u", "status": "S", "eta": ""}, "d13_critical_checklist": {"done_items": 0, "total_items": 0}},
                        "created_at": self.ts,
                    }
                )
            if rid == "snap-prev":
                return _MappingsResult(
                    first={
                        "id": "snap-prev",
                        "owner": "o1",
                        "eta": None,
                        "status": "S0",
                        "payload_json": {"approval": {"owner": "v", "status": "S", "eta": ""}, "d13_critical_checklist": {"done_items": 0, "total_items": 0}},
                        "created_at": self.ts,
                    }
                )
            return _MappingsResult(first=None)
        raise AssertionError(f"SQL inesperado (compare by id): {s[:400]}")

    def commit(self) -> None:
        return None


def test_compare_with_explicit_ids_uses_where_id_queries():
    ts = datetime(2026, 5, 5, 9, 0, 0, tzinfo=timezone.utc)
    db = _FakeDBCompareExplicitIds(ts)
    out = compare_accounting_approval_snapshots(current_id="snap-cur", previous_id="snap-prev", db=db, _=None)
    assert out["ok"] is True
    assert out["current"]["id"] == "snap-cur"
    assert out["previous"]["id"] == "snap-prev"
    assert any(c.get("field") == "approval.owner" for c in out["diff"]["changed"])
