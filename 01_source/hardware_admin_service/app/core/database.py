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
    from app.models import assets as _assets  # noqa: F401
    from app.models import cross_domain as _cross_domain  # noqa: F401
    from app.models import finance as _finance  # noqa: F401
    from app.models import hardware_ops as _hardware_ops  # noqa: F401
    from app.models import operators as _operators  # noqa: F401
    from app.models import runtime as _runtime  # noqa: F401
    from app.models import professional_ops as _professional_ops  # noqa: F401
    from app.models import integration as _integration  # noqa: F401
    from app.models import topology as _topology  # noqa: F401
    from app.models import vendor as _vendor  # noqa: F401

    Base.metadata.create_all(bind=engine)
