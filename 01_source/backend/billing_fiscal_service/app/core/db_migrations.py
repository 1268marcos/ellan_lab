# 01_source/backend/billing_fiscal_service/app/core/db_migrations.py
from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.models.processed_event import ProcessedEvent  # 👈 IMPORTANTE

logger = logging.getLogger(__name__)


REQUIRED_TABLES = {
    "invoices",
    "product_fiscal_config",
    "invoice_delivery_log",
    "invoice_email_outbox",
    "fiscal_reconciliation_gaps",
    "fiscal_provider_health_status",
    "fiscal_authority_callbacks",
}

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


def _ensure_fiscal_reconciliation_gaps(engine: Engine) -> None:
    stmt = """
    CREATE TABLE IF NOT EXISTS fiscal_reconciliation_gaps (
        id VARCHAR(60) NOT NULL PRIMARY KEY,
        dedupe_key VARCHAR(180) NOT NULL UNIQUE,
        gap_type VARCHAR(80) NOT NULL,
        severity VARCHAR(20) NOT NULL DEFAULT 'WARN',
        status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
        order_id VARCHAR(100),
        invoice_id VARCHAR(50),
        details_json JSONB,
        first_detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        last_detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        resolved_at TIMESTAMPTZ
    );
    CREATE INDEX IF NOT EXISTS ix_fiscal_gap_status_last
        ON fiscal_reconciliation_gaps (status, last_detected_at);
    CREATE INDEX IF NOT EXISTS ix_fiscal_gap_order
        ON fiscal_reconciliation_gaps (order_id);
    CREATE INDEX IF NOT EXISTS ix_fiscal_gap_invoice
        ON fiscal_reconciliation_gaps (invoice_id);
    CREATE INDEX IF NOT EXISTS ix_fiscal_gap_type
        ON fiscal_reconciliation_gaps (gap_type);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_fiscal_provider_health_status(engine: Engine) -> None:
    stmt = """
    CREATE TABLE IF NOT EXISTS fiscal_provider_health_status (
        country VARCHAR(5) NOT NULL PRIMARY KEY,
        provider_name VARCHAR(80) NOT NULL,
        mode VARCHAR(20) NOT NULL DEFAULT 'stub',
        enabled BOOLEAN NOT NULL DEFAULT FALSE,
        base_url VARCHAR(300),
        last_status VARCHAR(20) NOT NULL DEFAULT 'UNKNOWN',
        last_http_status INTEGER,
        last_latency_ms INTEGER,
        last_error VARCHAR(1000),
        checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS ix_fiscal_provider_health_country
        ON fiscal_provider_health_status (country);
    CREATE INDEX IF NOT EXISTS ix_fiscal_provider_health_checked_at
        ON fiscal_provider_health_status (checked_at);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_fiscal_authority_callbacks(engine: Engine) -> None:
    stmt = """
    CREATE TABLE IF NOT EXISTS fiscal_authority_callbacks (
        id VARCHAR(60) NOT NULL PRIMARY KEY,
        invoice_id VARCHAR(50) NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
        authority VARCHAR(30) NOT NULL,
        event_type VARCHAR(80),
        status VARCHAR(40),
        protocol_number VARCHAR(120),
        raw_payload JSONB,
        received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS ix_fiscal_cb_invoice
        ON fiscal_authority_callbacks (invoice_id);
    CREATE INDEX IF NOT EXISTS ix_fiscal_cb_authority
        ON fiscal_authority_callbacks (authority);
    CREATE INDEX IF NOT EXISTS ix_fiscal_cb_received_at
        ON fiscal_authority_callbacks (received_at);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_partner_payment_holds(engine: Engine) -> None:
    """FA-0: retenção parcial de recebíveis B2B para proteção de disputas."""
    stmt = """
    CREATE TABLE IF NOT EXISTS partner_payment_holds (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        partner_id VARCHAR(36) NOT NULL,
        invoice_id VARCHAR(36) NOT NULL,
        hold_amount_cents BIGINT NOT NULL,
        release_schedule VARCHAR(30) NOT NULL DEFAULT 'AFTER_15_DAYS',
        released_at TIMESTAMPTZ,
        released_amount_cents BIGINT,
        dispute_opened_at TIMESTAMPTZ,
        dispute_resolved_at TIMESTAMPTZ,
        dispute_result VARCHAR(20),
        status VARCHAR(20) NOT NULL DEFAULT 'HELD',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT ck_pph_release_schedule CHECK (
            release_schedule IN ('AFTER_15_DAYS', 'AFTER_30_DAYS', 'UPON_DISPUTE_RESOLUTION')
        ),
        CONSTRAINT ck_pph_status CHECK (
            status IN ('HELD', 'RELEASED', 'DISPUTED', 'CANCELLED')
        ),
        CONSTRAINT ck_pph_dispute_result CHECK (
            dispute_result IS NULL OR dispute_result IN ('IN_FAVOR_ELLAN', 'IN_FAVOR_PARTNER')
        )
    );
    CREATE INDEX IF NOT EXISTS ix_partner_payment_holds_partner_status
        ON partner_payment_holds (partner_id, status);
    CREATE INDEX IF NOT EXISTS ix_partner_payment_holds_invoice
        ON partner_payment_holds (invoice_id);
    CREATE INDEX IF NOT EXISTS ix_partner_payment_holds_created_at
        ON partner_payment_holds (created_at);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_locker_slot_hourly_occupancy(engine: Engine) -> None:
    """FA-0: ocupação horária do slot para billing por uso com granularidade fina."""
    stmt = """
    CREATE TABLE IF NOT EXISTS locker_slot_hourly_occupancy (
        id BIGSERIAL PRIMARY KEY,
        locker_id VARCHAR(36) NOT NULL,
        slot_number INTEGER NOT NULL,
        hour_bucket TIMESTAMPTZ NOT NULL,
        is_occupied BOOLEAN NOT NULL,
        delivery_id VARCHAR(36),
        occupied_duration_minutes INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT ck_lsho_occupied_duration CHECK (
            occupied_duration_minutes >= 0 AND occupied_duration_minutes <= 60
        ),
        CONSTRAINT uq_lsho_locker_slot_hour UNIQUE (locker_id, slot_number, hour_bucket)
    );
    CREATE INDEX IF NOT EXISTS ix_lsho_locker_hour
        ON locker_slot_hourly_occupancy (locker_id, hour_bucket);
    CREATE INDEX IF NOT EXISTS ix_lsho_delivery_hour
        ON locker_slot_hourly_occupancy (delivery_id, hour_bucket);
    CREATE INDEX IF NOT EXISTS ix_lsho_hour_bucket
        ON locker_slot_hourly_occupancy (hour_bucket);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_journal_entries_foundation(engine: Engine) -> None:
    """
    FA-0: preparação de dedupe contábil.
    Garante `journal_entries` com `reference_source` e `dedupe_key` único.
    """
    create_stmt = """
    CREATE TABLE IF NOT EXISTS journal_entries (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        entry_date DATE NOT NULL,
        description VARCHAR(255) NOT NULL,
        reference_type VARCHAR(50),
        reference_id VARCHAR(36),
        reference_source VARCHAR(50) NOT NULL DEFAULT 'manual',
        dedupe_key VARCHAR(128),
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        is_posted BOOLEAN NOT NULL DEFAULT FALSE,
        posted_at TIMESTAMPTZ,
        posted_by VARCHAR(36),
        created_by VARCHAR(36),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """
    with engine.begin() as conn:
        conn.execute(text(create_stmt))

    # Auto-heal para ambientes em que a tabela já exista sem os campos de dedupe.
    _add_column_if_missing(engine, "journal_entries", "reference_source", "VARCHAR(50) NOT NULL DEFAULT 'manual'")
    _add_column_if_missing(engine, "journal_entries", "dedupe_key", "VARCHAR(128)")

    index_stmt = """
    CREATE UNIQUE INDEX IF NOT EXISTS ux_journal_entries_dedupe_key
        ON journal_entries (dedupe_key)
        WHERE dedupe_key IS NOT NULL;
    CREATE INDEX IF NOT EXISTS ix_journal_entries_reference
        ON journal_entries (reference_source, reference_type, reference_id);
    """
    with engine.begin() as conn:
        conn.execute(text(index_stmt))


def _ensure_partner_billing_plans(engine: Engine) -> None:
    """
    FA-1: catálogo de planos de billing B2B (global-first, multi-país/jurisdição).
    """
    stmt = """
    CREATE TABLE IF NOT EXISTS partner_billing_plans (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        partner_id VARCHAR(36) NOT NULL,
        partner_type VARCHAR(20) NOT NULL,
        plan_name VARCHAR(128) NOT NULL,
        billing_model VARCHAR(30) NOT NULL,
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        country_code VARCHAR(2),
        jurisdiction_code VARCHAR(32),
        timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
        monthly_fee_cents BIGINT,
        fee_per_delivery_cents BIGINT,
        fee_per_pickup_cents BIGINT,
        fee_per_day_stored_cents BIGINT,
        free_storage_hours INTEGER NOT NULL DEFAULT 72,
        revenue_share_pct NUMERIC(6,4),
        min_monthly_fee_cents BIGINT,
        included_deliveries_month INTEGER,
        overage_fee_cents BIGINT,
        valid_from DATE NOT NULL,
        valid_until DATE,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT ck_pbp_partner_type CHECK (
            partner_type IN ('ECOMMERCE','LOGISTICS','LOCAL_MERCHANT','CARRIER','ENTERPRISE')
        ),
        CONSTRAINT ck_pbp_billing_model CHECK (
            billing_model IN ('FLAT_MONTHLY','PER_USE','HYBRID','REVENUE_SHARE','FREE_TIER')
        ),
        CONSTRAINT ck_pbp_revenue_share_pct CHECK (
            revenue_share_pct IS NULL OR (revenue_share_pct >= 0 AND revenue_share_pct <= 1)
        ),
        CONSTRAINT ck_pbp_country_code CHECK (
            country_code IS NULL OR LENGTH(country_code) = 2
        )
    );
    CREATE INDEX IF NOT EXISTS ix_pbp_partner_active
        ON partner_billing_plans (partner_id, is_active);
    CREATE INDEX IF NOT EXISTS ix_pbp_country_jurisdiction
        ON partner_billing_plans (country_code, jurisdiction_code);
    CREATE INDEX IF NOT EXISTS ix_pbp_validity
        ON partner_billing_plans (valid_from, valid_until);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_partner_billing_cycles(engine: Engine) -> None:
    """
    FA-1: ciclo de billing por parceiro (global-first, suporte por locker ou contrato global).
    """
    stmt = """
    CREATE TABLE IF NOT EXISTS partner_billing_cycles (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        partner_id VARCHAR(36) NOT NULL,
        locker_id VARCHAR(36),
        partner_type VARCHAR(20) NOT NULL,
        billing_plan_id VARCHAR(36) NOT NULL REFERENCES partner_billing_plans(id),
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        country_code VARCHAR(2),
        jurisdiction_code VARCHAR(32),
        period_timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
        period_start DATE NOT NULL,
        period_end DATE NOT NULL,
        total_deliveries INTEGER NOT NULL DEFAULT 0,
        total_pickups INTEGER NOT NULL DEFAULT 0,
        total_slot_days NUMERIC(10,2) NOT NULL DEFAULT 0,
        total_overdue_days NUMERIC(10,2) NOT NULL DEFAULT 0,
        base_fee_cents BIGINT NOT NULL DEFAULT 0,
        usage_fee_cents BIGINT NOT NULL DEFAULT 0,
        overage_fee_cents BIGINT NOT NULL DEFAULT 0,
        sla_penalty_cents BIGINT NOT NULL DEFAULT 0,
        discount_cents BIGINT NOT NULL DEFAULT 0,
        tax_cents BIGINT NOT NULL DEFAULT 0,
        total_amount_cents BIGINT NOT NULL DEFAULT 0,
        status VARCHAR(20) NOT NULL DEFAULT 'OPEN',
        dedupe_key VARCHAR(160),
        computed_at TIMESTAMPTZ,
        approved_at TIMESTAMPTZ,
        approved_by VARCHAR(36),
        invoiced_at TIMESTAMPTZ,
        paid_at TIMESTAMPTZ,
        payment_ref VARCHAR(128),
        dispute_reason TEXT,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT ck_pbc_status CHECK (
            status IN ('OPEN','COMPUTING','REVIEW','APPROVED','INVOICED','PAID','DISPUTED','CANCELLED')
        ),
        CONSTRAINT ck_pbc_country_code CHECK (
            country_code IS NULL OR LENGTH(country_code) = 2
        )
    );
    CREATE INDEX IF NOT EXISTS ix_pbc_partner_period
        ON partner_billing_cycles (partner_id, period_start, period_end);
    CREATE INDEX IF NOT EXISTS ix_pbc_status
        ON partner_billing_cycles (status);
    CREATE INDEX IF NOT EXISTS ix_pbc_country_jurisdiction
        ON partner_billing_cycles (country_code, jurisdiction_code);
    CREATE UNIQUE INDEX IF NOT EXISTS ux_pbc_partner_locker_period
        ON partner_billing_cycles (partner_id, locker_id, period_start, period_end)
        WHERE locker_id IS NOT NULL;
    CREATE UNIQUE INDEX IF NOT EXISTS ux_pbc_partner_global_period
        ON partner_billing_cycles (partner_id, period_start, period_end)
        WHERE locker_id IS NULL;
    CREATE UNIQUE INDEX IF NOT EXISTS ux_pbc_dedupe_key
        ON partner_billing_cycles (dedupe_key)
        WHERE dedupe_key IS NOT NULL;
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_partner_billing_line_items(engine: Engine) -> None:
    """
    FA-1: detalhamento auditável do billing por ciclo (global-first).
    """
    stmt = """
    CREATE TABLE IF NOT EXISTS partner_billing_line_items (
        id BIGSERIAL PRIMARY KEY,
        cycle_id VARCHAR(36) NOT NULL REFERENCES partner_billing_cycles(id) ON DELETE CASCADE,
        partner_id VARCHAR(36) NOT NULL,
        locker_id VARCHAR(36),
        line_type VARCHAR(40) NOT NULL,
        description VARCHAR(255) NOT NULL,
        reference_id VARCHAR(36),
        reference_type VARCHAR(40),
        reference_source VARCHAR(50) NOT NULL DEFAULT 'billing_engine',
        dedupe_key VARCHAR(180),
        quantity NUMERIC(12,4) NOT NULL DEFAULT 1,
        unit_price_cents BIGINT NOT NULL,
        total_cents BIGINT NOT NULL,
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        country_code VARCHAR(2),
        jurisdiction_code VARCHAR(32),
        tax_code VARCHAR(32),
        tax_rate_pct NUMERIC(8,4),
        period_from TIMESTAMPTZ,
        period_to TIMESTAMPTZ,
        metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT ck_pbli_line_type CHECK (
            line_type IN (
                'BASE_FEE','DELIVERY_FEE','PICKUP_FEE','STORAGE_DAY_FEE','OVERAGE_FEE',
                'SLA_PENALTY','TAX','DISCOUNT','CREDIT_NOTE','ADJUSTMENT'
            )
        ),
        CONSTRAINT ck_pbli_country_code CHECK (
            country_code IS NULL OR LENGTH(country_code) = 2
        )
    );
    CREATE INDEX IF NOT EXISTS ix_pbli_cycle
        ON partner_billing_line_items (cycle_id);
    CREATE INDEX IF NOT EXISTS ix_pbli_reference
        ON partner_billing_line_items (reference_source, reference_type, reference_id);
    CREATE UNIQUE INDEX IF NOT EXISTS ux_pbli_dedupe_key
        ON partner_billing_line_items (dedupe_key)
        WHERE dedupe_key IS NOT NULL;
    CREATE INDEX IF NOT EXISTS ix_pbli_country_jurisdiction
        ON partner_billing_line_items (country_code, jurisdiction_code);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_partner_b2b_invoices(engine: Engine) -> None:
    """
    FA-1: faturas B2B globais emitidas para parceiros.
    """
    stmt = """
    CREATE TABLE IF NOT EXISTS partner_b2b_invoices (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        cycle_id VARCHAR(36) NOT NULL REFERENCES partner_billing_cycles(id),
        partner_id VARCHAR(36) NOT NULL,
        invoice_number VARCHAR(50),
        invoice_series VARCHAR(20),
        access_key VARCHAR(140),
        document_type VARCHAR(30) NOT NULL DEFAULT 'INVOICE',
        amount_cents BIGINT NOT NULL,
        tax_cents BIGINT NOT NULL DEFAULT 0,
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        country_code VARCHAR(2),
        jurisdiction_code VARCHAR(32),
        timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
        due_date DATE,
        payment_method VARCHAR(30),
        emitter_tax_id VARCHAR(32),
        emitter_name VARCHAR(140),
        taker_tax_id VARCHAR(32),
        taker_name VARCHAR(140),
        taker_email VARCHAR(128),
        status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
        dedupe_key VARCHAR(180),
        external_provider_ref VARCHAR(140),
        issued_at TIMESTAMPTZ,
        sent_at TIMESTAMPTZ,
        viewed_at TIMESTAMPTZ,
        paid_at TIMESTAMPTZ,
        cancelled_at TIMESTAMPTZ,
        cancel_reason TEXT,
        pdf_url VARCHAR(500),
        xml_content JSONB,
        government_response JSONB,
        metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT ck_pbi_status CHECK (
            status IN ('DRAFT','ISSUED','SENT','VIEWED','PAID','OVERDUE','DISPUTED','CANCELLED')
        ),
        CONSTRAINT ck_pbi_document_type CHECK (
            document_type IN ('INVOICE','NFS_E','NFE_55','NFC_E_65','BOLETO','INVOICE_PDF')
        ),
        CONSTRAINT ck_pbi_country_code CHECK (
            country_code IS NULL OR LENGTH(country_code) = 2
        )
    );
    CREATE INDEX IF NOT EXISTS ix_pbi_partner_status
        ON partner_b2b_invoices (partner_id, status);
    CREATE INDEX IF NOT EXISTS ix_pbi_due_date
        ON partner_b2b_invoices (due_date);
    CREATE INDEX IF NOT EXISTS ix_pbi_country_jurisdiction
        ON partner_b2b_invoices (country_code, jurisdiction_code);
    CREATE UNIQUE INDEX IF NOT EXISTS ux_pbi_dedupe_key
        ON partner_b2b_invoices (dedupe_key)
        WHERE dedupe_key IS NOT NULL;
    CREATE UNIQUE INDEX IF NOT EXISTS ux_pbi_cycle
        ON partner_b2b_invoices (cycle_id);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_partner_credit_notes(engine: Engine) -> None:
    """
    FA-1: notas de crédito globais vinculadas a invoice/ciclo/parceiro.
    """
    stmt = """
    CREATE TABLE IF NOT EXISTS partner_credit_notes (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        partner_id VARCHAR(36) NOT NULL,
        original_invoice_id VARCHAR(36) REFERENCES partner_b2b_invoices(id),
        cycle_id VARCHAR(36) REFERENCES partner_billing_cycles(id),
        reason_code VARCHAR(40) NOT NULL,
        description TEXT NOT NULL,
        amount_cents BIGINT NOT NULL,
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        country_code VARCHAR(2),
        jurisdiction_code VARCHAR(32),
        timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
        status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
        dedupe_key VARCHAR(180),
        approved_by VARCHAR(36),
        approved_at TIMESTAMPTZ,
        applied_to_cycle_id VARCHAR(36),
        applied_at TIMESTAMPTZ,
        expires_at TIMESTAMPTZ,
        dispute_ref VARCHAR(140),
        metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT ck_pcn_reason_code CHECK (
            reason_code IN ('SLA_BREACH','HARDWARE_DOWNTIME','COMMERCIAL_ADJUSTMENT','DUPLICATE','TAX_ADJUSTMENT','OTHER')
        ),
        CONSTRAINT ck_pcn_status CHECK (
            status IN ('PENDING','APPROVED','APPLIED','REFUNDED','EXPIRED','CANCELLED')
        ),
        CONSTRAINT ck_pcn_country_code CHECK (
            country_code IS NULL OR LENGTH(country_code) = 2
        )
    );
    CREATE INDEX IF NOT EXISTS ix_pcn_partner_status
        ON partner_credit_notes (partner_id, status);
    CREATE INDEX IF NOT EXISTS ix_pcn_invoice
        ON partner_credit_notes (original_invoice_id);
    CREATE INDEX IF NOT EXISTS ix_pcn_country_jurisdiction
        ON partner_credit_notes (country_code, jurisdiction_code);
    CREATE UNIQUE INDEX IF NOT EXISTS ux_pcn_dedupe_key
        ON partner_credit_notes (dedupe_key)
        WHERE dedupe_key IS NOT NULL;
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_locker_utilization_snapshots(engine: Engine) -> None:
    """
    FA-2: snapshots diários de utilização para reconciliação uso x faturamento.
    """
    stmt = """
    CREATE TABLE IF NOT EXISTS locker_utilization_snapshots (
        id BIGSERIAL PRIMARY KEY,
        snapshot_date DATE NOT NULL,
        partner_id VARCHAR(36) NOT NULL,
        locker_id VARCHAR(36) NOT NULL,
        country_code VARCHAR(2),
        jurisdiction_code VARCHAR(32),
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',
        measured_occupied_minutes INTEGER NOT NULL DEFAULT 0,
        measured_occupied_hours NUMERIC(12,4) NOT NULL DEFAULT 0,
        billed_storage_units NUMERIC(12,4) NOT NULL DEFAULT 0,
        billed_storage_hours NUMERIC(12,4) NOT NULL DEFAULT 0,
        billed_storage_amount_cents BIGINT NOT NULL DEFAULT 0,
        difference_hours NUMERIC(12,4) NOT NULL DEFAULT 0,
        difference_pct NUMERIC(10,4),
        divergence_status VARCHAR(20) NOT NULL DEFAULT 'OK',
        dedupe_key VARCHAR(180),
        metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT ck_lus_status CHECK (
            divergence_status IN ('OK', 'UNDER_BILLED', 'OVER_BILLED', 'MISSING_BILLING')
        ),
        CONSTRAINT ck_lus_country_code CHECK (
            country_code IS NULL OR LENGTH(country_code) = 2
        )
    );
    CREATE UNIQUE INDEX IF NOT EXISTS ux_lus_partner_locker_date
        ON locker_utilization_snapshots (partner_id, locker_id, snapshot_date);
    CREATE UNIQUE INDEX IF NOT EXISTS ux_lus_dedupe_key
        ON locker_utilization_snapshots (dedupe_key)
        WHERE dedupe_key IS NOT NULL;
    CREATE INDEX IF NOT EXISTS ix_lus_snapshot_date
        ON locker_utilization_snapshots (snapshot_date);
    CREATE INDEX IF NOT EXISTS ix_lus_status_date
        ON locker_utilization_snapshots (divergence_status, snapshot_date);
    CREATE INDEX IF NOT EXISTS ix_lus_partner_locker
        ON locker_utilization_snapshots (partner_id, locker_id);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_chart_of_accounts(engine: Engine) -> None:
    """
    FA-3: plano de contas contábil (double-entry).
    """
    stmt = """
    CREATE TABLE IF NOT EXISTS chart_of_accounts (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        account_code VARCHAR(32) NOT NULL,
        account_name VARCHAR(140) NOT NULL,
        account_type VARCHAR(20) NOT NULL,
        normal_balance VARCHAR(10) NOT NULL,
        parent_account_id VARCHAR(36),
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        country_code VARCHAR(2),
        jurisdiction_code VARCHAR(32),
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_coa_account_code UNIQUE (account_code),
        CONSTRAINT ck_coa_account_type CHECK (
            account_type IN ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE')
        ),
        CONSTRAINT ck_coa_normal_balance CHECK (
            normal_balance IN ('DEBIT', 'CREDIT')
        ),
        CONSTRAINT ck_coa_country_code CHECK (
            country_code IS NULL OR LENGTH(country_code) = 2
        )
    );
    CREATE INDEX IF NOT EXISTS ix_coa_type_active
        ON chart_of_accounts (account_type, is_active);
    CREATE INDEX IF NOT EXISTS ix_coa_country_jurisdiction
        ON chart_of_accounts (country_code, jurisdiction_code);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_journal_entry_lines(engine: Engine) -> None:
    """
    FA-3: linhas de lançamento para garantir partidas dobradas.
    """
    stmt = """
    CREATE TABLE IF NOT EXISTS journal_entry_lines (
        id BIGSERIAL PRIMARY KEY,
        journal_entry_id VARCHAR(36) NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
        line_number INTEGER NOT NULL,
        account_id VARCHAR(36) NOT NULL REFERENCES chart_of_accounts(id),
        partner_id VARCHAR(36),
        locker_id VARCHAR(36),
        description VARCHAR(255),
        debit_amount NUMERIC(16,2) NOT NULL DEFAULT 0,
        credit_amount NUMERIC(16,2) NOT NULL DEFAULT 0,
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        country_code VARCHAR(2),
        jurisdiction_code VARCHAR(32),
        reference_source VARCHAR(50) NOT NULL DEFAULT 'manual',
        reference_id VARCHAR(36),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_jel_journal_entry_line_number UNIQUE (journal_entry_id, line_number),
        CONSTRAINT ck_jel_single_side CHECK (
            (debit_amount > 0 AND credit_amount = 0)
            OR (credit_amount > 0 AND debit_amount = 0)
        ),
        CONSTRAINT ck_jel_country_code CHECK (
            country_code IS NULL OR LENGTH(country_code) = 2
        )
    );
    CREATE INDEX IF NOT EXISTS ix_jel_journal_entry
        ON journal_entry_lines (journal_entry_id);
    CREATE INDEX IF NOT EXISTS ix_jel_account
        ON journal_entry_lines (account_id);
    CREATE INDEX IF NOT EXISTS ix_jel_partner_locker
        ON journal_entry_lines (partner_id, locker_id);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_financial_ledger_compat(engine: Engine) -> None:
    """
    FA-3: financial_ledger como camada de compatibilidade (derivada de journal entries).
    Não deve ser usada como fonte primária de verdade contábil.
    """
    stmt = """
    CREATE TABLE IF NOT EXISTS financial_ledger (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        order_id VARCHAR(36),
        payment_transaction_id VARCHAR(36),
        wallet_id VARCHAR(36),
        entry_type VARCHAR(30) NOT NULL,
        amount_cents BIGINT NOT NULL,
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        status VARCHAR(20) NOT NULL DEFAULT 'POSTED',
        external_reference VARCHAR(100),
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT ck_ledger_amount_nonzero CHECK (amount_cents <> 0),
        CONSTRAINT ck_ledger_status_check CHECK (
            status IN ('PENDING', 'POSTED', 'VOIDED')
        )
    );
    CREATE INDEX IF NOT EXISTS ix_financial_ledger_created_at
        ON financial_ledger (created_at);
    CREATE INDEX IF NOT EXISTS ix_financial_ledger_entry_type
        ON financial_ledger (entry_type);
    CREATE INDEX IF NOT EXISTS ix_financial_ledger_external_reference
        ON financial_ledger (external_reference);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_ellanlab_hardware_assets(engine: Engine) -> None:
    """
    FA-4: ativos de hardware para cálculo de CAPEX/depreciação por locker.
    """
    stmt = """
    CREATE TABLE IF NOT EXISTS ellanlab_hardware_assets (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        asset_code VARCHAR(64) NOT NULL,
        locker_id VARCHAR(36),
        partner_id VARCHAR(36),
        asset_category VARCHAR(40) NOT NULL,
        description VARCHAR(255) NOT NULL,
        acquisition_date DATE NOT NULL,
        in_service_date DATE,
        acquisition_cost_cents BIGINT NOT NULL,
        residual_value_cents BIGINT NOT NULL DEFAULT 0,
        useful_life_months INTEGER NOT NULL,
        depreciation_method VARCHAR(20) NOT NULL DEFAULT 'STRAIGHT_LINE',
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        country_code VARCHAR(2),
        jurisdiction_code VARCHAR(32),
        status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
        metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_eha_asset_code UNIQUE (asset_code),
        CONSTRAINT ck_eha_asset_category CHECK (
            asset_category IN ('LOCKER', 'TOTEM', 'SENSOR', 'NETWORK', 'BATTERY', 'OTHER')
        ),
        CONSTRAINT ck_eha_method CHECK (
            depreciation_method IN ('STRAIGHT_LINE')
        ),
        CONSTRAINT ck_eha_status CHECK (
            status IN ('ACTIVE', 'INACTIVE', 'DISPOSED')
        ),
        CONSTRAINT ck_eha_life CHECK (useful_life_months > 0),
        CONSTRAINT ck_eha_country_code CHECK (
            country_code IS NULL OR LENGTH(country_code) = 2
        )
    );
    CREATE INDEX IF NOT EXISTS ix_eha_locker_partner
        ON ellanlab_hardware_assets (locker_id, partner_id);
    CREATE INDEX IF NOT EXISTS ix_eha_status
        ON ellanlab_hardware_assets (status);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_ellanlab_depreciation_schedule(engine: Engine) -> None:
    """
    FA-4: agenda mensal de depreciação por ativo.
    """
    stmt = """
    CREATE TABLE IF NOT EXISTS ellanlab_depreciation_schedule (
        id BIGSERIAL PRIMARY KEY,
        asset_id VARCHAR(36) NOT NULL REFERENCES ellanlab_hardware_assets(id) ON DELETE CASCADE,
        depreciation_month DATE NOT NULL,
        partner_id VARCHAR(36),
        locker_id VARCHAR(36),
        depreciation_amount_cents BIGINT NOT NULL,
        accumulated_depreciation_cents BIGINT NOT NULL,
        nbv_cents BIGINT NOT NULL,
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        status VARCHAR(20) NOT NULL DEFAULT 'POSTED',
        dedupe_key VARCHAR(180),
        metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT ck_eds_status CHECK (status IN ('POSTED', 'REVERSED')),
        CONSTRAINT ck_eds_month_start CHECK (depreciation_month = date_trunc('month', depreciation_month)::date)
    );
    CREATE UNIQUE INDEX IF NOT EXISTS ux_eds_asset_month
        ON ellanlab_depreciation_schedule (asset_id, depreciation_month);
    CREATE UNIQUE INDEX IF NOT EXISTS ux_eds_dedupe_key
        ON ellanlab_depreciation_schedule (dedupe_key)
        WHERE dedupe_key IS NOT NULL;
    CREATE INDEX IF NOT EXISTS ix_eds_partner_locker_month
        ON ellanlab_depreciation_schedule (partner_id, locker_id, depreciation_month);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_ellanlab_opex_entries(engine: Engine) -> None:
    """
    FA-4: lançamentos OPEX operacionais por mês/parceiro/locker.
    """
    stmt = """
    CREATE TABLE IF NOT EXISTS ellanlab_opex_entries (
        id VARCHAR(36) NOT NULL PRIMARY KEY,
        expense_date DATE NOT NULL,
        expense_month DATE NOT NULL,
        partner_id VARCHAR(36),
        locker_id VARCHAR(36),
        cost_center_code VARCHAR(32),
        category VARCHAR(40) NOT NULL,
        description VARCHAR(255) NOT NULL,
        amount_cents BIGINT NOT NULL,
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        country_code VARCHAR(2),
        jurisdiction_code VARCHAR(32),
        vendor_ref VARCHAR(120),
        reference_source VARCHAR(50) NOT NULL DEFAULT 'manual',
        dedupe_key VARCHAR(180),
        metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT ck_eoe_category CHECK (
            category IN ('MAINTENANCE', 'CONNECTIVITY', 'ENERGY', 'RENT', 'SUPPORT', 'LOGISTICS', 'OTHER')
        ),
        CONSTRAINT ck_eoe_month_start CHECK (expense_month = date_trunc('month', expense_month)::date),
        CONSTRAINT ck_eoe_country_code CHECK (
            country_code IS NULL OR LENGTH(country_code) = 2
        )
    );
    CREATE INDEX IF NOT EXISTS ix_eoe_month
        ON ellanlab_opex_entries (expense_month);
    CREATE INDEX IF NOT EXISTS ix_eoe_partner_locker_month
        ON ellanlab_opex_entries (partner_id, locker_id, expense_month);
    CREATE UNIQUE INDEX IF NOT EXISTS ux_eoe_dedupe_key
        ON ellanlab_opex_entries (dedupe_key)
        WHERE dedupe_key IS NOT NULL;
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_ellanlab_monthly_pnl(engine: Engine) -> None:
    """
    FA-4: snapshot mensal consolidado de P&L por parceiro/locker.
    """
    stmt = """
    CREATE TABLE IF NOT EXISTS ellanlab_monthly_pnl (
        id BIGSERIAL PRIMARY KEY,
        pnl_month DATE NOT NULL,
        partner_id VARCHAR(36) NOT NULL,
        locker_id VARCHAR(36),
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        country_code VARCHAR(2),
        jurisdiction_code VARCHAR(32),
        revenue_cents BIGINT NOT NULL DEFAULT 0,
        cogs_cents BIGINT NOT NULL DEFAULT 0,
        opex_cents BIGINT NOT NULL DEFAULT 0,
        depreciation_cents BIGINT NOT NULL DEFAULT 0,
        gross_profit_cents BIGINT NOT NULL DEFAULT 0,
        gross_margin_pct NUMERIC(10,4),
        ebitda_cents BIGINT NOT NULL DEFAULT 0,
        net_income_cents BIGINT NOT NULL DEFAULT 0,
        ar_open_cents BIGINT NOT NULL DEFAULT 0,
        dso_days NUMERIC(10,2),
        metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT ck_emp_month_start CHECK (pnl_month = date_trunc('month', pnl_month)::date),
        CONSTRAINT ck_emp_country_code CHECK (
            country_code IS NULL OR LENGTH(country_code) = 2
        )
    );
    CREATE UNIQUE INDEX IF NOT EXISTS ux_emp_partner_locker_month
        ON ellanlab_monthly_pnl (partner_id, locker_id, pnl_month);
    CREATE INDEX IF NOT EXISTS ix_emp_month
        ON ellanlab_monthly_pnl (pnl_month);
    CREATE INDEX IF NOT EXISTS ix_emp_partner
        ON ellanlab_monthly_pnl (partner_id, pnl_month);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_ellanlab_revenue_recognition(engine: Engine) -> None:
    """
    FA-5: reconhecimento de receita diário por origem operacional (invoice/cycle/etc.).
    """
    stmt = """
    CREATE TABLE IF NOT EXISTS ellanlab_revenue_recognition (
        id BIGSERIAL PRIMARY KEY,
        recognition_date DATE NOT NULL,
        partner_id VARCHAR(36) NOT NULL,
        locker_id VARCHAR(36),
        source_type VARCHAR(40) NOT NULL,
        source_id VARCHAR(64) NOT NULL,
        recognition_rule VARCHAR(40) NOT NULL DEFAULT 'ACCRUAL_DAILY',
        recognized_amount_cents BIGINT NOT NULL,
        deferred_amount_cents BIGINT NOT NULL DEFAULT 0,
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        country_code VARCHAR(2),
        jurisdiction_code VARCHAR(32),
        dedupe_key VARCHAR(180),
        metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT ck_err_source_type CHECK (
            source_type IN ('PARTNER_INVOICE', 'PARTNER_CYCLE', 'MANUAL_ADJUSTMENT')
        ),
        CONSTRAINT ck_err_rule CHECK (
            recognition_rule IN ('ACCRUAL_DAILY', 'CASH_BASIS', 'MANUAL')
        ),
        CONSTRAINT ck_err_country_code CHECK (
            country_code IS NULL OR LENGTH(country_code) = 2
        )
    );
    CREATE UNIQUE INDEX IF NOT EXISTS ux_err_source_day
        ON ellanlab_revenue_recognition (source_type, source_id, recognition_date);
    DROP INDEX IF EXISTS ux_err_dedupe_key;
    CREATE UNIQUE INDEX IF NOT EXISTS ux_err_dedupe_key_time
        ON ellanlab_revenue_recognition (dedupe_key, recognition_date)
        WHERE dedupe_key IS NOT NULL;
    CREATE INDEX IF NOT EXISTS ix_err_partner_locker_day
        ON ellanlab_revenue_recognition (partner_id, locker_id, recognition_date);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_financial_kpi_daily(engine: Engine) -> None:
    """
    FA-5: snapshot diário de KPIs financeiros operacionais.
    """
    stmt = """
    CREATE TABLE IF NOT EXISTS financial_kpi_daily (
        id BIGSERIAL PRIMARY KEY,
        snapshot_date DATE NOT NULL,
        partner_id VARCHAR(36) NOT NULL,
        locker_id VARCHAR(36),
        currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
        country_code VARCHAR(2),
        jurisdiction_code VARCHAR(32),
        revenue_recognized_cents BIGINT NOT NULL DEFAULT 0,
        ar_open_cents BIGINT NOT NULL DEFAULT 0,
        arpl_cents BIGINT NOT NULL DEFAULT 0,
        gross_margin_pct NUMERIC(10,4) NOT NULL DEFAULT 0,
        dso_days NUMERIC(10,2) NOT NULL DEFAULT 0,
        active_invoice_count INTEGER NOT NULL DEFAULT 0,
        metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
        dedupe_key VARCHAR(180),
        computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT ck_fkd_country_code CHECK (
            country_code IS NULL OR LENGTH(country_code) = 2
        )
    );
    CREATE UNIQUE INDEX IF NOT EXISTS ux_fkd_partner_locker_day
        ON financial_kpi_daily (partner_id, locker_id, snapshot_date);
    DROP INDEX IF EXISTS ux_fkd_dedupe_key;
    CREATE UNIQUE INDEX IF NOT EXISTS ux_fkd_dedupe_key_time
        ON financial_kpi_daily (dedupe_key, snapshot_date)
        WHERE dedupe_key IS NOT NULL;
    CREATE INDEX IF NOT EXISTS ix_fkd_snapshot_day
        ON financial_kpi_daily (snapshot_date);
    """
    with engine.begin() as conn:
        conn.execute(text(stmt))


def _ensure_timescale_fa5_policies(engine: Engine) -> None:
    """
    FA-5: habilita (quando disponível) hypertables + políticas de compressão/retenção.
    Mantém execução resiliente para ambientes sem TimescaleDB.
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                DO $$
                BEGIN
                    BEGIN
                        CREATE EXTENSION IF NOT EXISTS timescaledb;
                    EXCEPTION WHEN OTHERS THEN
                        RAISE NOTICE 'timescaledb extension unavailable: %', SQLERRM;
                    END;
                END$$;
                """
            )
        )

        conn.execute(
            text(
                """
                DO $$
                DECLARE
                    has_timescaledb BOOLEAN := EXISTS (
                        SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
                    );
                BEGIN
                    IF NOT has_timescaledb THEN
                        RAISE NOTICE 'timescaledb not enabled; skipping FA-5 hypertables/policies';
                        RETURN;
                    END IF;

                    PERFORM create_hypertable(
                        'ellanlab_revenue_recognition',
                        'recognition_date',
                        if_not_exists => TRUE,
                        migrate_data => TRUE
                    );
                    PERFORM create_hypertable(
                        'financial_kpi_daily',
                        'snapshot_date',
                        if_not_exists => TRUE,
                        migrate_data => TRUE
                    );
                    PERFORM create_hypertable(
                        'ellanlab_monthly_pnl',
                        'pnl_month',
                        if_not_exists => TRUE,
                        migrate_data => TRUE
                    );

                    EXECUTE 'ALTER TABLE ellanlab_revenue_recognition SET (timescaledb.compress = true)';
                    EXECUTE 'ALTER TABLE financial_kpi_daily SET (timescaledb.compress = true)';
                    EXECUTE 'ALTER TABLE ellanlab_monthly_pnl SET (timescaledb.compress = true)';

                    EXECUTE 'SELECT add_compression_policy(''ellanlab_revenue_recognition'', INTERVAL ''14 days'', if_not_exists => TRUE)';
                    EXECUTE 'SELECT add_compression_policy(''financial_kpi_daily'', INTERVAL ''14 days'', if_not_exists => TRUE)';
                    EXECUTE 'SELECT add_compression_policy(''ellanlab_monthly_pnl'', INTERVAL ''90 days'', if_not_exists => TRUE)';

                    EXECUTE 'SELECT add_retention_policy(''ellanlab_revenue_recognition'', INTERVAL ''365 days'', if_not_exists => TRUE)';
                    EXECUTE 'SELECT add_retention_policy(''financial_kpi_daily'', INTERVAL ''365 days'', if_not_exists => TRUE)';
                    EXECUTE 'SELECT add_retention_policy(''ellanlab_monthly_pnl'', INTERVAL ''5 years'', if_not_exists => TRUE)';
                EXCEPTION WHEN OTHERS THEN
                    RAISE NOTICE 'timescale FA-5 policy setup skipped due to error: %', SQLERRM;
                END$$;
                """
            )
        )


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
    from app.models.fiscal_authority_callback import FiscalAuthorityCallback  # noqa: F401
    from app.models.fiscal_provider_health_status import FiscalProviderHealthStatus  # noqa: F401
    from app.models.fiscal_reconciliation_gap import FiscalReconciliationGap  # noqa: F401
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
    _ensure_fiscal_reconciliation_gaps(engine)
    _ensure_fiscal_provider_health_status(engine)
    _ensure_fiscal_authority_callbacks(engine)
    _ensure_partner_payment_holds(engine)
    _ensure_locker_slot_hourly_occupancy(engine)
    _ensure_journal_entries_foundation(engine)
    _ensure_partner_billing_plans(engine)
    _ensure_partner_billing_cycles(engine)
    _ensure_partner_billing_line_items(engine)
    _ensure_partner_b2b_invoices(engine)
    _ensure_partner_credit_notes(engine)
    _ensure_locker_utilization_snapshots(engine)
    _ensure_chart_of_accounts(engine)
    _ensure_journal_entry_lines(engine)
    _ensure_financial_ledger_compat(engine)
    _ensure_ellanlab_hardware_assets(engine)
    _ensure_ellanlab_depreciation_schedule(engine)
    _ensure_ellanlab_opex_entries(engine)
    _ensure_ellanlab_monthly_pnl(engine)
    _ensure_ellanlab_revenue_recognition(engine)
    _ensure_financial_kpi_daily(engine)
    _ensure_timescale_fa5_policies(engine)
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