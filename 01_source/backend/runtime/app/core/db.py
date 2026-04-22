# 01_source/backend/runtime/app/core/db.py
import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = os.getenv(
    "EVENTS_DB_PATH",
    str(Path.home() / "ellan_lab" / "03_data" / "sqlite" / "runtime" / "events.db"),
    # "backend_sp"
)

_conn = None


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        Path(DEFAULT_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(DEFAULT_DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL;")
        _conn.execute("PRAGMA synchronous=NORMAL;")
    return _conn


# =========================================================
# Helpers de inspeção de schema
# =========================================================

def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    )
    return cur.fetchone() is not None


def _index_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
        (name,),
    )
    return cur.fetchone() is not None


def _allocations_has_bad_unique(conn: sqlite3.Connection) -> bool:
    """
    Detecta schema antigo com:
      UNIQUE(machine_id, door_id)
    diretamente na tabela allocations.
    """
    cur = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='allocations'"
    )
    row = cur.fetchone()
    if not row or not row["sql"]:
        return False

    sql = row["sql"].upper().replace(" ", "")
    return "UNIQUE(MACHINE_ID,DOOR_ID)" in sql


# =========================================================
# Migrations
# =========================================================

def _migrate_allocations_drop_bad_unique(conn: sqlite3.Connection) -> None:
    """
    Migração idempotente:
    - recria allocations sem UNIQUE(machine_id, door_id)
    - preserva dados
    - cria índice único parcial só para estados ativos
    """
    conn.execute("BEGIN;")
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS allocations_new (
                allocation_id TEXT PRIMARY KEY,
                machine_id TEXT NOT NULL,
                door_id INTEGER NOT NULL,
                state TEXT NOT NULL, -- RESERVED | COMMITTED | RELEASED | EXPIRED
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                sale_id TEXT,
                request_id TEXT
            );
            """
        )

        conn.execute(
            """
            INSERT OR IGNORE INTO allocations_new
            (allocation_id, machine_id, door_id, state, created_at, expires_at, sale_id, request_id)
            SELECT allocation_id, machine_id, door_id, state, created_at, expires_at, sale_id, request_id
            FROM allocations;
            """
        )

        conn.execute("DROP TABLE allocations;")
        conn.execute("ALTER TABLE allocations_new RENAME TO allocations;")

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_allocations_machine_state
            ON allocations(machine_id, state, expires_at);
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_allocations_machine_door
            ON allocations(machine_id, door_id);
            """
        )

        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS ux_alloc_active
            ON allocations(machine_id, door_id)
            WHERE state IN ('RESERVED','COMMITTED');
            """
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise


# =========================================================
# Criação de tabelas
# =========================================================

def _create_events_table(conn: sqlite3.Connection) -> None:
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


def _create_door_state_table(conn: sqlite3.Connection) -> None:
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


def _create_allocations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS allocations (
            allocation_id TEXT PRIMARY KEY,
            machine_id TEXT NOT NULL,
            door_id INTEGER NOT NULL,
            state TEXT NOT NULL, -- RESERVED | COMMITTED | RELEASED | EXPIRED
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            sale_id TEXT,
            request_id TEXT
        );
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_allocations_machine_state
        ON allocations(machine_id, state, expires_at);
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_allocations_machine_door
        ON allocations(machine_id, door_id);
        """
    )

    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_alloc_active
        ON allocations(machine_id, door_id)
        WHERE state IN ('RESERVED','COMMITTED');
        """
    )


def _create_pending_sync_operations_table(conn: sqlite3.Connection) -> None:
    """
    Preparação para futuro modo degradado / sincronização.
    Ainda não muda seu fluxo atual.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pending_sync_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_type TEXT NOT NULL,
            aggregate_id TEXT,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            synced INTEGER NOT NULL DEFAULT 0
        );
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pending_sync_unsynced
        ON pending_sync_operations(synced, created_at);
        """
    )


def _create_catalog_slot_overrides_table(conn: sqlite3.Connection) -> None:
    """
    Mapeamento operacional editável de slot -> sku por locker.
    Usado pela interface de alocação de produtos em ambiente operacional.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS catalog_slot_overrides (
            machine_id TEXT NOT NULL,
            door_id INTEGER NOT NULL,
            sku_id TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (machine_id, door_id)
        );
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_catalog_slot_overrides_machine
        ON catalog_slot_overrides(machine_id, door_id);
        """
    )


# =========================================================
# Migração - Verificação de índice antigo
# =========================================================

def _has_bad_unique_index_on_allocations(conn: sqlite3.Connection) -> bool:
    cur = conn.execute(
        """
        SELECT name, sql
        FROM sqlite_master
        WHERE type='index' AND tbl_name='allocations'
        """
    )
    rows = cur.fetchall()
    for row in rows:
        sql = (row["sql"] or "").upper().replace(" ", "")
        if not sql:
            continue
        if "UNIQUEINDEX" in sql and "ONALLOCATIONS(MACHINE_ID,DOOR_ID)" in sql and "WHERESTATEIN('RESERVED','COMMITTED')" not in sql:
            return True
    return False


# =========================================================
# Init principal
# =========================================================

def init_db() -> None:
    conn = get_conn()

    _create_events_table(conn)
    _create_door_state_table(conn)
    _create_allocations_table(conn)
    _create_pending_sync_operations_table(conn)
    _create_catalog_slot_overrides_table(conn)

    conn.commit()

    if _table_exists(conn, "allocations") and (
        _allocations_has_bad_unique(conn) or _has_bad_unique_index_on_allocations(conn)
    ):
        _migrate_allocations_drop_bad_unique(conn)