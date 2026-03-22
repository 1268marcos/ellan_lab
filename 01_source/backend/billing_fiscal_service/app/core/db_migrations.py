# 01_source/backend/billing_fiscal_service/app/core/db_migrations.py
from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


REQUIRED_TABLES = {
    "invoices",
}


REQUIRED_COLUMNS = {
    "invoices": {
        "id": "VARCHAR(50)",
        "order_id": "VARCHAR(100)",
        "tenant_id": "VARCHAR(100)",
        "country": "VARCHAR(5)",
        "invoice_type": "VARCHAR(20)",
        "invoice_number": "VARCHAR(50)",
        "invoice_series": "VARCHAR(50)",
        "access_key": "VARCHAR(120)",
        "payment_method": "VARCHAR(50)",
        "currency": "VARCHAR(10)",
        "status": "VARCHAR(50)",
        "xml_content": "JSONB",
        "payload_json": "JSONB",
        "tax_details": "JSONB",
        "government_response": "JSONB",
        "error_message": "VARCHAR(1000)",
        "issued_at": "TIMESTAMP WITH TIME ZONE",
        "processing_started_at": "TIMESTAMP WITH TIME ZONE",
        "created_at": "TIMESTAMP WITH TIME ZONE",
        "updated_at": "TIMESTAMP WITH TIME ZONE",
    }
}


def _get_columns_map(inspector, table_name: str) -> dict[str, dict]:
    return {col["name"]: col for col in inspector.get_columns(table_name)}


def _add_column_if_missing(engine: Engine, table_name: str, column_name: str, sql_type: str) -> None:
    inspector = inspect(engine)
    columns = _get_columns_map(inspector, table_name)

    if column_name in columns:
        return

    sql = f'ALTER TABLE {table_name} ADD COLUMN "{column_name}" {sql_type}'
    logger.info(
        "billing_fiscal_add_column",
        extra={
            "table": table_name,
            "column": column_name,
            "sql_type": sql_type,
        },
    )

    with engine.begin() as conn:
        conn.execute(text(sql))


def _ensure_indexes(engine: Engine) -> None:
    index_statements = [
        'CREATE INDEX IF NOT EXISTS ix_invoice_order_id ON invoices (order_id)',
        'CREATE INDEX IF NOT EXISTS ix_invoice_status ON invoices (status)',
        'CREATE INDEX IF NOT EXISTS ix_invoice_country_status ON invoices (country, status)',
        'CREATE INDEX IF NOT EXISTS ix_invoice_created_at ON invoices (created_at)',
    ]

    with engine.begin() as conn:
        for stmt in index_statements:
            conn.execute(text(stmt))


def _ensure_unique_constraint(engine: Engine) -> None:
    """
    Em Postgres, adicionamos índice único para order_id se ainda não existir.
    """
    stmt = """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND indexname = 'uq_invoice_order'
        ) THEN
            CREATE UNIQUE INDEX uq_invoice_order ON invoices (order_id);
        END IF;
    END$$;
    """

    with engine.begin() as conn:
        conn.execute(text(stmt))


def run_startup_migrations(engine: Engine) -> None:
    """
    Estratégia:
    1. create_all() para criação inicial
    2. garantir colunas novas em tabelas já existentes
    3. garantir índices e unique index
    4. validar schema final
    """
    from app.models.base import Base
    from app.models.invoice_model import Invoice  # noqa: F401

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    logger.info(
        "billing_fiscal_db_startup_check",
        extra={"existing_tables": sorted(existing_tables)},
    )

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    final_tables = set(inspector.get_table_names())
    missing_tables = sorted(REQUIRED_TABLES - final_tables)

    if missing_tables:
        raise RuntimeError(
            "Schema incompleto no billing_fiscal_service; tabelas ausentes: "
            + ", ".join(missing_tables)
        )

    for table_name, required_columns in REQUIRED_COLUMNS.items():
        for column_name, sql_type in required_columns.items():
            _add_column_if_missing(engine, table_name, column_name, sql_type)

    _ensure_indexes(engine)
    _ensure_unique_constraint(engine)

    inspector_after = inspect(engine)

    for table_name, required_columns in REQUIRED_COLUMNS.items():
        final_columns = set(_get_columns_map(inspector_after, table_name).keys())
        missing_columns = sorted(set(required_columns.keys()) - final_columns)
        if missing_columns:
            raise RuntimeError(
                f"Schema incompleto em {table_name}; colunas ausentes: "
                + ", ".join(missing_columns)
            )

    logger.info("billing_fiscal_db_startup_ready")
