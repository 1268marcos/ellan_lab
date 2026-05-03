from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import psycopg2
import psycopg2.extras

from app.config import settings


def _pg_dsn(url: str) -> str:
    """Converte sqlalchemy-style postgresql:// em DSN para psycopg2."""
    if url.startswith("postgresql+asyncpg://"):
        url = "postgresql://" + url.split("postgresql+asyncpg://", 1)[1]
    if url.startswith("postgres://"):
        url = "postgresql://" + url[11:]
    return url


@contextmanager
def get_conn() -> Iterator[psycopg2.extensions.connection]:
    conn = psycopg2.connect(_pg_dsn(settings.database_url))
    try:
        yield conn
    finally:
        conn.close()


def fetch_all(sql: str, params: tuple | None = None) -> list[dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return [dict(r) for r in cur.fetchall()]


def fetch_one(sql: str, params: tuple | None = None) -> dict[str, Any] | None:
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: tuple | None = None) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
        conn.commit()


def execute_returning(sql: str, params: tuple | None = None) -> dict[str, Any] | None:
    """INSERT/UPDATE … RETURNING em uma transação."""
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params or ())
            row = cur.fetchone()
        conn.commit()
        return dict(row) if row else None


def refresh_materialized_view_concurrent() -> None:
    conn = psycopg2.connect(_pg_dsn(settings.database_url))
    conn.set_session(autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY ml_features_daily_mv")
    finally:
        conn.close()
