from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
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
    from app.models import marketplace as _marketplace  # noqa: F401
    from app.models import marketplace_extended as _marketplace_extended  # noqa: F401, F403
    from app.models import webhook as _webhook  # noqa: F401

    Base.metadata.create_all(bind=engine)
