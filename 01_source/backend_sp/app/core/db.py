import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = os.getenv(
    "EVENTS_DB_PATH",
    str(Path.home() / "ellan_lab" / "03_data" / "sqlite" / "backend_sp" / "events.db")
)

_conn = None


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        Path(DEFAULT_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(DEFAULT_DB_PATH, check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL;")
        _conn.execute("PRAGMA synchronous=NORMAL;")
    return _conn


def init_db() -> None:
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            machine_id TEXT NOT NULL,
            door_id INTEGER,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            correlation_id TEXT NOT NULL,
            sale_id TEXT,
            command_id TEXT,
            old_state TEXT,
            new_state TEXT,
            payload_json TEXT NOT NULL,
            prev_hash TEXT,
            hash TEXT NOT NULL
        );
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_ts
        ON events(ts);
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_machine
        ON events(machine_id, ts);
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_door
        ON events(machine_id, door_id, ts);
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS door_state (
            machine_id TEXT NOT NULL,
            door_id INTEGER NOT NULL,
            state TEXT NOT NULL,
            product_id TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (machine_id, door_id)
        );
        """
    )

    conn.commit()
