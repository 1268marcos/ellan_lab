import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator, Optional


class SQLiteService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        folder = os.path.dirname(self.db_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        # Segurança/consistência em SQLite
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def migrate(self) -> None:
        ddl = [
            """
            CREATE TABLE IF NOT EXISTS idempotency_keys (
              id                   TEXT PRIMARY KEY,
              endpoint             TEXT NOT NULL,
              idem_key             TEXT NOT NULL,
              payload_hash         TEXT NOT NULL,

              response_blob        TEXT NOT NULL,
              status               TEXT NOT NULL,

              created_at           INTEGER NOT NULL,
              expires_at           INTEGER NOT NULL
            );
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_idem_endpoint_key
            ON idempotency_keys (endpoint, idem_key);
            """,
            """
            CREATE INDEX IF NOT EXISTS ix_idem_expires
            ON idempotency_keys (expires_at);
            """,
            """
            CREATE TABLE IF NOT EXISTS device_registry (
              device_hash          TEXT PRIMARY KEY,
              version              TEXT NOT NULL,

              first_seen_at        INTEGER NOT NULL,
              last_seen_at         INTEGER NOT NULL,
              seen_count           INTEGER NOT NULL DEFAULT 1,

              flags_json           TEXT NOT NULL DEFAULT '{}'
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS ix_device_last_seen
            ON device_registry (last_seen_at);
            """,
            """
            CREATE TABLE IF NOT EXISTS risk_events (
              id                   TEXT PRIMARY KEY,
              request_id            TEXT NOT NULL,

              event_type            TEXT NOT NULL,
              decision              TEXT NOT NULL,
              score                 INTEGER NOT NULL,
              policy_id             TEXT NOT NULL,

              region                TEXT NOT NULL,
              locker_id             TEXT NOT NULL,
              porta                 INTEGER NOT NULL,

              created_at            INTEGER NOT NULL,

              reasons_json          TEXT NOT NULL,
              signals_json          TEXT NOT NULL,

              audit_event_id        TEXT NOT NULL
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS ix_risk_created_at
            ON risk_events (created_at);
            """,
            """
            CREATE INDEX IF NOT EXISTS ix_risk_region_locker_porta
            ON risk_events (region, locker_id, porta);
            """,
        ]

        with self.session() as conn:
            for stmt in ddl:
                conn.execute(stmt)