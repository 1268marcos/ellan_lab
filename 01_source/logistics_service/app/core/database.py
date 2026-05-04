from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        k: dict = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in url:
            from sqlalchemy.pool import StaticPool

            k["poolclass"] = StaticPool
        return k
    return {"pool_pre_ping": True}


engine = create_engine(get_settings().database_url, **engine_kwargs(get_settings().database_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.models import delivery as _d  # noqa: F401
    from app.models import manifest as _m  # noqa: F401

    Base.metadata.create_all(bind=engine)
