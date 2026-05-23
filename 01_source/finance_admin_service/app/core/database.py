from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        kwargs: dict = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in url:
            from sqlalchemy.pool import StaticPool

            kwargs["poolclass"] = StaticPool
        return kwargs
    return {"pool_pre_ping": True}


engine = create_engine(get_settings().database_url, **_engine_kwargs(get_settings().database_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_b2b_fiscal_columns() -> None:
    url = get_settings().database_url
    if not url.startswith("sqlite") or ":memory:" in url:
        return
    if "partner_b2b_invoices" not in inspect(engine).get_table_names():
        return
    existing = {c["name"] for c in inspect(engine).get_columns("partner_b2b_invoices")}
    alters = [
        ("fiscal_status", "VARCHAR(20) DEFAULT 'PENDING'"),
        ("fiscal_access_key", "VARCHAR(80)"),
        ("fiscal_pdf_url", "VARCHAR(500)"),
    ]
    with engine.begin() as conn:
        for col, ddl in alters:
            if col not in existing:
                conn.execute(text(f"ALTER TABLE partner_b2b_invoices ADD COLUMN {col} {ddl}"))


def _migrate_catalog_columns() -> None:
    """SQLite legado: colunas do ecossistema (004) sem recriar o ficheiro."""
    url = get_settings().database_url
    if not url.startswith("sqlite") or ":memory:" in url:
        return
    if "finance_locker_network_catalog" not in inspect(engine).get_table_names():
        return
    existing = {c["name"] for c in inspect(engine).get_columns("finance_locker_network_catalog")}
    alters: list[tuple[str, str]] = [
        ("segment_code", "VARCHAR(40)"),
        ("supports_collection_points", "BOOLEAN NOT NULL DEFAULT 0"),
        ("supports_food_delivery", "BOOLEAN NOT NULL DEFAULT 0"),
        ("integration_modes_json", "TEXT NOT NULL DEFAULT '[]'"),
    ]
    with engine.begin() as conn:
        for col, ddl in alters:
            if col not in existing:
                conn.execute(text(f"ALTER TABLE finance_locker_network_catalog ADD COLUMN {col} {ddl}"))


def init_db() -> None:
    from app.models import finance as _finance  # noqa: F401
    from app.models import finance_catalog as _finance_catalog  # noqa: F401
    from app.models import finance_ecosystem as _finance_ecosystem  # noqa: F401
    from app.models import finance_extended as _finance_extended  # noqa: F401
    from app.models import finance_professional as _finance_professional  # noqa: F401
    from app.models import finance_advanced as _finance_advanced  # noqa: F401
    from app.models import finance_revenue as _finance_revenue  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_b2b_fiscal_columns()
    _migrate_catalog_columns()
