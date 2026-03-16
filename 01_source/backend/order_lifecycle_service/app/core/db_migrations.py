from __future__ import annotations

import logging

from sqlalchemy import inspect
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def run_startup_migrations(engine: Engine) -> None:
    """
    Bootstrap inicial do schema do order_lifecycle_service.

    Como este serviço ainda não possui um framework formal de migração,
    garantimos no startup a criação das tabelas mapeadas em app.models.lifecycle.
    """

    from app.models.lifecycle import Base

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    logger.info(
        "order_lifecycle_db_startup_check",
        extra={
            "existing_tables": sorted(existing_tables),
        },
    )

    Base.metadata.create_all(bind=engine)

    inspector_after = inspect(engine)
    final_tables = set(inspector_after.get_table_names())

    logger.info(
        "order_lifecycle_db_startup_ready",
        extra={
            "final_tables": sorted(final_tables),
        },
    )