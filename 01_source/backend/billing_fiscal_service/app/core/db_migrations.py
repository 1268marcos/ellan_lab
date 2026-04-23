# 01_source/backend/billing_fiscal_service/app/core/db_migrations.py
from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.models.processed_event import ProcessedEvent  # 👈 IMPORTANTE

logger = logging.getLogger(__name__)


REQUIRED_TABLES = {"invoices", "product_fiscal_config", "invoice_delivery_log", "invoice_email_outbox"}

REQUIRED_COLUMNS = {
    "invoices": {
        "id": "VARCHAR(50)",
        "order_id": "VARCHAR(100)",
        "tenant_id": "VARCHAR(100)",
        "region": "VARCHAR(20)",
        "country": "VARCHAR(5)",
        "invoice_type": "VARCHAR(20)",
        "invoice_number": "VARCHAR(50)",
        "invoice_series": "VARCHAR(50)",
        "access_key": "VARCHAR(120)",
        "payment_method": "VARCHAR(50)",
        "currency": "VARCHAR(10)",
        "amount_cents": "BIGINT",
        "status": "invoicestatus",
        "xml_content": "JSONB",
        "payload_json": "JSONB",
        "tax_details": "JSONB",
        "tax_breakdown_json": "JSONB",
        "government_response": "JSONB",
        "order_snapshot": "JSONB",
        "error_message": "VARCHAR(1000)",
        "last_error_code": "VARCHAR(120)",
        "retry_count": "INTEGER DEFAULT 0",
        "next_retry_at": "TIMESTAMP WITH TIME ZONE",
        "last_attempt_at": "TIMESTAMP WITH TIME ZONE",
        "dead_lettered_at": "TIMESTAMP WITH TIME ZONE",
        "processing_started_at": "TIMESTAMP WITH TIME ZONE",
        "locked_by": "VARCHAR(120)",
        "locked_at": "TIMESTAMP WITH TIME ZONE",
        "issued_at": "TIMESTAMP WITH TIME ZONE",
        "created_at": "TIMESTAMP WITH TIME ZONE",
        "updated_at": "TIMESTAMP WITH TIME ZONE",
        # F-1 — NFC-e / locker / emitente / consumidor
        "locker_id": "VARCHAR(64)",
        "totem_id": "VARCHAR(64)",
        "slot_label": "VARCHAR(32)",
        "fiscal_doc_subtype": "VARCHAR(20) NOT NULL DEFAULT 'NFC_E_65'",
        "emission_mode": "VARCHAR(20) NOT NULL DEFAULT 'ONLINE'",
        "emitter_cnpj": "VARCHAR(18)",
        "emitter_name": "VARCHAR(140)",
        "consumer_cpf": "VARCHAR(14)",
        "consumer_name": "VARCHAR(140)",
        "locker_address": "JSONB",
        "items_json": "JSONB",
    }
}


def _get_columns_map(inspector, table_name: str) -> dict[str, dict]:
    return {col["name"]: col for col in inspector.get_columns(table_name)}


def _ensure_invoice_status_enum(engine: Engine) -> None:
    statements = [
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type
                WHERE typname = 'invoicestatus'
            ) THEN
                CREATE TYPE invoicestatus AS ENUM (
                    'PENDING',
                    'PROCESSING',
                    'ISSUED',
                    'FAILED',
                    'DEAD_LETTER',
                    'CANCELLED'
                );
            END IF;
        END$$;
        """,
        "ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'PENDING';",
        "ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'PROCESSING';",
        "ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'ISSUED';",
        "ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'FAILED';",
        "ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'DEAD_LETTER';",
        "ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'CANCELLED';",
        "ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'CANCELLING';",
        "ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'CORRECTION_REQUESTED';",
        "ALTER TYPE invoicestatus ADD VALUE IF NOT EXISTS 'COMPLEMENTARY_ISSUED';",
    ]

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def _add_column_if_missing(engine: Engine, table_name: str, column_name: str, sql_type: str) -> None:
    inspector = inspect(engine)
    columns = _get_columns_map(inspector, table_name)

    if column_name in columns:
        return

    sql = f'ALTER TABLE {table_name} ADD COLUMN "{column_name}" {sql_type}'
    with engine.begin() as conn:
        conn.execute(text(sql))


def _ensure_indexes(engine: Engine) -> None:
    statements = [
        "CREATE INDEX IF NOT EXISTS ix_invoice_order_id ON invoices (order_id)",
        "CREATE INDEX IF NOT EXISTS ix_invoice_status ON invoices (status)",
        "CREATE INDEX IF NOT EXISTS ix_invoice_country_status ON invoices (country, status)",
        "CREATE INDEX IF NOT EXISTS ix_invoice_created_at ON invoices (created_at)",
        "CREATE INDEX IF NOT EXISTS ix_invoice_next_retry_at ON invoices (next_retry_at)",
        "CREATE INDEX IF NOT EXISTS ix_invoice_locker_id ON invoices (locker_id)",
        "CREATE INDEX IF NOT EXISTS ix_invoice_fiscal_doc_subtype ON invoices (fiscal_doc_subtype)",
    ]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def _ensure_invoice_email_outbox(engine: Engine) -> None:
    """F-3: fila de e-mail fiscal (SMTP worker)."""
    stmt = """
    CREATE TABLE IF NOT EXISTS invoice_email_outbox (
        id VARCHAR(50) NOT NULL PRIMARY KEY,
        invoice_id VARCHAR(50) NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
        template VARCHAR(32) NOT NULL,
        to_email VARCHAR(255) NOT NULL,
        subject VARCHAR(500) NOT NULL,
        body_text TEXT NOT NULL,
        detail_json JSONB,
        status VARCHAR(24) NOT NULL DEFAULT 'PENDING',
        retry_count INTEGER NOT NULL DEFAULT 0,
        next_retry_at TIMESTAMPTZ,
        last_error VARCHAR(2000),
        locked_by VARCHAR(120),
        locked_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        sent_at TIMESTAMPTZ
    );
    CREATE INDEX IF NOT EXISTS ix_invoice_email_outbox_status
        ON invoice_email_outbox (status, next_retry_at);
    CREATE INDEX IF NOT EXISTS ix_invoice_email_outbox_invoice
        ON invoice_email_outbox (invoice_id);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_invoice_delivery_log(engine: Engine) -> None:
    """I-2: auditoria de entrega (e-mail DANFE, etc.)."""
    stmt = """
    CREATE TABLE IF NOT EXISTS invoice_delivery_log (
        id VARCHAR(50) NOT NULL PRIMARY KEY,
        invoice_id VARCHAR(50) NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
        channel VARCHAR(32) NOT NULL,
        status VARCHAR(32) NOT NULL,
        detail JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS ix_invoice_delivery_log_invoice
        ON invoice_delivery_log (invoice_id);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_invoice_order_view(engine: Engine) -> None:
    """
    I-1: visão de reconciliação no Postgres do billing (sem join cross-DB a orders).
    Une invoice + order_snapshot + items_json em colunas consultáveis.
    """
    stmt = """
    CREATE OR REPLACE VIEW invoice_order_view AS
    SELECT
        i.id AS invoice_id,
        i.order_id,
        i.tenant_id,
        i.region,
        i.country,
        i.status::text AS invoice_status,
        i.locker_id,
        i.totem_id,
        i.slot_label,
        i.amount_cents,
        i.currency,
        i.created_at,
        i.issued_at,
        i.items_json,
        i.order_snapshot,
        (i.order_snapshot->'order') AS order_json,
        (i.order_snapshot->'order_items') AS order_items_snapshot,
        COALESCE(i.items_json->'lines', '[]'::jsonb) AS items_lines
    FROM invoices i;
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_unique_constraint(engine: Engine) -> None:
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
    from app.models.base import Base
    from app.models.invoice_delivery_log import InvoiceDeliveryLog  # noqa: F401
    from app.models.invoice_email_outbox import InvoiceEmailOutbox  # noqa: F401
    from app.models.invoice_model import Invoice  # noqa: F401
    from app.models.product_fiscal_config import ProductFiscalConfig  # noqa: F401

    _ensure_invoice_status_enum(engine)

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
    _ensure_invoice_delivery_log(engine)
    _ensure_invoice_email_outbox(engine)
    _ensure_invoice_order_view(engine)

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