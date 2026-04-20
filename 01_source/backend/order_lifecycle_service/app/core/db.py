# 01_source/backend/order_lifecycle_service/app/core/db.py
# 20/04/2026 - garantir timezone=UTC

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# engine = create_engine(
#     settings.database_url,
#     pool_pre_ping=settings.db_pool_pre_ping,
#     pool_size=settings.db_pool_size,
#     max_overflow=settings.db_max_overflow,
#     future=True,
# )

engine = create_engine(
    settings.database_url,
    pool_pre_ping=settings.db_pool_pre_ping,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    connect_args={"options": "-c timezone=UTC"},
    future=True,
)


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.core.db_migrations import run_startup_migrations

    run_startup_migrations(engine)