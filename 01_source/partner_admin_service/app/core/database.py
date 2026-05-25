from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, text
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


def _make_engine():
    url = get_settings().database_url
    return create_engine(url, **_engine_kwargs(url))


engine = _make_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import api_key as _api_key  # noqa: F401
    from app.models import contact as _contact  # noqa: F401
    from app.models import partner as _partner  # noqa: F401
    from app.models import user as _user  # noqa: F401
    from app.models import tenant as _tenant  # noqa: F401
    from app.models import webhook as _webhook  # noqa: F401
    from app.models import partner_domain as _partner_domain  # noqa: F401
    from app.models import partner_extended as _partner_extended  # noqa: F401
    from app.models import partner_ecosystem as _partner_ecosystem  # noqa: F401
    from app.models import partner_ecosystem_professional as _partner_ecosystem_pro  # noqa: F401
    from app.models import partner_capability_webhook as _partner_cap_wh  # noqa: F401
    from app.models import partner_global_ops as _partner_global_ops  # noqa: F401
    from app.models import security as _security  # noqa: F401 — registry, segments, relations, integrations

    Base.metadata.create_all(bind=engine)
    _apply_sqlite_compat_migrations(engine)
    _apply_partner_admin_sql_migrations(engine)


def _sql_file_statements(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    stmts: list[str] = []
    buf: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        buf.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(buf).strip().rstrip(";").strip()
            buf = []
            if stmt:
                stmts.append(stmt)
    tail = "\n".join(buf).strip()
    if tail:
        stmts.append(tail)
    return stmts


def _apply_partner_admin_sql_migrations(eng) -> None:
    mig_dir = Path(__file__).resolve().parents[2] / "migrations"
    if not mig_dir.is_dir():
        return
    security_files = sorted(
        p for p in mig_dir.glob("*.sql") if p.name >= "009_security_domain.sql"
    )
    with eng.begin() as conn:
        for mig in security_files:
            for stmt in _sql_file_statements(mig):
                try:
                    conn.execute(text(stmt))
                except Exception:
                    pass


def _apply_sqlite_compat_migrations(eng) -> None:
    """Colunas/tabelas da migração 005 em SQLite existente (create_all não faz ALTER)."""
    if not str(eng.url).startswith("sqlite"):
        return
    alters = [
        "ALTER TABLE partner_ecosystem_players ADD COLUMN integration_status VARCHAR(16) DEFAULT 'PLANNED'",
        "ALTER TABLE partner_ecosystem_players ADD COLUMN website_url VARCHAR(500)",
        "ALTER TABLE partner_ecosystem_players ADD COLUMN estimated_locker_count INTEGER",
        "ALTER TABLE partner_ecosystem_players ADD COLUMN data_source VARCHAR(32) DEFAULT 'CATALOG'",
        "ALTER TABLE partner_ecosystem_players ADD COLUMN finance_catalog_code VARCHAR(48)",
    ]
    with eng.begin() as conn:
        for stmt in alters:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass
