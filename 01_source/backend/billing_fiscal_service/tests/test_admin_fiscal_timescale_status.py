from __future__ import annotations

from app.api import routes_admin_fiscal as raf


class _FakeMappingsResult:
    def __init__(self, rows: list[dict]):
        self._rows = rows

    def mappings(self):
        return self

    def first(self):
        return self._rows[0] if self._rows else None

    def all(self):
        return self._rows


class _FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one(self):
        return self._value


class _FakeDB:
    def execute(self, statement, params=None):
        sql = str(statement)
        if "FROM pg_extension" in sql:
            return _FakeMappingsResult([{"extname": "timescaledb", "extversion": "2.26.3"}])
        if "timescaledb_information.hypertables" in sql:
            return _FakeMappingsResult(
                [
                    {"hypertable_schema": "public", "hypertable_name": "ellanlab_monthly_pnl"},
                    {"hypertable_schema": "public", "hypertable_name": "ellanlab_revenue_recognition"},
                    {"hypertable_schema": "public", "hypertable_name": "financial_kpi_daily"},
                ]
            )
        if "timescaledb_information.jobs" in sql:
            return _FakeMappingsResult(
                [
                    {"hypertable_name": "ellanlab_monthly_pnl", "proc_name": "policy_compression", "schedule_interval": "12:00:00"},
                    {"hypertable_name": "ellanlab_monthly_pnl", "proc_name": "policy_retention", "schedule_interval": "1 day"},
                    {"hypertable_name": "ellanlab_revenue_recognition", "proc_name": "policy_compression", "schedule_interval": "12:00:00"},
                    {"hypertable_name": "ellanlab_revenue_recognition", "proc_name": "policy_retention", "schedule_interval": "1 day"},
                    {"hypertable_name": "financial_kpi_daily", "proc_name": "policy_compression", "schedule_interval": "12:00:00"},
                    {"hypertable_name": "financial_kpi_daily", "proc_name": "policy_retention", "schedule_interval": "1 day"},
                ]
            )
        if "FROM pg_indexes" in sql:
            return _FakeScalarResult(2)
        raise AssertionError(f"SQL inesperado no fake DB: {sql}")


def test_timescale_status_returns_smoke_ok_when_expected_objects_exist():
    db = _FakeDB()
    out = raf.get_timescale_status(db=db, _=None)
    assert out["ext_ok"] is True
    assert out["hypertable_count"] == 3
    assert out["policy_count"] == 6
    assert out["dedupe_index_count"] == 2
    assert out["smoke_result"] == "SMOKE_OK"
