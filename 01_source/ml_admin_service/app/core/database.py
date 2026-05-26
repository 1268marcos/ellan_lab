from __future__ import annotations

from collections.abc import Generator

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


engine = create_engine(get_settings().database_url, **_engine_kwargs(get_settings().database_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import ml_core as _ml_core  # noqa: F401
    from app.models import ml_ops as _ml_ops  # noqa: F401
    from app.models import ml_ecosystem as _ml_ecosystem  # noqa: F401
    from app.models import ml_alerts_webhooks as _ml_alerts_webhooks  # noqa: F401
    from app.models import ml_readiness as _ml_readiness  # noqa: F401
    from app.models import ml_network as _ml_network  # noqa: F401
    from app.models import partner as _partner  # noqa: F401
    from app.models import ml_efficiency as _ml_efficiency  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _apply_sqlite_compat_migrations(engine)


def _apply_sqlite_compat_migrations(eng) -> None:
    if not str(eng.url).startswith("sqlite"):
        return
    alters = [
        "ALTER TABLE ml_locker_network_players ADD COLUMN finance_catalog_code VARCHAR(48)",
    ]
    with eng.begin() as conn:
        for stmt in alters:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass
