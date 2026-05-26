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
    from app.models import bi_core as _bi_core  # noqa: F401
    from app.models import bi_marts as _bi_marts  # noqa: F401
    from app.models import bi_partners as _bi_partners  # noqa: F401
    from app.models import bi_players as _bi_players  # noqa: F401
    from app.models import bi_webhooks as _bi_webhooks  # noqa: F401
    from app.models import bi_ops as _bi_ops  # noqa: F401
    from app.models import bi_integrations as _bi_integrations  # noqa: F401
    from app.models import bi_efficiency as _bi_efficiency  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_analytics_schema(engine)


def _ensure_analytics_schema(eng) -> None:
    url = str(eng.url)
    if not url.startswith("postgresql"):
        return
    with eng.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS analytics_analytics"))
