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


engine = create_engine(get_settings().database_url, **_engine_kwargs(get_settings().database_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import cambio as _cambio  # noqa: F401
    from app.models import catalog as _catalog  # noqa: F401
    from app.models import integration as _integration  # noqa: F401
    from app.models import money as _money  # noqa: F401
    from app.models import advanced as _advanced  # noqa: F401
    from app.models import intelligence as _intelligence  # noqa: F401
    from app.models import professional as _professional  # noqa: F401

    Base.metadata.create_all(bind=engine)
