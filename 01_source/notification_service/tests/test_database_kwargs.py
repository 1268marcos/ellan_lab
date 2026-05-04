from app.core.database import engine_kwargs


def test_disk_sqlite_engine_kwargs():
    k = engine_kwargs("sqlite:////tmp/notification_cov.sqlite3")
    assert "poolclass" not in k


def test_postgres_engine_kwargs():
    assert engine_kwargs("postgresql://u:p@localhost/db") == {"pool_pre_ping": True}
