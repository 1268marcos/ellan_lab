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
    from app.models import privacy as _privacy  # noqa: F401
    from app.models import privacy_ecosystem as _privacy_ecosystem  # noqa: F401
    from app.models import privacy_extended as _privacy_extended  # noqa: F401
    from app.models import privacy_pro as _privacy_pro  # noqa: F401
    from app.models import privacy_regulatory as _privacy_regulatory  # noqa: F401
    from app.models import privacy_player_legal as _privacy_player_legal  # noqa: F401
    from app.models import critical_table_security as _critical_table_security  # noqa: F401

    Base.metadata.create_all(bind=engine)
    from app.services.critical_table_security_service import seed_registry_and_policies

    db = SessionLocal()
    try:
        seed_registry_and_policies(db)
    except Exception:
        db.rollback()
    finally:
        db.close()
