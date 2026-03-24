# 01_source/backend/order_lifecycle_service/app/core/db_migrations.py
from __future__ import annotations

import logging

from sqlalchemy import inspect
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


REQUIRED_TABLES = {
    "lifecycle_deadlines",
    "domain_events",
    "analytics_facts",
}


def run_startup_migrations(engine: Engine) -> None:
    """
    Bootstrap inicial do schema do order_lifecycle_service.

    Regras:
    - importa explicitamente os models para registrar o metadata
    - executa create_all() no Base canônico
    - valida que as tabelas críticas existem ao final
    - falha no startup se o schema ficar incompleto
    """

    from app.models.base import Base
    from app.models.lifecycle import AnalyticsFact, DomainEvent, LifecycleDeadline  # noqa: F401

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

    missing_tables = sorted(REQUIRED_TABLES - final_tables)

    logger.info(
        "order_lifecycle_db_startup_ready",
        extra={
            "final_tables": sorted(final_tables),
            "missing_tables": missing_tables,
        },
    )

    if missing_tables:
        raise RuntimeError(
            "Schema incompleto no order_lifecycle_service; tabelas ausentes: "
            + ", ".join(missing_tables)
        )