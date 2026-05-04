from app.core.database import engine_kwargs


def test_disk_sqlite_engine_kwargs():
    k = engine_kwargs("sqlite:////tmp/inventory_cov.sqlite3")
    assert "poolclass" not in k
    assert "connect_args" in k


def test_postgres_engine_kwargs():
    k = engine_kwargs("postgresql://user:pass@localhost/db")
    assert k == {"pool_pre_ping": True}
