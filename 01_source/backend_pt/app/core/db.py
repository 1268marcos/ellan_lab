import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = os.getenv(
    "EVENTS_DB_PATH",
    str(Path.home() / "ellan_lab" / "03_data" / "sqlite" / "backend_pt" / "events.db")
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
    Detecta o schema antigo:
      UNIQUE(machine_id, door_id) dentro da tabela allocations.
    Isso costuma aparecer no SQL do sqlite_master.
    """
    cur = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='allocations'"
    )
    row = cur.fetchone()
    if not row or not row[0]:
        return False
    sql = row[0].upper().replace(" ", "")
    return "UNIQUE(MACHINE_ID,DOOR_ID)" in sql


def _migrate_allocations_drop_bad_unique(conn: sqlite3.Connection) -> None:
    """
    Migração idempotente:
    - recria allocations sem UNIQUE(machine_id, door_id)
    - mantém os dados
    - cria índice único parcial para ativos (RESERVED/COMMITTED)
    """
    conn.execute("BEGIN;")
    try:
        # 1) cria tabela nova (sem UNIQUE)
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

        # 2) copia dados antigos
        conn.execute(
            """
            INSERT OR IGNORE INTO allocations_new
            (allocation_id, machine_id, door_id, state, created_at, expires_at, sale_id, request_id)
            SELECT allocation_id, machine_id, door_id, state, created_at, expires_at, sale_id, request_id
            FROM allocations;
            """
        )

        # 3) troca tabela
        conn.execute("DROP TABLE allocations;")
        conn.execute("ALTER TABLE allocations_new RENAME TO allocations;")

        # 4) recria índices “normais”
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

        # 5) índice único parcial (só para alocações ativas)
        # Permite histórico (RELEASED/EXPIRED) sem travar novas reservas.
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

    # Tabela allocations: se não existir, cria já no formato novo (sem UNIQUE ruim)
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

    # Índice único parcial para impedir duas reservas ativas na mesma porta,
    # mas permitir histórico de RELEASED/EXPIRED.
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_alloc_active
        ON allocations(machine_id, door_id)
        WHERE state IN ('RESERVED','COMMITTED');
        """
    )

    conn.commit()

    # Se a tabela foi criada lá atrás com UNIQUE(machine_id, door_id), migra.
    if _table_exists(conn, "allocations") and _allocations_has_bad_unique(conn):
        _migrate_allocations_drop_bad_unique(conn)