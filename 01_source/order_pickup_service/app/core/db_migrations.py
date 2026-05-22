# 01_source/order_pickup_service/app/core/db_migrations.py
#
# Estratégia de banco de dados:
#   PRIMARY  → PostgreSQL (produção, cloud, back-office)
#   FALLBACK → SQLite    (KIOSK local — resiliência offline, replicação assíncrona separada)
#
# Este arquivo é a FONTE DA VERDADE para todo o schema do banco de dados.
# Qualquer alteração no schema deve ser feita AQUI, nunca diretamente no banco.
#
# Convenções:
#   - IDs: VARCHAR(36) compatível com UUID v4
#   - Timestamps: TIMESTAMPTZ (PostgreSQL) / TIMESTAMP WITH TIME ZONE (SQLite)
#   - Monetário: INTEGER (centavos) + VARCHAR(8) currency — nunca FLOAT
#   - JSON: JSONB (PostgreSQL) / TEXT (SQLite)
#   - Booleanos: BOOLEAN
#   - Migrações rastreadas em `schema_migrations`
#
# ══════════════════════════════════════════════════════════════════════════
# ORDEM DE CRIAÇÃO DAS TABELAS (respeita FK):
# ══════════════════════════════════════════════════════════════════════════
#
# 1. Extensões e schemas
# 2. Tipos ENUM
# 3. Tabelas de identidade (users, auth_sessions, core_user, etc.)
# 4. Lockers e operadores
# 5. Produtos e catálogos
# 6. Parceiros (ecommerce, logistics)
# 7. Pedidos e pagamentos
# 8. Alocações e pickups
# 9. Fulfillment e inventário
# 10. Documentos fiscais
# 11. Notificações e outbox
# 12. Métricas e ML
# 13. BI e Analytics (Metabase)
# 14. Funções, triggers, views materializadas
# 15. Row Level Security (RLS)
#

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import inspect, text

from app.core.db import engine

logger = logging.getLogger(__name__)

# ============================================================================
# Helpers de inspeção (dialect-agnóstico)
# ============================================================================

def _dialect(conn) -> str:
    return conn.dialect.name  # 'postgresql' | 'sqlite'


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(
        col["name"] == column_name
        for col in inspector.get_columns(table_name)
    )


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return any(
        idx["name"] == index_name
        for idx in inspector.get_indexes(table_name)
    )


def _has_type(conn, type_name: str) -> bool:
    """Verifica se um tipo ENUM existe no PostgreSQL."""
    if _dialect(conn) != "postgresql":
        return True  # SQLite não tem ENUM
    result = conn.execute(
        text("SELECT 1 FROM pg_type WHERE typname = :name"),
        {"name": type_name}
    ).fetchone()
    return result is not None


def _jsonb_or_text(conn) -> str:
    """Retorna JSONB em PostgreSQL, TEXT em SQLite."""
    return "JSONB" if _dialect(conn) == "postgresql" else "TEXT"


def _ts(conn) -> str:
    """Tipo de timestamp com fuso horário."""
    return "TIMESTAMPTZ" if _dialect(conn) == "postgresql" else "TIMESTAMP WITH TIME ZONE"


def _quote_ident(name: str) -> str:
    """Quote mínimo e seguro para identificadores SQL."""
    return '"' + name.replace('"', '""') + '"'


def _ensure_column(conn, table_name: str, column_name: str, ddl: str) -> None:
    """Garante que uma coluna exista. Idempotente e seguro."""
    inspector = inspect(conn)
    if not _has_table(inspector, table_name):
        return
    if _has_column(inspector, table_name, column_name):
        return

    logger.warning("[AUTO-HEAL] adicionando coluna %s.%s %s", table_name, column_name, ddl)
    conn.execute(text(f"ALTER TABLE {_quote_ident(table_name)} ADD COLUMN {_quote_ident(column_name)} {ddl}"))


def _ensure_index(conn, table_name: str, index_name: str, create_sql: str) -> None:
    """Garante que um índice exista."""
    inspector = inspect(conn)
    if not _has_table(inspector, table_name):
        return
    if _has_index(inspector, table_name, index_name):
        return

    logger.warning("[AUTO-HEAL] criando índice %s em %s", index_name, table_name)
    conn.execute(text(create_sql))


def _ensure_constraint(conn, table_name: str, constraint_name: str, constraint_sql: str) -> None:
    """Garante que uma constraint CHECK exista."""
    if _dialect(conn) != "postgresql":
        return
    result = conn.execute(
        text("SELECT 1 FROM pg_constraint WHERE conname = :name"),
        {"name": constraint_name}
    ).fetchone()
    if result:
        return
    logger.warning("[AUTO-HEAL] adicionando constraint %s em %s", constraint_name, table_name)
    conn.execute(text(f"ALTER TABLE {_quote_ident(table_name)} ADD CONSTRAINT {constraint_name} {constraint_sql}"))


# ============================================================================
# Versionamento de migrações
# ============================================================================

MIGRATIONS: dict[str, str] = {}


def _migration_applied(conn, name: str) -> bool:
    try:
        row = conn.execute(
            text("SELECT 1 FROM schema_migrations WHERE name = :name"),
            {"name": name},
        ).fetchone()
        return row is not None
    except Exception:
        return False


def _mark_migration(conn, name: str) -> None:
    conn.execute(
        text(
            "INSERT INTO schema_migrations (name, applied_at) "
            "VALUES (:name, :ts) ON CONFLICT (name) DO NOTHING"
        ),
        {"name": name, "ts": datetime.now(timezone.utc)},
    )


def _ensure_schema_migrations(conn) -> None:
    """Cria a tabela de controle de versão de migrations."""
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            name       VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))


# ============================================================================
# BLOCO 0 — Extensões e Schemas
# ============================================================================

def _create_extensions(conn, applied: list[str]) -> None:
    """Cria extensões PostgreSQL necessárias."""
    name = "extensions.create_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    extensions = [
        "timescaledb",
        "postgis",
        "postgis_topology",
        "postgis_tiger_geocoder",
        "address_standardizer",
        "pg_cron",
        "citext",
        "fuzzystrmatch",
    ]

    for ext in extensions:
        conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS {ext} WITH SCHEMA public"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_schemas(conn, applied: list[str]) -> None:
    """Cria schemas adicionais do sistema."""
    name = "schemas.create_v1"
    if _migration_applied(conn, name):
        return

    schemas = ["analytics_analytics", "geodata", "tiger", "tiger_data", "topology"]

    for schema in schemas:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 1 — Tipos ENUM
# ============================================================================

def _create_enums(conn, applied: list[str]) -> None:
    """Cria todos os tipos ENUM do sistema."""
    name = "enums.create_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    enums = [
        ("allocationstate", """CREATE TYPE allocationstate AS ENUM (
            'RESERVED_PENDING_PAYMENT', 'RESERVED_PAID_PENDING_PICKUP',
            'OPENED_FOR_PICKUP', 'PICKED_UP', 'EXPIRED', 'RELEASED',
            'CANCELLED', 'FRAUD_REVIEW', 'ERROR', 'MAINTENANCE', 'OUT_OF_STOCK'
        )"""),
        ("billing_cycle_status", """CREATE TYPE billing_cycle_status AS ENUM (
            'OPEN', 'COMPUTING', 'REVIEW', 'APPROVED', 'INVOICED', 'PAID', 'DISPUTED', 'CANCELLED'
        )"""),
        ("billing_cycle_type", "CREATE TYPE billing_cycle_type AS ENUM ('MONTHLY', 'YEARLY')"),
        ("billing_line_type", """CREATE TYPE billing_line_type AS ENUM (
            'BASE_FEE', 'DELIVERY_FEE', 'PICKUP_FEE', 'STORAGE_DAY_FEE',
            'OVERAGE_FEE', 'SLA_PENALTY', 'TAX', 'DISCOUNT', 'CREDIT_NOTE',
            'USAGE_FEE', 'ADJUSTMENT'
        )"""),
        ("billing_model_type", """CREATE TYPE billing_model_type AS ENUM (
            'FLAT_MONTHLY', 'PER_USE', 'HYBRID', 'REVENUE_SHARE', 'FREE_TIER'
        )"""),
        ("cardtype", "CREATE TYPE cardtype AS ENUM ('CREDIT', 'DEBIT', 'PREPAID', 'VIRTUAL')"),
        ("creditstatus", "CREATE TYPE creditstatus AS ENUM ('AVAILABLE', 'USED', 'EXPIRED', 'REVOKED')"),
        ("deadline_status_enum", "CREATE TYPE deadline_status_enum AS ENUM ('PENDING', 'EXECUTING', 'EXECUTED', 'CANCELLED', 'FAILED')"),
        ("deadline_type_enum", "CREATE TYPE deadline_type_enum AS ENUM ('PREPAYMENT_TIMEOUT', 'POSTPAYMENT_EXPIRY', 'PICKUP_TIMEOUT')"),
        ("dispute_state", "CREATE TYPE dispute_state AS ENUM ('NONE', 'OPEN', 'UNDER_REVIEW', 'ACCEPTED', 'REJECTED', 'CLOSED')"),
        ("event_status_enum", "CREATE TYPE event_status_enum AS ENUM ('PENDING', 'PUBLISHED', 'FAILED')"),
        ("evidence_strength", "CREATE TYPE evidence_strength AS ENUM ('NONE', 'WEAK', 'MEDIUM', 'STRONG', 'FINAL')"),
        ("financial_entry_type", """CREATE TYPE financial_entry_type AS ENUM (
            'SUBSCRIPTION_RENEWAL', 'ORDER_PAYMENT', 'REFUND',
            'COMMISSION_PAYOUT', 'GATEWAY_FEE', 'PLATFORM_FEE'
        )"""),
        ("fulfillment_order_status", "CREATE TYPE fulfillment_order_status AS ENUM ('PENDING', 'PROCESSING', 'SHIPPED', 'DELIVERED', 'FAILED', 'CANCELLED')"),
        ("inventory_movement_type", """CREATE TYPE inventory_movement_type AS ENUM (
            'RESTOCK', 'SALE', 'RESERVATION', 'RESERVATION_RELEASE',
            'ADJUSTMENT', 'RETURN', 'DAMAGE', 'EXPIRED', 'TRANSFER_IN', 'TRANSFER_OUT'
        )"""),
        ("inventory_reservation_status", "CREATE TYPE inventory_reservation_status AS ENUM ('ACTIVE', 'RELEASED', 'CONSUMED', 'EXPIRED')"),
        ("invoice_status_enum", "CREATE TYPE invoice_status_enum AS ENUM ('PENDING', 'PROCESSING', 'ISSUED', 'FAILED', 'CANCELLED')"),
        ("invoicestatus", """CREATE TYPE invoicestatus AS ENUM (
            'PENDING', 'ISSUED', 'FAILED', 'PROCESSING', 'DEAD_LETTER',
            'CANCELLED', 'CANCELLING', 'CORRECTION_REQUESTED', 'COMPLEMENTARY_ISSUED'
        )"""),
        ("locker_opex_cost_type", """CREATE TYPE locker_opex_cost_type AS ENUM (
            'RENT', 'MAINTENANCE_PREVENTIVE', 'MAINTENANCE_CORRECTIVE',
            'CONNECTIVITY', 'ENERGY', 'INSURANCE', 'CLEANING', 'SECURITY', 'OTHER'
        )"""),
        ("locker_slot_status", "CREATE TYPE locker_slot_status AS ENUM ('AVAILABLE', 'OCCUPIED', 'RESERVED', 'MAINTENANCE', 'BLOCKED')"),
        ("orderchannel", "CREATE TYPE orderchannel AS ENUM ('ONLINE', 'KIOSK', 'API', 'PARTNER', 'STAFF')"),
        ("orderstatus", """CREATE TYPE orderstatus AS ENUM (
            'PENDING_PAYMENT', 'PAID', 'ALLOCATED', 'PICKED_UP', 'CANCELLED',
            'REFUNDED', 'EXPIRED', 'PAYMENT_PENDING', 'PAID_PENDING_PICKUP'
        )"""),
        ("otpchannel", "CREATE TYPE otpchannel AS ENUM ('EMAIL', 'PHONE')"),
        ("partner_invoice_status", "CREATE TYPE partner_invoice_status AS ENUM ('DRAFT', 'ISSUED', 'SENT', 'VIEWED', 'PAID', 'OVERDUE', 'DISPUTED', 'CANCELLED')"),
        ("payment_reconciliation_status", "CREATE TYPE payment_reconciliation_status AS ENUM ('PENDING', 'MATCHED', 'MISMATCHED', 'RESOLVED')"),
        ("paymentinterface", """CREATE TYPE paymentinterface AS ENUM (
            'NFC', 'QR_CODE', 'CHIP', 'WEB_TOKEN', 'MANUAL', 'DEEP_LINK', 'API', 'USSD',
            'FACE_RECOGNITION', 'FINGERPRINT', 'BARCODE'
        )"""),
        ("paymentmethod", """CREATE TYPE paymentmethod AS ENUM (
            'PIX', 'CREDIT_CARD', 'DEBIT_CARD', 'CASH', 'VOUCHER', 'MBWAY', 'BIZUM', 'MERCADO_PAGO'
        )"""),
        ("paymentstatus", "CREATE TYPE paymentstatus AS ENUM ('PENDING', 'PAID', 'FAILED', 'REFUNDED', 'CANCELLED')"),
        ("pickup_phase", """CREATE TYPE pickup_phase AS ENUM (
            'CREATED', 'READY_FOR_PICKUP', 'AUTH_PENDING', 'AUTHENTICATED',
            'DISPENSE_REQUESTED', 'ACCESS_GRANTED', 'IN_PROGRESS', 'COMPLETED_UNVERIFIED',
            'COMPLETED_VERIFIED', 'EXPIRED', 'CANCELLED', 'FAILED', 'RECONCILING', 'RECONCILED'
        )"""),
        ("pickupchannel", "CREATE TYPE pickupchannel AS ENUM ('ONLINE', 'KIOSK')"),
        ("pickuplifecyclestage", """CREATE TYPE pickuplifecyclestage AS ENUM (
            'CREATED', 'READY_FOR_PICKUP', 'DOOR_OPENED', 'ITEM_REMOVED',
            'DOOR_CLOSED', 'COMPLETED', 'EXPIRED', 'CANCELLED'
        )"""),
        ("pickupredeemvia", "CREATE TYPE pickupredeemvia AS ENUM ('QR', 'MANUAL', 'KIOSK', 'SENSOR', 'OPERATOR', 'BLE')"),
        ("pickupstatus", "CREATE TYPE pickupstatus AS ENUM ('ACTIVE', 'REDEEMED', 'EXPIRED', 'CANCELLED')"),
        ("plan_type", "CREATE TYPE plan_type AS ENUM ('BASIC', 'PREMIUM', 'PRO', 'ENTERPRISE')"),
        ("promotion_type", "CREATE TYPE promotion_type AS ENUM ('PERCENT_OFF', 'FIXED_OFF', 'BUY_X_GET_Y', 'FREE_ITEM', 'BUNDLE_DISCOUNT')"),
        ("rental_contract_status", "CREATE TYPE rental_contract_status AS ENUM ('PENDING', 'ACTIVE', 'EXPIRED', 'CANCELLED')"),
        ("subscription_benefit_type", "CREATE TYPE subscription_benefit_type AS ENUM ('FREE_SHIPPING', 'PRIORITY_SHELF', 'EXCLUSIVE_DEAL')"),
        ("subscription_status", "CREATE TYPE subscription_status AS ENUM ('ACTIVE', 'CANCELLED', 'EXPIRED', 'TRIALING', 'PAST_DUE')"),
        ("telemetry_event_type", """CREATE TYPE telemetry_event_type AS ENUM (
            'HEARTBEAT', 'DOOR_FAILURE', 'SIGNAL_LOST', 'DOOR_OPENED',
            'DOOR_CLOSED', 'TEMPERATURE_ALERT', 'HARDWARE_ERROR'
        )"""),
        ("walletprovider", """CREATE TYPE walletprovider AS ENUM (
            'APPLE_PAY', 'GOOGLE_PAY', 'SAMSUNG_PAY', 'PAYPAL', 'MERCADO_PAGO',
            'PICPAY', 'VENMO', 'CASHAPP', 'REVOLUT', 'MBWAY', 'M_PESA', 'ALIPAY',
            'WECHAT_PAY', 'PAYPAY', 'LINE_PAY'
        )"""),
    ]

    for type_name, create_sql in enums:
        if not _has_type(conn, type_name):
            conn.execute(text(create_sql))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 2 — Tabelas de Identidade e Usuários
# ============================================================================

def _create_users(conn, applied: list[str]) -> None:
    name = "users.create_table_v2"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id                  VARCHAR(36)  PRIMARY KEY,
            full_name           VARCHAR(255) NOT NULL,
            email               VARCHAR(255) NOT NULL,
            phone               VARCHAR(32),
            password_hash       VARCHAR(255) NOT NULL,
            is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
            email_verified      BOOLEAN      NOT NULL DEFAULT FALSE,
            phone_verified      BOOLEAN      NOT NULL DEFAULT FALSE,
            created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            anonymized_at       TIMESTAMPTZ,
            locale              VARCHAR(10)  NOT NULL DEFAULT 'pt-BR',
            totp_enabled        BOOLEAN      NOT NULL DEFAULT FALSE,
            totp_secret_ref     VARCHAR(255),
            created_by          VARCHAR(36),
            updated_by          VARCHAR(36),
            deleted_at          TIMESTAMPTZ,
            tax_country         VARCHAR(2),
            tax_document_type   VARCHAR(16),
            tax_document_value  VARCHAR(1024),
            fiscal_email        VARCHAR(1024),
            fiscal_phone        VARCHAR(1024),
            fiscal_address_line1 VARCHAR(1024),
            fiscal_address_line2 VARCHAR(1024),
            fiscal_address_city VARCHAR(1024),
            fiscal_address_state VARCHAR(1024),
            fiscal_address_postal_code VARCHAR(1024),
            fiscal_address_country VARCHAR(2),
            fiscal_profile_updated_at TIMESTAMPTZ,
            fiscal_data_consent BOOLEAN      NOT NULL DEFAULT FALSE,
            cpf_encrypted       BYTEA,
            phone_encrypted     BYTEA
        )
    """))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON users (email) WHERE anonymized_at IS NULL"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_phone ON users (phone)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_totp_enabled ON users (totp_enabled)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_auth_sessions(conn, applied: list[str]) -> None:
    name = "auth_sessions.create_table_v2"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS auth_sessions (
            id                  BIGSERIAL    PRIMARY KEY,
            user_id             VARCHAR(36)  NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            session_token_hash  VARCHAR(255) NOT NULL,
            user_agent          VARCHAR(500),
            ip_address          VARCHAR(64),
            created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            expires_at          TIMESTAMPTZ  NOT NULL,
            revoked_at          TIMESTAMPTZ
        )
    """))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_auth_sessions_token_hash ON auth_sessions (session_token_hash)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_auth_sessions_user_id ON auth_sessions (user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_auth_sessions_expires_at ON auth_sessions (expires_at) WHERE revoked_at IS NULL"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_core_user(conn, applied: list[str]) -> None:
    """Tabela do Metabase para usuários."""
    name = "core_user.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS core_user (
            id                 INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            email              CITEXT NOT NULL UNIQUE,
            first_name         VARCHAR(254),
            last_name          VARCHAR(254),
            password           VARCHAR(254),
            password_salt      VARCHAR(254) DEFAULT 'default',
            date_joined        TIMESTAMPTZ NOT NULL,
            last_login         TIMESTAMPTZ,
            is_superuser       BOOLEAN NOT NULL DEFAULT FALSE,
            is_active          BOOLEAN NOT NULL DEFAULT TRUE,
            reset_token        VARCHAR(254),
            reset_triggered    BIGINT,
            is_qbnewb          BOOLEAN NOT NULL DEFAULT TRUE,
            login_attributes   TEXT,
            updated_at         TIMESTAMP,
            sso_source         VARCHAR(254),
            locale             VARCHAR(5),
            is_datasetnewb     BOOLEAN NOT NULL DEFAULT TRUE,
            settings           TEXT,
            type               VARCHAR(64) NOT NULL DEFAULT 'personal'
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lower_email ON core_user (LOWER(email))"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_full_name ON core_user (((first_name || ' ' || last_name)))"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_core_session(conn, applied: list[str]) -> None:
    """Tabela do Metabase para sessões."""
    name = "core_session.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS core_session (
            id               VARCHAR(254) PRIMARY KEY,
            user_id          INTEGER NOT NULL REFERENCES core_user(id) ON DELETE CASCADE,
            created_at       TIMESTAMPTZ NOT NULL,
            anti_csrf_token  TEXT
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_core_session_user_id ON core_session (user_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_login_history(conn, applied: list[str]) -> None:
    name = "login_history.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS login_history (
            id                 INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            timestamp          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            user_id            INTEGER NOT NULL REFERENCES core_user(id) ON DELETE CASCADE,
            session_id         VARCHAR(254) REFERENCES core_session(id) ON DELETE SET NULL,
            device_id          CHAR(36) NOT NULL,
            device_description TEXT NOT NULL,
            ip_address         TEXT NOT NULL
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_id ON login_history (user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_timestamp ON login_history (timestamp)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_login_otps(conn, applied: list[str]) -> None:
    name = "login_otps.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS login_otps (
            id             VARCHAR(36) PRIMARY KEY,
            channel        OTPCHANNEL NOT NULL,
            email          VARCHAR(255),
            phone          VARCHAR(32),
            otp_hash       VARCHAR(255) NOT NULL,
            expires_at     TIMESTAMPTZ NOT NULL,
            used_at        TIMESTAMPTZ,
            attempts       INTEGER NOT NULL,
            requested_ip   VARCHAR(64),
            created_at     TIMESTAMPTZ NOT NULL
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_login_otps_email ON login_otps (email)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_login_otps_phone ON login_otps (phone)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_login_otps_expires_at ON login_otps (expires_at)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_user_roles(conn, applied: list[str]) -> None:
    name = "user_roles.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS user_roles (
            id          VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id     VARCHAR(36) NOT NULL REFERENCES users(id),
            role        VARCHAR(40) NOT NULL,
            scope_type  VARCHAR(40) DEFAULT 'GLOBAL',
            scope_id    VARCHAR(36),
            is_active   BOOLEAN NOT NULL DEFAULT TRUE,
            granted_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            revoked_at  TIMESTAMPTZ
        )
    """))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_user_role_active ON user_roles (user_id, role, scope_type, scope_id) WHERE revoked_at IS NULL"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_privacy_consents(conn, applied: list[str]) -> None:
    name = "privacy_consents.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS privacy_consents (
            id                  VARCHAR(36) PRIMARY KEY,
            user_id             VARCHAR(36) REFERENCES users(id),
            guest_identifier    VARCHAR(255),
            consent_type        VARCHAR(50) NOT NULL,
            granted             BOOLEAN NOT NULL,
            channel             VARCHAR(20),
            ip_address          VARCHAR(64),
            user_agent          VARCHAR(500),
            policy_version      VARCHAR(20),
            granted_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            revoked_at          TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_consents_user ON privacy_consents (user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_consents_guest ON privacy_consents (guest_identifier)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_consents_type ON privacy_consents (consent_type)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_data_deletion_requests(conn, applied: list[str]) -> None:
    name = "data_deletion_requests.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS data_deletion_requests (
            id               VARCHAR(36) PRIMARY KEY,
            user_id          VARCHAR(36) REFERENCES users(id),
            requested_by     VARCHAR(255),
            status           VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            reason           VARCHAR(255),
            rejection_reason TEXT,
            requested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at     TIMESTAMPTZ,
            notes            TEXT,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_deletion_req_user ON data_deletion_requests (user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_deletion_req_status ON data_deletion_requests (status)"))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 3 — Lockers e Operadores
# ============================================================================

def _create_locker_operators(conn, applied: list[str]) -> None:
    name = "locker_operators.create_table_v2"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS locker_operators (
            id                  VARCHAR(64) PRIMARY KEY,
            name                VARCHAR(128) NOT NULL,
            document            VARCHAR(32),
            email               VARCHAR(128),
            phone               VARCHAR(32),
            operator_type       VARCHAR(32) NOT NULL DEFAULT 'LOGISTICS',
            country             VARCHAR(2) NOT NULL DEFAULT 'BR',
            active              BOOLEAN NOT NULL DEFAULT TRUE,
            commission_rate     NUMERIC(6,4),
            currency            VARCHAR(8) NOT NULL DEFAULT 'BRL',
            created_at          TIMESTAMPTZ NOT NULL,
            updated_at          TIMESTAMPTZ NOT NULL,
            contract_start_at   TIMESTAMPTZ,
            contract_end_at     TIMESTAMPTZ,
            contract_ref        VARCHAR(255),
            sla_pickup_hours    INTEGER NOT NULL DEFAULT 72,
            sla_return_hours    INTEGER NOT NULL DEFAULT 24,
            status              VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
            legal_name          VARCHAR(140),
            tier                VARCHAR(20) DEFAULT 'STANDARD'
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_locker_operators_document ON locker_operators (document)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_lockers(conn, applied: list[str]) -> None:
    name = "lockers.create_table_v3"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS lockers (
            id                      VARCHAR(36) PRIMARY KEY,
            external_id             VARCHAR(100),
            display_name            VARCHAR(255),
            description             TEXT,
            region                  VARCHAR(10) NOT NULL,
            site_id                 VARCHAR(100),
            timezone                VARCHAR(50),
            address_line            VARCHAR(255),
            address_number          VARCHAR(50),
            address_extra           VARCHAR(255),
            district                VARCHAR(100),
            city                    VARCHAR(100),
            state                   VARCHAR(100),
            postal_code             VARCHAR(50),
            country                 VARCHAR(100),
            latitude                DOUBLE PRECISION,
            longitude               DOUBLE PRECISION,
            active                  BOOLEAN DEFAULT TRUE,
            slots_count             INTEGER NOT NULL DEFAULT 0,
            machine_id              VARCHAR(100),
            allowed_channels        VARCHAR(100),
            allowed_payment_methods VARCHAR(255),
            temperature_zone        VARCHAR(50) DEFAULT 'AMBIENT',
            security_level          VARCHAR(50) DEFAULT 'STANDARD',
            has_camera              BOOLEAN DEFAULT FALSE,
            has_alarm               BOOLEAN DEFAULT FALSE,
            access_hours            TEXT,
            operator_id             VARCHAR(100),
            tenant_id               VARCHAR(100),
            is_rented               BOOLEAN DEFAULT FALSE,
            metadata_json           JSONB,
            created_at              TIMESTAMPTZ NOT NULL,
            updated_at              TIMESTAMPTZ NOT NULL,
            finding_instructions    TEXT,
            pickup_code_length      INTEGER NOT NULL DEFAULT 6,
            pickup_reuse_policy     VARCHAR(32) NOT NULL DEFAULT 'NO_REUSE',
            pickup_reuse_window_sec INTEGER,
            pickup_max_reopens      INTEGER NOT NULL DEFAULT 0,
            geolocation_wkt         TEXT,
            has_card_reader         BOOLEAN NOT NULL DEFAULT FALSE,
            has_kiosk               BOOLEAN NOT NULL DEFAULT FALSE,
            has_nfc                 BOOLEAN NOT NULL DEFAULT FALSE,
            has_printer             BOOLEAN NOT NULL DEFAULT FALSE,
            slots_available         INTEGER NOT NULL DEFAULT 0,
            payment_rules           JSONB,
            created_by              VARCHAR(36),
            updated_by              VARCHAR(36),
            deleted_at              TIMESTAMPTZ,
            has_ble                 BOOLEAN NOT NULL DEFAULT FALSE
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lockers_active ON lockers (active)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lockers_operator ON lockers (operator_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lockers_region ON lockers (region)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lockers_site_id ON lockers (site_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lockers_tenant_id ON lockers (tenant_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lockers_machine_id ON lockers (machine_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lockers_lat_lng ON lockers (latitude, longitude)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lockers_has_ble ON lockers (has_ble) WHERE has_ble = true"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lockers_active_ble ON lockers (active, has_ble) WHERE active = true"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_capability_locker_location(conn, applied: list[str]) -> None:
    name = "capability_locker_location.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS capability_locker_location (
            id                 INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            external_id        VARCHAR(100) UNIQUE,
            province_code      VARCHAR(10),
            city_name          VARCHAR(100),
            district           VARCHAR(100),
            postal_code        VARCHAR(20),
            latitude           NUMERIC(10,8),
            longitude          NUMERIC(11,8),
            geom               GEOMETRY(Point, 4326),
            timezone           VARCHAR(50),
            address_street     VARCHAR(255),
            address_number     VARCHAR(20),
            address_complement VARCHAR(100),
            operating_hours_json JSONB,
            is_active          BOOLEAN DEFAULT TRUE,
            metadata_json      JSONB,
            created_at         TIMESTAMPTZ DEFAULT NOW(),
            updated_at         TIMESTAMPTZ DEFAULT NOW(),
            has_ble            BOOLEAN DEFAULT FALSE
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_capability_locker_location_geom ON capability_locker_location USING GIST (geom)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_locker_is_active ON capability_locker_location (is_active)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_locker_city_name ON capability_locker_location (city_name)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_locker_postal_code ON capability_locker_location (postal_code)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_location_ble_geom ON capability_locker_location USING GIST (geom) WHERE (has_ble = true AND is_active = true)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_capability_country(conn, applied: list[str]) -> None:
    name = "capability_country.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS capability_country (
            id                INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            code              CHAR(2) NOT NULL UNIQUE,
            name              VARCHAR(100) NOT NULL,
            continent         VARCHAR(50),
            default_currency  CHAR(3),
            default_timezone  VARCHAR(50),
            address_format    VARCHAR(20),
            metadata_json     JSONB,
            is_active         BOOLEAN DEFAULT TRUE,
            created_at        TIMESTAMPTZ DEFAULT NOW(),
            updated_at        TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_country_code ON capability_country (code)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_country_continent ON capability_country (continent)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_country_is_active ON capability_country (is_active)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_capability_province(conn, applied: list[str]) -> None:
    name = "capability_province.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS capability_province (
            id                   INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            code                 VARCHAR(10) NOT NULL UNIQUE,
            name                 VARCHAR(100) NOT NULL,
            country_code         CHAR(2) REFERENCES capability_country(code) ON DELETE CASCADE,
            province_code_original CHAR(2),
            region               VARCHAR(50),
            timezone             VARCHAR(50),
            is_active            BOOLEAN DEFAULT TRUE,
            metadata_json        JSONB,
            created_at           TIMESTAMPTZ DEFAULT NOW(),
            updated_at           TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_province_code ON capability_province (code)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_province_country_code ON capability_province (country_code)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_province_is_active ON capability_province (is_active)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_locker_slots(conn, applied: list[str]) -> None:
    name = "locker_slots.create_table_v2"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS locker_slots (
            id                    VARCHAR(36) PRIMARY KEY,
            locker_id             VARCHAR(36) NOT NULL REFERENCES lockers(id),
            slot_label            VARCHAR(20) NOT NULL,
            slot_size             VARCHAR(8) NOT NULL,
            status                VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE',
            occupied_since        TIMESTAMPTZ,
            current_allocation_id VARCHAR(36),
            current_delivery_id   VARCHAR(36),
            current_rental_id     VARCHAR(36),
            last_opened_at        TIMESTAMPTZ,
            last_closed_at        TIMESTAMPTZ,
            fault_code            VARCHAR(50),
            fault_detail          TEXT,
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(locker_id, slot_label)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_locker_slots_locker_status ON locker_slots (locker_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_locker_slots_status ON locker_slots (status)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_locker_slot_configs(conn, applied: list[str]) -> None:
    name = "locker_slot_configs.create_table_v2"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS locker_slot_configs (
            id              BIGSERIAL PRIMARY KEY,
            locker_id       VARCHAR(64) NOT NULL REFERENCES lockers(id),
            slot_size       VARCHAR(8) NOT NULL,
            slot_count      INTEGER NOT NULL DEFAULT 0,
            available_count INTEGER,
            width_cm        INTEGER,
            height_cm       INTEGER,
            depth_cm        INTEGER,
            max_weight_kg   DOUBLE PRECISION,
            created_at      TIMESTAMPTZ NOT NULL,
            updated_at      TIMESTAMPTZ NOT NULL,
            width_mm        INTEGER,
            height_mm       INTEGER,
            depth_mm        INTEGER,
            max_weight_g    INTEGER,
            UNIQUE(locker_id, slot_size)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_locker_slot_locker ON locker_slot_configs (locker_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_runtime_lockers(conn, applied: list[str]) -> None:
    name = "runtime_lockers.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS runtime_lockers (
            locker_id          VARCHAR(120) PRIMARY KEY,
            machine_id         VARCHAR(120) NOT NULL UNIQUE,
            display_name       VARCHAR(255) NOT NULL,
            region             VARCHAR(16) NOT NULL,
            country            VARCHAR(8) NOT NULL,
            timezone           VARCHAR(64) NOT NULL,
            operator_id        VARCHAR(120),
            temperature_zone   VARCHAR(32) NOT NULL DEFAULT 'AMBIENT',
            security_level     VARCHAR(32) NOT NULL DEFAULT 'STANDARD',
            active             BOOLEAN NOT NULL DEFAULT TRUE,
            runtime_enabled    BOOLEAN NOT NULL DEFAULT TRUE,
            mqtt_region        VARCHAR(32) NOT NULL,
            mqtt_locker_id     VARCHAR(120) NOT NULL,
            topology_version   INTEGER NOT NULL DEFAULT 1,
            slot_count_total   INTEGER NOT NULL,
            created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            payment_methods_json JSONB NOT NULL DEFAULT '[]'
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_runtime_lockers_active ON runtime_lockers (active, runtime_enabled)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_runtime_lockers_region ON runtime_lockers (region)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_runtime_locker_slots(conn, applied: list[str]) -> None:
    name = "runtime_locker_slots.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS runtime_locker_slots (
            locker_id      VARCHAR(120) NOT NULL REFERENCES runtime_lockers(locker_id) ON DELETE CASCADE,
            slot_number    INTEGER NOT NULL,
            slot_size      VARCHAR(16) NOT NULL,
            width_mm       INTEGER,
            height_mm      INTEGER,
            depth_mm       INTEGER,
            max_weight_g   INTEGER,
            is_active      BOOLEAN NOT NULL DEFAULT TRUE,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            width_cm       INTEGER,
            height_cm      INTEGER,
            depth_cm       INTEGER,
            max_weight_kg  NUMERIC(10,3),
            PRIMARY KEY (locker_id, slot_number)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_runtime_locker_slots_active ON runtime_locker_slots (locker_id, is_active, slot_number)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_runtime_locker_features(conn, applied: list[str]) -> None:
    name = "runtime_locker_features.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS runtime_locker_features (
            locker_id                    VARCHAR(120) PRIMARY KEY REFERENCES runtime_lockers(locker_id) ON DELETE CASCADE,
            supports_online              BOOLEAN NOT NULL DEFAULT TRUE,
            supports_kiosk               BOOLEAN NOT NULL DEFAULT TRUE,
            supports_pickup_qr           BOOLEAN NOT NULL DEFAULT TRUE,
            supports_manual_code         BOOLEAN NOT NULL DEFAULT TRUE,
            supports_open_command        BOOLEAN NOT NULL DEFAULT TRUE,
            supports_light_command       BOOLEAN NOT NULL DEFAULT TRUE,
            supports_paid_pending_pickup BOOLEAN NOT NULL DEFAULT TRUE,
            supports_refrigerated_items  BOOLEAN NOT NULL DEFAULT FALSE,
            supports_frozen_items        BOOLEAN NOT NULL DEFAULT FALSE,
            supports_high_value_items    BOOLEAN NOT NULL DEFAULT FALSE,
            created_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            supports_boolean             BOOLEAN NOT NULL DEFAULT FALSE,
            supports_ble                 BOOLEAN NOT NULL DEFAULT FALSE
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_runtime_sync_queue(conn, applied: list[str]) -> None:
    name = "runtime_sync_queue.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS runtime_sync_queue (
            id             VARCHAR(36) PRIMARY KEY,
            locker_id      VARCHAR(64) NOT NULL,
            operation      VARCHAR(32) NOT NULL,
            status         VARCHAR(20) NOT NULL,
            retry_count    INTEGER NOT NULL DEFAULT 0,
            max_retries    INTEGER NOT NULL DEFAULT 3,
            last_error     TEXT,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            processed_at   TIMESTAMPTZ,
            next_retry_at  TIMESTAMPTZ
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_runtime_sync_queue_locker ON runtime_sync_queue (locker_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_runtime_sync_queue_status ON runtime_sync_queue (status)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_locker_telemetry(conn, applied: list[str]) -> None:
    name = "locker_telemetry.create_table_v1"
    if _migration_applied(conn, name):
        return

    jsonb = _jsonb_or_text(conn)
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS locker_telemetry (
            id                  BIGSERIAL PRIMARY KEY,
            locker_id           VARCHAR(36) NOT NULL REFERENCES lockers(id),
            event_type          VARCHAR(50) NOT NULL,
            slot_label          VARCHAR(20),
            temperature_celsius NUMERIC(5,2),
            humidity_pct        NUMERIC(5,2),
            battery_pct         NUMERIC(5,2),
            voltage_mv          INTEGER,
            signal_rssi         INTEGER,
            firmware_version    VARCHAR(50),
            raw_payload_json    {jsonb},
            occurred_at         TIMESTAMPTZ NOT NULL,
            received_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_locker_telemetry_locker_time ON locker_telemetry (locker_id, occurred_at DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_locker_telemetry_event_time ON locker_telemetry (event_type, occurred_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_locker_telemetry_partitioned(conn, applied: list[str]) -> None:
    """Tabela particionada para telemetria (TimescaleDB)."""
    name = "locker_telemetry_partitioned.create_table_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS locker_telemetry_partitioned (
            id                  BIGSERIAL NOT NULL,
            locker_id           VARCHAR(36) NOT NULL,
            event_type          VARCHAR(50) NOT NULL,
            slot_label          VARCHAR(20),
            temperature_celsius NUMERIC(5,2),
            humidity_pct        NUMERIC(5,2),
            battery_pct         NUMERIC(5,2),
            voltage_mv          INTEGER,
            signal_rssi         INTEGER,
            firmware_version    VARCHAR(50),
            raw_payload_json    JSONB,
            occurred_at         TIMESTAMPTZ NOT NULL,
            received_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_door_state(conn, applied: list[str]) -> None:
    name = "door_state.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS door_state (
            machine_id VARCHAR(120) NOT NULL,
            door_id    INTEGER NOT NULL,
            state      VARCHAR(40) NOT NULL,
            product_id VARCHAR(120),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (machine_id, door_id)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_door_state_machine ON door_state (machine_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_door_state_machine_state ON door_state (machine_id, state)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_ble_handshake_logs(conn, applied: list[str]) -> None:
    name = "ble_handshake_logs.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ble_handshake_logs (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            pickup_id        VARCHAR(36) NOT NULL REFERENCES pickups(id) ON DELETE CASCADE,
            locker_id        VARCHAR(36) NOT NULL REFERENCES lockers(id),
            handshake_type   VARCHAR(20) NOT NULL,
            status           VARCHAR(20) NOT NULL,
            rssi_at_handshake INTEGER,
            duration_ms      INTEGER,
            challenge_hash   VARCHAR(128),
            response_hash    VARCHAR(128),
            ble_device_id    VARCHAR(128),
            error_code       VARCHAR(50),
            error_message    TEXT,
            metadata_json    JSONB DEFAULT '{}',
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ble_handshake_pickup ON ble_handshake_logs (pickup_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ble_handshake_locker_created ON ble_handshake_logs (locker_id, created_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_tenant_fiscal_config(conn, applied: list[str]) -> None:
    name = "tenant_fiscal_config.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS tenant_fiscal_config (
            tenant_id      VARCHAR(100) PRIMARY KEY,
            cnpj           VARCHAR(18) NOT NULL,
            razao_social   VARCHAR(140) NOT NULL,
            ie             VARCHAR(20),
            regime         VARCHAR(20) NOT NULL,
            crt            CHAR(1) NOT NULL,
            cert_a1_ref    VARCHAR(255),
            is_active      BOOLEAN NOT NULL DEFAULT TRUE,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            brand_config   JSONB NOT NULL DEFAULT '{
                "logo_url": null, "accent_color": "#38A169",
                "company_name": null, "custom_domain": null,
                "primary_color": "#1A365D", "support_email": null,
                "support_phone": null, "secondary_color": "#2D3748"
            }'::jsonb
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_tenant_fiscal_active ON tenant_fiscal_config (is_active)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_custom_domains(conn, applied: list[str]) -> None:
    name = "custom_domains.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS custom_domains (
            id            VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id     VARCHAR(100) NOT NULL REFERENCES tenant_fiscal_config(tenant_id),
            domain        VARCHAR(255) NOT NULL UNIQUE,
            verified      BOOLEAN DEFAULT FALSE,
            ssl_cert_ref  VARCHAR(255),
            created_at    TIMESTAMPTZ DEFAULT NOW(),
            verified_at   TIMESTAMPTZ
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_cost_centers(conn, applied: list[str]) -> None:
    name = "cost_centers.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS cost_centers (
            id                           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            locker_id                    VARCHAR(36) REFERENCES lockers(id),
            operational_cost_monthly_cents BIGINT,
            maintenance_cost_annual_cents   BIGINT,
            depreciation_cost_annual_cents  BIGINT,
            utilities_cost_monthly_cents    BIGINT,
            created_at                   TIMESTAMPTZ DEFAULT NOW(),
            updated_at                   TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_cost_center_monthly(conn, applied: list[str]) -> None:
    name = "cost_center_monthly.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS cost_center_monthly (
            id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            locker_id                   VARCHAR(36) NOT NULL REFERENCES lockers(id) ON DELETE CASCADE,
            month                       DATE NOT NULL,
            rent_cents                  BIGINT DEFAULT 0,
            maintenance_preventive_cents BIGINT DEFAULT 0,
            maintenance_corrective_cents BIGINT DEFAULT 0,
            connectivity_cents          BIGINT DEFAULT 0,
            energy_cents                BIGINT DEFAULT 0,
            insurance_cents             BIGINT DEFAULT 0,
            payment_gateway_fee_cents   BIGINT DEFAULT 0,
            depreciation_cents          BIGINT DEFAULT 0,
            cleaning_cents              BIGINT DEFAULT 0,
            security_cents              BIGINT DEFAULT 0,
            marketing_cents             BIGINT DEFAULT 0,
            other_cents                 BIGINT DEFAULT 0,
            notes                       TEXT,
            metadata_json               JSONB DEFAULT '{}',
            created_by                  VARCHAR(36) REFERENCES users(id),
            updated_by                  VARCHAR(36) REFERENCES users(id),
            created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(locker_id, month),
            CONSTRAINT ck_ccm_month_start CHECK (month = date_trunc('month', month)::date)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ccm_locker_id ON cost_center_monthly (locker_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ccm_month ON cost_center_monthly (month DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_locker_capex(conn, applied: list[str]) -> None:
    name = "locker_capex.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS locker_capex (
            id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            locker_id               VARCHAR(36) NOT NULL REFERENCES lockers(id),
            asset_id                VARCHAR(36) REFERENCES ellanlab_hardware_assets(id),
            acquisition_cost_cents  BIGINT NOT NULL,
            installation_cost_cents BIGINT NOT NULL DEFAULT 0,
            residual_value_cents    BIGINT NOT NULL DEFAULT 0,
            useful_life_months      INTEGER NOT NULL DEFAULT 60,
            depreciation_method     VARCHAR(20) NOT NULL DEFAULT 'STRAIGHT_LINE',
            depreciation_start_date DATE NOT NULL DEFAULT CURRENT_DATE,
            status                  VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
            disposal_date           DATE,
            disposal_proceeds_cents BIGINT DEFAULT 0,
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_locker_capex_locker ON locker_capex (locker_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_locker_capex_details(conn, applied: list[str]) -> None:
    name = "locker_capex_details.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS locker_capex_details (
            id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            locker_id               VARCHAR(36) NOT NULL UNIQUE REFERENCES lockers(id) ON DELETE CASCADE,
            equipment_cost_cents    BIGINT NOT NULL DEFAULT 0,
            installation_cost_cents BIGINT NOT NULL DEFAULT 0,
            connectivity_setup_cents BIGINT NOT NULL DEFAULT 0,
            go_live_cost_cents      BIGINT NOT NULL DEFAULT 0,
            property_rent_cents     BIGINT DEFAULT 0,
            property_ownership      BOOLEAN DEFAULT FALSE,
            property_address        TEXT,
            useful_life_months      INTEGER DEFAULT 60,
            salvage_value_cents     BIGINT DEFAULT 0,
            depreciation_method     VARCHAR(20) DEFAULT 'STRAIGHT_LINE',
            installation_date       DATE,
            go_live_date            DATE,
            supplier                VARCHAR(255),
            invoice_ref             VARCHAR(255),
            metadata_json           JSONB DEFAULT '{}',
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_locker_opex(conn, applied: list[str]) -> None:
    name = "locker_opex.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS locker_opex (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            locker_id        VARCHAR(36) NOT NULL REFERENCES lockers(id),
            reference_month  DATE NOT NULL,
            cost_type        VARCHAR(40) NOT NULL,
            amount_cents     BIGINT NOT NULL,
            currency         VARCHAR(8) NOT NULL DEFAULT 'BRL',
            description      TEXT,
            invoice_ref      VARCHAR(100),
            paid_at          TIMESTAMPTZ,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(locker_id, reference_month, cost_type)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_locker_opex_locker_month ON locker_opex (locker_id, reference_month DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 4 — Produtos e Catálogos
# ============================================================================

def _create_product_categories(conn, applied: list[str]) -> None:
    name = "product_categories.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_categories (
            id                       VARCHAR(64) PRIMARY KEY,
            name                     VARCHAR(128) NOT NULL,
            description              TEXT,
            parent_category          VARCHAR(64) REFERENCES product_categories(id),
            default_temperature_zone VARCHAR(32) NOT NULL DEFAULT 'AMBIENT',
            default_security_level   VARCHAR(32) NOT NULL DEFAULT 'STANDARD',
            is_hazardous             BOOLEAN NOT NULL DEFAULT FALSE,
            requires_age_verification BOOLEAN NOT NULL DEFAULT FALSE,
            created_at               TIMESTAMPTZ NOT NULL,
            updated_at               TIMESTAMPTZ NOT NULL,
            requires_id              BOOLEAN DEFAULT FALSE,
            requires_signature       BOOLEAN DEFAULT FALSE,
            max_weight_g             INTEGER,
            max_width_mm             INTEGER,
            max_height_mm            INTEGER,
            max_depth_mm             INTEGER
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_product_categories_parent ON product_categories (parent_category)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_products(conn, applied: list[str]) -> None:
    name = "products.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
            id                      VARCHAR(255) PRIMARY KEY,
            name                    VARCHAR(255) NOT NULL,
            description             TEXT,
            amount_cents            INTEGER NOT NULL,
            currency                VARCHAR(8) NOT NULL DEFAULT 'BRL',
            category_id             VARCHAR(64) REFERENCES product_categories(id),
            width_mm                INTEGER,
            height_mm               INTEGER,
            depth_mm                INTEGER,
            weight_g                INTEGER,
            is_active               BOOLEAN NOT NULL DEFAULT TRUE,
            requires_age_verification BOOLEAN NOT NULL DEFAULT FALSE,
            requires_id_check       BOOLEAN NOT NULL DEFAULT FALSE,
            requires_signature      BOOLEAN NOT NULL DEFAULT FALSE,
            is_hazardous            BOOLEAN NOT NULL DEFAULT FALSE,
            is_fragile              BOOLEAN NOT NULL DEFAULT FALSE,
            is_virtual              BOOLEAN NOT NULL DEFAULT FALSE,
            metadata_json           JSONB NOT NULL DEFAULT '{}',
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            status                  VARCHAR(30) NOT NULL DEFAULT 'DRAFT'
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_products_category ON products (category_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_products_is_active ON products (is_active)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_products_created_at ON products (created_at)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_product_status_history(conn, applied: list[str]) -> None:
    name = "product_status_history.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_status_history (
            id          VARCHAR(36) PRIMARY KEY,
            product_id  VARCHAR(255) NOT NULL REFERENCES products(id),
            from_status VARCHAR(30),
            to_status   VARCHAR(30) NOT NULL,
            reason      TEXT,
            changed_by  VARCHAR(36),
            changed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_prsh_product ON product_status_history (product_id, changed_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_product_media(conn, applied: list[str]) -> None:
    name = "product_media.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_media (
            id          VARCHAR(36) PRIMARY KEY,
            product_id  VARCHAR(255) NOT NULL REFERENCES products(id),
            media_type  VARCHAR(10) NOT NULL CHECK (media_type IN ('IMAGE','VIDEO','PDF','3D')),
            url         VARCHAR(500) NOT NULL,
            cdn_key     VARCHAR(255),
            alt_text    VARCHAR(255),
            sort_order  INTEGER NOT NULL DEFAULT 0,
            is_primary  BOOLEAN NOT NULL DEFAULT FALSE,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pm_product_sort ON product_media (product_id, sort_order, created_at DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pm_primary ON product_media (product_id, is_primary)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_product_barcodes(conn, applied: list[str]) -> None:
    name = "product_barcodes.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_barcodes (
            id            VARCHAR(36) PRIMARY KEY,
            product_id    VARCHAR(255) NOT NULL REFERENCES products(id),
            barcode_type  VARCHAR(20) NOT NULL,
            barcode_value VARCHAR(128) NOT NULL UNIQUE,
            is_primary    BOOLEAN NOT NULL DEFAULT FALSE,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT product_barcodes_barcode_type_check CHECK (
                barcode_type IN ('EAN13','EAN8','GTIN14','QR','CODE128','DATAMATRIX')
            )
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pb_product_type ON product_barcodes (product_id, barcode_type, created_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_product_inventory(conn, applied: list[str]) -> None:
    name = "product_inventory.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_inventory (
            id                  VARCHAR(36) PRIMARY KEY,
            product_id          VARCHAR(255) NOT NULL REFERENCES products(id),
            locker_id           VARCHAR(64) NOT NULL REFERENCES lockers(id),
            slot_size           VARCHAR(8) NOT NULL,
            quantity_on_hand    INTEGER NOT NULL DEFAULT 0,
            quantity_reserved   INTEGER NOT NULL DEFAULT 0,
            quantity_available  INTEGER GENERATED ALWAYS AS (quantity_on_hand - quantity_reserved) STORED,
            reorder_point       INTEGER NOT NULL DEFAULT 0,
            reorder_quantity    INTEGER NOT NULL DEFAULT 0,
            last_counted_at     TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(product_id, locker_id, slot_size)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pi_locker_available ON product_inventory (locker_id, quantity_available, updated_at DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pi_product_updated ON product_inventory (product_id, updated_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_inventory_movements(conn, applied: list[str]) -> None:
    name = "inventory_movements.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS inventory_movements (
            id              VARCHAR(36) PRIMARY KEY,
            product_id      VARCHAR(255) NOT NULL REFERENCES products(id),
            locker_id       VARCHAR(64) NOT NULL REFERENCES lockers(id),
            movement_type   VARCHAR(30) NOT NULL,
            quantity_delta  INTEGER NOT NULL,
            reference_id    VARCHAR(64),
            reference_type  VARCHAR(30),
            note            TEXT,
            occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by      VARCHAR(36),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_im_product_locker_occurred ON inventory_movements (product_id, locker_id, occurred_at DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_im_locker_occurred ON inventory_movements (locker_id, occurred_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_inventory_reservations(conn, applied: list[str]) -> None:
    name = "inventory_reservations.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS inventory_reservations (
            id          VARCHAR(36) PRIMARY KEY,
            order_id    VARCHAR(64) NOT NULL,
            product_id  VARCHAR(255) NOT NULL REFERENCES products(id),
            locker_id   VARCHAR(64) NOT NULL REFERENCES lockers(id),
            slot_size   VARCHAR(8) NOT NULL,
            quantity    INTEGER NOT NULL DEFAULT 1,
            expires_at  TIMESTAMPTZ NOT NULL,
            status      VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
            note        TEXT,
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ir_order_status ON inventory_reservations (order_id, status, updated_at DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ir_expiry_active ON inventory_reservations (expires_at) WHERE status = 'ACTIVE'"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_product_bundles(conn, applied: list[str]) -> None:
    name = "product_bundles.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_bundles (
            id           VARCHAR(36) PRIMARY KEY,
            name         VARCHAR(128) NOT NULL,
            code         VARCHAR(32) NOT NULL UNIQUE,
            description  TEXT,
            amount_cents INTEGER NOT NULL,
            currency     VARCHAR(8) NOT NULL DEFAULT 'BRL',
            bundle_type  VARCHAR(20) NOT NULL DEFAULT 'FIXED',
            is_active    BOOLEAN NOT NULL DEFAULT TRUE,
            valid_from   TIMESTAMPTZ,
            valid_until  TIMESTAMPTZ,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pb_active_window ON product_bundles (is_active, valid_from, valid_until)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_product_bundle_items(conn, applied: list[str]) -> None:
    name = "product_bundle_items.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_bundle_items (
            id               BIGSERIAL PRIMARY KEY,
            bundle_id        VARCHAR(36) NOT NULL REFERENCES product_bundles(id) ON DELETE CASCADE,
            product_id       VARCHAR(255) NOT NULL REFERENCES products(id),
            quantity         INTEGER NOT NULL DEFAULT 1,
            unit_price_cents INTEGER,
            sort_order       INTEGER NOT NULL DEFAULT 0
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pbi_bundle_sort ON product_bundle_items (bundle_id, sort_order)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_promotions(conn, applied: list[str]) -> None:
    name = "promotions.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS promotions (
            id               VARCHAR(36) PRIMARY KEY,
            code             VARCHAR(32) UNIQUE,
            name             VARCHAR(128) NOT NULL,
            type             VARCHAR(30) NOT NULL,
            discount_pct     NUMERIC(5,2),
            discount_cents   INTEGER,
            min_order_cents  INTEGER NOT NULL DEFAULT 0,
            max_discount_cents INTEGER,
            max_uses         INTEGER,
            uses_count       INTEGER NOT NULL DEFAULT 0,
            per_user_limit   INTEGER DEFAULT 1,
            conditions_json  JSONB NOT NULL DEFAULT '{}',
            is_active        BOOLEAN NOT NULL DEFAULT TRUE,
            valid_from       TIMESTAMPTZ NOT NULL,
            valid_until      TIMESTAMPTZ,
            created_by       VARCHAR(36),
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_promotions_active_window ON promotions (is_active, valid_from, valid_until)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_promotion_product_exclusions(conn, applied: list[str]) -> None:
    name = "promotion_product_exclusions.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS promotion_product_exclusions (
            promotion_id VARCHAR(36) NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
            product_id   VARCHAR(255) NOT NULL REFERENCES products(id),
            PRIMARY KEY (promotion_id, product_id)
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_promotion_campaigns(conn, applied: list[str]) -> None:
    name = "promotion_campaigns.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS promotion_campaigns (
            id               VARCHAR(36) PRIMARY KEY,
            code             VARCHAR(32) NOT NULL UNIQUE,
            name             VARCHAR(128) NOT NULL,
            description      TEXT,
            channel_family   VARCHAR(32) NOT NULL DEFAULT 'GENERAL',
            primary_country  VARCHAR(8),
            priority         INTEGER NOT NULL DEFAULT 100,
            max_stack_promotions INTEGER NOT NULL DEFAULT 1,
            is_active        BOOLEAN NOT NULL DEFAULT TRUE,
            valid_from       TIMESTAMPTZ NOT NULL,
            valid_until      TIMESTAMPTZ,
            metadata_json    JSONB NOT NULL DEFAULT '{}',
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_promo_campaigns_active "
        "ON promotion_campaigns (is_active, valid_from, valid_until)"
    ))

    _mark_migration(conn, name)
    applied.append(name)


def _create_promotion_scopes(conn, applied: list[str]) -> None:
    name = "promotion_scopes.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS promotion_scopes (
            id            VARCHAR(36) PRIMARY KEY,
            promotion_id  VARCHAR(36) NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
            scope_type    VARCHAR(32) NOT NULL,
            scope_value   VARCHAR(128) NOT NULL,
            mode          VARCHAR(16) NOT NULL DEFAULT 'INCLUDE',
            notes         VARCHAR(255),
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_promotion_scopes UNIQUE (promotion_id, scope_type, scope_value, mode)
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_promotion_scopes_promo "
        "ON promotion_scopes (promotion_id, scope_type)"
    ))

    _mark_migration(conn, name)
    applied.append(name)


def _create_promotion_product_inclusions(conn, applied: list[str]) -> None:
    name = "promotion_product_inclusions.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS promotion_product_inclusions (
            promotion_id VARCHAR(36) NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
            product_id   VARCHAR(255) NOT NULL REFERENCES products(id),
            PRIMARY KEY (promotion_id, product_id)
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_promotion_redemptions(conn, applied: list[str]) -> None:
    name = "promotion_redemptions.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS promotion_redemptions (
            id               VARCHAR(36) PRIMARY KEY,
            promotion_id     VARCHAR(36) NOT NULL REFERENCES promotions(id) ON DELETE RESTRICT,
            campaign_id      VARCHAR(36) REFERENCES promotion_campaigns(id) ON DELETE SET NULL,
            order_id         VARCHAR(64) NOT NULL,
            user_id          VARCHAR(36),
            partner_id       VARCHAR(36),
            channel_code     VARCHAR(32),
            country_code     VARCHAR(8),
            player_code      VARCHAR(64),
            discount_cents   INTEGER NOT NULL DEFAULT 0,
            currency         VARCHAR(8) NOT NULL DEFAULT 'BRL',
            idempotency_key  VARCHAR(64),
            redeemed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata_json    JSONB NOT NULL DEFAULT '{}'
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_promo_redemptions_promo_at "
        "ON promotion_redemptions (promotion_id, redeemed_at DESC)"
    ))
    conn.execute(text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_promo_redemptions_idem "
        "ON promotion_redemptions (idempotency_key) WHERE idempotency_key IS NOT NULL"
    ))

    _mark_migration(conn, name)
    applied.append(name)


def _create_promotion_audit_events(conn, applied: list[str]) -> None:
    name = "promotion_audit_events.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS promotion_audit_events (
            id              VARCHAR(36) PRIMARY KEY,
            entity_type     VARCHAR(32) NOT NULL,
            entity_id       VARCHAR(64) NOT NULL,
            action          VARCHAR(64) NOT NULL,
            actor_id        VARCHAR(36),
            correlation_id  VARCHAR(64),
            payload_json    JSONB NOT NULL DEFAULT '{}',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_promo_audit_entity "
        "ON promotion_audit_events (entity_type, entity_id, created_at DESC)"
    ))
    _mark_migration(conn, name)
    applied.append(name)


def _promotions_add_campaign_id(conn, applied: list[str]) -> None:
    name = "promotions.add_campaign_id_v1"
    if _migration_applied(conn, name):
        return
    _ensure_column(conn, "promotions", "campaign_id", "VARCHAR(36)")
    conn.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'fk_promotions_campaign_id'
            ) THEN
                ALTER TABLE promotions
                ADD CONSTRAINT fk_promotions_campaign_id
                FOREIGN KEY (campaign_id) REFERENCES promotion_campaigns(id) ON DELETE SET NULL;
            END IF;
        EXCEPTION WHEN undefined_table THEN
            NULL;
        END $$;
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS idx_promotions_campaign ON promotions (campaign_id)"
    ))
    _mark_migration(conn, name)
    applied.append(name)


def _create_products_cache(conn, applied: list[str]) -> None:
    name = "products_cache.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS products_cache (
            sku_id               VARCHAR(255) PRIMARY KEY,
            partner_id           VARCHAR(36),
            partner_sku          VARCHAR(255),
            name                 VARCHAR(255) NOT NULL,
            description          TEXT,
            category_id          VARCHAR(64) NOT NULL,
            amount_cents         INTEGER NOT NULL,
            currency             VARCHAR(8) NOT NULL DEFAULT 'BRL',
            width_mm             INTEGER,
            height_mm            INTEGER,
            depth_mm             INTEGER,
            weight_g             INTEGER,
            is_active            BOOLEAN NOT NULL DEFAULT TRUE,
            requires_signature   BOOLEAN NOT NULL DEFAULT FALSE,
            is_hazardous         BOOLEAN NOT NULL DEFAULT FALSE,
            temperature_zone     VARCHAR(32) NOT NULL DEFAULT 'AMBIENT',
            payload_json         JSONB,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            synced_at            TIMESTAMPTZ
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_products_cache_partner ON products_cache (partner_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_product_locker_configs(conn, applied: list[str]) -> None:
    name = "product_locker_configs.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_locker_configs (
            id                  BIGSERIAL PRIMARY KEY,
            locker_id           VARCHAR(64) NOT NULL REFERENCES lockers(id),
            category            VARCHAR(64) NOT NULL,
            subcategory         VARCHAR(64),
            allowed             BOOLEAN NOT NULL DEFAULT TRUE,
            temperature_zone    VARCHAR(32) NOT NULL DEFAULT 'ANY',
            min_value           DOUBLE PRECISION,
            max_value           DOUBLE PRECISION,
            max_weight_kg       DOUBLE PRECISION,
            max_width_cm        INTEGER,
            max_height_cm       INTEGER,
            max_depth_cm        INTEGER,
            requires_signature  BOOLEAN NOT NULL DEFAULT FALSE,
            requires_id         BOOLEAN NOT NULL DEFAULT FALSE,
            is_fragile          BOOLEAN NOT NULL DEFAULT FALSE,
            is_hazardous        BOOLEAN NOT NULL DEFAULT FALSE,
            priority            INTEGER NOT NULL DEFAULT 100,
            notes               TEXT,
            created_at          TIMESTAMPTZ NOT NULL,
            updated_at          TIMESTAMPTZ NOT NULL,
            min_value_cents     BIGINT,
            max_value_cents     BIGINT,
            max_weight_g        INTEGER,
            max_width_mm        INTEGER,
            max_height_mm       INTEGER,
            max_depth_mm        INTEGER,
            requires_id_check   BOOLEAN NOT NULL DEFAULT FALSE,
            UNIQUE(locker_id, category)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_product_cfg_locker ON product_locker_configs (locker_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_product_cfg_category ON product_locker_configs (category)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_dynamic_pricing_rules(conn, applied: list[str]) -> None:
    name = "dynamic_pricing_rules.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS dynamic_pricing_rules (
            id                VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
            rule_name         VARCHAR(128) NOT NULL,
            product_id        VARCHAR(255),
            category_id       VARCHAR(64) REFERENCES product_categories(id),
            locker_id         VARCHAR(36) REFERENCES lockers(id),
            rule_type         VARCHAR(30) NOT NULL,
            trigger_condition JSONB NOT NULL,
            adjustment_type   VARCHAR(20) NOT NULL,
            adjustment_value  NUMERIC(10,4) NOT NULL,
            min_price_cents   INTEGER,
            max_price_cents   INTEGER,
            priority          INTEGER DEFAULT 100,
            is_active         BOOLEAN DEFAULT TRUE,
            valid_from        TIMESTAMPTZ,
            valid_until       TIMESTAMPTZ,
            created_at        TIMESTAMPTZ DEFAULT NOW(),
            updated_at        TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_dpr_active ON dynamic_pricing_rules (is_active, valid_from, valid_until)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_price_history(conn, applied: list[str]) -> None:
    name = "price_history.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS price_history (
            id             BIGSERIAL PRIMARY KEY,
            product_id     VARCHAR(255) NOT NULL REFERENCES products(id),
            locker_id      VARCHAR(36) REFERENCES lockers(id),
            old_price_cents INTEGER NOT NULL,
            new_price_cents INTEGER NOT NULL,
            rule_id        VARCHAR(36) REFERENCES dynamic_pricing_rules(id),
            reason         VARCHAR(100),
            changed_at     TIMESTAMPTZ DEFAULT NOW(),
            changed_by     VARCHAR(36)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history (product_id, changed_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_product_recommendations(conn, applied: list[str]) -> None:
    name = "product_recommendations.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_recommendations (
            id           BIGSERIAL PRIMARY KEY,
            user_id      VARCHAR(36) REFERENCES users(id),
            locker_id    VARCHAR(36) REFERENCES lockers(id),
            product_id   VARCHAR(255) NOT NULL REFERENCES products(id),
            score        NUMERIC(5,4) NOT NULL,
            context      VARCHAR(50),
            generated_at TIMESTAMPTZ DEFAULT NOW(),
            expires_at   TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours'
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_product_recommendations_user ON product_recommendations (user_id, locker_id, score DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_product_recommendations_expires ON product_recommendations (expires_at)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_catalog_professional_tables(conn, applied: list[str]) -> None:
    """Taxonomias globais, listings por canal e atributos extensíveis (nível marketplace mundial)."""
    name = "catalog_professional.create_tables_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS category_taxonomy_mappings (
            id              VARCHAR(36) PRIMARY KEY,
            category_id     VARCHAR(64) NOT NULL REFERENCES product_categories(id) ON DELETE CASCADE,
            taxonomy_scheme VARCHAR(40) NOT NULL,
            external_code   VARCHAR(128) NOT NULL,
            external_name   VARCHAR(255),
            country_code    VARCHAR(3),
            is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
            metadata_json   JSONB NOT NULL DEFAULT '{}',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_category_taxonomy UNIQUE (category_id, taxonomy_scheme, external_code)
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_category_taxonomy_scheme "
        "ON category_taxonomy_mappings (taxonomy_scheme, external_code)"
    ))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_channel_listings (
            id                  VARCHAR(36) PRIMARY KEY,
            product_id          VARCHAR(255) NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            channel_code        VARCHAR(40) NOT NULL,
            external_sku        VARCHAR(255),
            external_category_id VARCHAR(128),
            listing_status      VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
            price_cents         INTEGER,
            currency            VARCHAR(8) NOT NULL DEFAULT 'BRL',
            partner_id          VARCHAR(36),
            sync_mode           VARCHAR(20) NOT NULL DEFAULT 'MANUAL',
            last_synced_at      TIMESTAMPTZ,
            metadata_json       JSONB NOT NULL DEFAULT '{}',
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_product_channel UNIQUE (product_id, channel_code),
            CONSTRAINT ck_pcl_listing_status CHECK (
                listing_status IN ('DRAFT', 'ACTIVE', 'SUSPENDED', 'DELISTED')
            ),
            CONSTRAINT ck_pcl_sync_mode CHECK (
                sync_mode IN ('MANUAL', 'API', 'FEED', 'WEBHOOK')
            )
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_product_channel_listings_channel "
        "ON product_channel_listings (channel_code, listing_status)"
    ))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_attribute_definitions (
            id               VARCHAR(36) PRIMARY KEY,
            category_id      VARCHAR(64) REFERENCES product_categories(id) ON DELETE CASCADE,
            attr_key         VARCHAR(64) NOT NULL,
            attr_label       VARCHAR(128) NOT NULL,
            data_type        VARCHAR(20) NOT NULL DEFAULT 'STRING',
            enum_values_json JSONB,
            is_required      BOOLEAN NOT NULL DEFAULT FALSE,
            sort_order       INTEGER NOT NULL DEFAULT 0,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_attr_def_category_key UNIQUE (category_id, attr_key),
            CONSTRAINT ck_attr_def_type CHECK (
                data_type IN ('STRING', 'INTEGER', 'BOOLEAN', 'ENUM', 'DECIMAL')
            )
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_attribute_values (
            id             VARCHAR(36) PRIMARY KEY,
            product_id     VARCHAR(255) NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            definition_id  VARCHAR(36) NOT NULL REFERENCES product_attribute_definitions(id) ON DELETE CASCADE,
            value_text     TEXT,
            value_number   NUMERIC(18,6),
            value_bool     BOOLEAN,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_product_attr_value UNIQUE (product_id, definition_id)
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_product_attr_values_product "
        "ON product_attribute_values (product_id)"
    ))

    _mark_migration(conn, name)
    applied.append(name)


def _create_global_players_registry(conn, applied: list[str]) -> None:
    """Registo mundial de players (redes locker, carriers, marketplaces, food, agregadores)."""
    name = "global_players.create_registry_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS global_players (
            code                    VARCHAR(40) PRIMARY KEY,
            name                    VARCHAR(128) NOT NULL,
            player_type             VARCHAR(32) NOT NULL,
            hq_country              VARCHAR(2) NOT NULL,
            supports_lockers        BOOLEAN NOT NULL DEFAULT FALSE,
            supports_pudo           BOOLEAN NOT NULL DEFAULT FALSE,
            supports_food_delivery  BOOLEAN NOT NULL DEFAULT FALSE,
            supports_marketplace    BOOLEAN NOT NULL DEFAULT FALSE,
            operator_id             VARCHAR(64),
            integration_modes_json  JSONB NOT NULL DEFAULT '[]',
            metadata_json           JSONB NOT NULL DEFAULT '{}',
            active                  BOOLEAN NOT NULL DEFAULT TRUE,
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_global_players_type ON global_players (player_type, active)"
    ))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS global_player_regions (
            id              VARCHAR(36) PRIMARY KEY,
            player_code     VARCHAR(40) NOT NULL REFERENCES global_players(code) ON DELETE CASCADE,
            country_code    VARCHAR(3) NOT NULL,
            region_code     VARCHAR(10),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_gpr_player_country UNIQUE (player_code, country_code)
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS global_player_capabilities (
            id              VARCHAR(36) PRIMARY KEY,
            player_code     VARCHAR(40) NOT NULL REFERENCES global_players(code) ON DELETE CASCADE,
            capability      VARCHAR(40) NOT NULL,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_gpc_player_cap UNIQUE (player_code, capability)
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS category_player_eligibility (
            id              VARCHAR(36) PRIMARY KEY,
            category_id     VARCHAR(64) NOT NULL REFERENCES product_categories(id) ON DELETE CASCADE,
            player_code     VARCHAR(40) NOT NULL REFERENCES global_players(code) ON DELETE CASCADE,
            eligibility     VARCHAR(20) NOT NULL DEFAULT 'ALLOWED',
            notes           TEXT,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_cpe_category_player UNIQUE (category_id, player_code)
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS global_player_integration_targets (
            id              VARCHAR(36) PRIMARY KEY,
            player_code     VARCHAR(40) NOT NULL REFERENCES global_players(code) ON DELETE CASCADE,
            target_type     VARCHAR(30) NOT NULL,
            target_key      VARCHAR(64) NOT NULL,
            metadata_json   JSONB NOT NULL DEFAULT '{}',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_gpit UNIQUE (player_code, target_type, target_key)
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_global_player_aliases_relations(conn, applied: list[str]) -> None:
    """Aliases canónicos e relações entre players (rede locker / marketplace / food)."""
    name = "global_players.aliases_relations_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS global_player_aliases (
            alias_code      VARCHAR(40) PRIMARY KEY,
            player_code     VARCHAR(40) NOT NULL REFERENCES global_players(code) ON DELETE CASCADE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_gpa_player ON global_player_aliases (player_code)"
    ))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS global_player_relations (
            id                  VARCHAR(36) PRIMARY KEY,
            from_player_code    VARCHAR(40) NOT NULL REFERENCES global_players(code) ON DELETE CASCADE,
            to_player_code      VARCHAR(40) NOT NULL REFERENCES global_players(code) ON DELETE CASCADE,
            relation_type       VARCHAR(32) NOT NULL,
            notes               TEXT,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_gpr_relation UNIQUE (from_player_code, to_player_code, relation_type)
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS promotion_player_eligibility (
            promotion_id        VARCHAR(36) NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
            player_code         VARCHAR(40) NOT NULL REFERENCES global_players(code) ON DELETE CASCADE,
            eligibility_mode    VARCHAR(16) NOT NULL DEFAULT 'INCLUDE',
            notes               VARCHAR(255),
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (promotion_id, player_code)
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_ppe_player ON promotion_player_eligibility (player_code)"
    ))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 5 — Parceiros
# ============================================================================

def _create_ecommerce_partners(conn, applied: list[str]) -> None:
    name = "ecommerce_partners.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ecommerce_partners (
            id                  VARCHAR(36) PRIMARY KEY,
            name                VARCHAR(128) NOT NULL,
            code                VARCHAR(32) NOT NULL UNIQUE,
            integration_type    VARCHAR(30) NOT NULL,
            api_base_url        VARCHAR(500),
            credentials_secret_ref VARCHAR(255),
            webhook_secret_ref  VARCHAR(255),
            revenue_share_pct   NUMERIC(6,4),
            currency            VARCHAR(8) NOT NULL DEFAULT 'BRL',
            sla_pickup_hours    INTEGER NOT NULL DEFAULT 72,
            active              BOOLEAN NOT NULL DEFAULT TRUE,
            country             VARCHAR(2) NOT NULL DEFAULT 'BR',
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            status              VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
            legal_name          VARCHAR(140),
            tax_id              VARCHAR(32),
            tier                VARCHAR(20) DEFAULT 'STANDARD',
            support_email       VARCHAR(128),
            support_phone       VARCHAR(32)
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_logistics_partners(conn, applied: list[str]) -> None:
    name = "logistics_partners.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS logistics_partners (
            id                      VARCHAR(36) PRIMARY KEY,
            name                    VARCHAR(128) NOT NULL,
            code                    VARCHAR(32) NOT NULL UNIQUE,
            integration_type        VARCHAR(30) NOT NULL,
            api_base_url            VARCHAR(500),
            tracking_url_template   VARCHAR(500),
            auth_type               VARCHAR(20),
            credentials_secret_ref  VARCHAR(255),
            default_sla_hours       INTEGER NOT NULL DEFAULT 72,
            reminder_hours_before   INTEGER NOT NULL DEFAULT 24,
            active                  BOOLEAN NOT NULL DEFAULT TRUE,
            country                 VARCHAR(2) NOT NULL DEFAULT 'BR',
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_status_history(conn, applied: list[str]) -> None:
    name = "partner_status_history.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_status_history (
            id           VARCHAR(36) PRIMARY KEY,
            partner_id   VARCHAR(36) NOT NULL,
            partner_type VARCHAR(20) NOT NULL,
            from_status  VARCHAR(30),
            to_status    VARCHAR(30) NOT NULL,
            reason       TEXT,
            changed_by   VARCHAR(36),
            changed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_psh_partner ON partner_status_history (partner_id, changed_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_contacts(conn, applied: list[str]) -> None:
    name = "partner_contacts.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_contacts (
            id           VARCHAR(36) PRIMARY KEY,
            partner_id   VARCHAR(36) NOT NULL,
            partner_type VARCHAR(20) NOT NULL,
            contact_type VARCHAR(20) NOT NULL,
            name         VARCHAR(128) NOT NULL,
            email        VARCHAR(128),
            phone        VARCHAR(32),
            is_primary   BOOLEAN NOT NULL DEFAULT FALSE,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pc_partner ON partner_contacts (partner_id, contact_type)"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_partner_contacts_primary_type ON partner_contacts (partner_id, partner_type, contact_type) WHERE is_primary = TRUE"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_sla_agreements(conn, applied: list[str]) -> None:
    name = "partner_sla_agreements.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_sla_agreements (
            id                VARCHAR(36) PRIMARY KEY,
            partner_id        VARCHAR(36) NOT NULL,
            partner_type      VARCHAR(20) NOT NULL,
            country           VARCHAR(2) NOT NULL DEFAULT 'BR',
            product_category  VARCHAR(64),
            sla_pickup_hours  INTEGER NOT NULL DEFAULT 72,
            sla_return_hours  INTEGER NOT NULL DEFAULT 24,
            penalty_pct       NUMERIC(5,2) DEFAULT 0,
            valid_from        DATE NOT NULL,
            valid_until       DATE,
            is_active         BOOLEAN NOT NULL DEFAULT TRUE,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_psa_partner_active ON partner_sla_agreements (partner_id, is_active)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_api_keys(conn, applied: list[str]) -> None:
    name = "partner_api_keys.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_api_keys (
            id           VARCHAR(36) PRIMARY KEY,
            partner_id   VARCHAR(36) NOT NULL,
            partner_type VARCHAR(20) NOT NULL,
            key_prefix   VARCHAR(16) NOT NULL,
            key_hash     VARCHAR(128) NOT NULL,
            label        VARCHAR(64),
            scopes_json  TEXT NOT NULL DEFAULT '[]',
            expires_at   TIMESTAMPTZ,
            last_used_at TIMESTAMPTZ,
            revoked_at   TIMESTAMPTZ,
            created_by   VARCHAR(36),
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pak_partner ON partner_api_keys (partner_id, partner_type)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_webhook_endpoints(conn, applied: list[str]) -> None:
    name = "partner_webhook_endpoints.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_webhook_endpoints (
            id           VARCHAR(36) PRIMARY KEY,
            partner_id   VARCHAR(36) NOT NULL,
            partner_type VARCHAR(20) NOT NULL,
            url          VARCHAR(500) NOT NULL,
            secret_hash  VARCHAR(128) NOT NULL,
            secret_key   VARCHAR(256),
            events_json  TEXT NOT NULL DEFAULT '["*"]',
            api_version  VARCHAR(10) NOT NULL DEFAULT 'v1',
            retry_policy TEXT NOT NULL DEFAULT '{}',
            active       BOOLEAN NOT NULL DEFAULT TRUE,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pwe_partner ON partner_webhook_endpoints (partner_id, partner_type)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_webhook_deliveries(conn, applied: list[str]) -> None:
    name = "partner_webhook_deliveries.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_webhook_deliveries (
            id                  VARCHAR(36) PRIMARY KEY,
            endpoint_id         VARCHAR(36) NOT NULL REFERENCES partner_webhook_endpoints(id),
            event_id            VARCHAR(36) NOT NULL,
            event_type          VARCHAR(80) NOT NULL,
            payload_json        TEXT NOT NULL DEFAULT '{}',
            payload_hash        VARCHAR(64),
            http_status         INTEGER,
            attempt_count       INTEGER NOT NULL DEFAULT 0,
            status              VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            last_error          TEXT,
            next_retry_at       TIMESTAMPTZ,
            processing_started_at TIMESTAMPTZ,
            delivered_at        TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pwd_status_retry ON partner_webhook_deliveries (status, next_retry_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pwd_endpoint ON partner_webhook_deliveries (endpoint_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_integration_health(conn, applied: list[str]) -> None:
    name = "partner_integration_health.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_integration_health (
            id              BIGSERIAL PRIMARY KEY,
            partner_id      VARCHAR(36) NOT NULL,
            partner_type    VARCHAR(20) NOT NULL,
            endpoint_url    VARCHAR(500),
            checked_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            status          VARCHAR(20) NOT NULL,
            latency_ms      INTEGER,
            http_status     INTEGER,
            error_message   VARCHAR(500)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pih_partner_time ON partner_integration_health (partner_id, checked_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_settlement_batches(conn, applied: list[str]) -> None:
    name = "partner_settlement_batches.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_settlement_batches (
            id                  VARCHAR(36) PRIMARY KEY,
            partner_id          VARCHAR(36) NOT NULL,
            partner_type        VARCHAR(20) NOT NULL DEFAULT 'ECOMMERCE',
            period_start        DATE NOT NULL,
            period_end          DATE NOT NULL,
            currency            VARCHAR(8) NOT NULL DEFAULT 'BRL',
            total_orders        INTEGER NOT NULL DEFAULT 0,
            gross_revenue_cents BIGINT NOT NULL DEFAULT 0,
            revenue_share_pct   NUMERIC(6,4) NOT NULL,
            revenue_share_cents BIGINT NOT NULL DEFAULT 0,
            fees_cents          BIGINT NOT NULL DEFAULT 0,
            net_amount_cents    BIGINT NOT NULL DEFAULT 0,
            status              VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
            settled_at          TIMESTAMPTZ,
            settlement_ref      VARCHAR(128),
            notes               TEXT,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_psb_partner_period ON partner_settlement_batches (partner_id, period_start, period_end)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_settlement_items(conn, applied: list[str]) -> None:
    name = "partner_settlement_items.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_settlement_items (
            id           BIGSERIAL PRIMARY KEY,
            batch_id     VARCHAR(36) NOT NULL REFERENCES partner_settlement_batches(id),
            order_id     VARCHAR(36) NOT NULL,
            order_date   TIMESTAMPTZ NOT NULL,
            gross_cents  BIGINT NOT NULL,
            share_pct    NUMERIC(6,4) NOT NULL,
            share_cents  BIGINT NOT NULL,
            currency     VARCHAR(8) NOT NULL DEFAULT 'BRL'
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_psi_batch ON partner_settlement_items (batch_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_service_areas(conn, applied: list[str]) -> None:
    name = "partner_service_areas.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_service_areas (
            id           VARCHAR(36) PRIMARY KEY,
            partner_id   VARCHAR(36) NOT NULL,
            partner_type VARCHAR(20) NOT NULL DEFAULT 'ECOMMERCE',
            locker_id    VARCHAR(36) NOT NULL REFERENCES lockers(id),
            priority     INTEGER NOT NULL DEFAULT 100,
            exclusive    BOOLEAN NOT NULL DEFAULT FALSE,
            valid_from   DATE NOT NULL,
            valid_until  DATE,
            is_active    BOOLEAN NOT NULL DEFAULT TRUE,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_psa_partner_locker_active ON partner_service_areas (partner_id, locker_id) WHERE is_active IS TRUE"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_performance_metrics(conn, applied: list[str]) -> None:
    name = "partner_performance_metrics.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_performance_metrics (
            id                 VARCHAR(36) PRIMARY KEY,
            partner_id         VARCHAR(36) NOT NULL,
            period_month       CHAR(7) NOT NULL,
            total_orders       INTEGER NOT NULL DEFAULT 0,
            on_time_pickup_pct NUMERIC(5,2),
            return_rate_pct    NUMERIC(5,2),
            avg_pickup_hours   NUMERIC(6,2),
            sla_compliance_pct NUMERIC(5,2),
            webhook_success_rate NUMERIC(5,2),
            generated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ppm_partner_month ON partner_performance_metrics (partner_id, period_month DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_order_events_outbox(conn, applied: list[str]) -> None:
    name = "partner_order_events_outbox.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_order_events_outbox (
            id              VARCHAR(36) PRIMARY KEY,
            partner_id      VARCHAR(36) NOT NULL,
            order_id        VARCHAR(36) NOT NULL,
            event_type      VARCHAR(50) NOT NULL,
            payload_json    JSONB NOT NULL DEFAULT '{}',
            api_version     VARCHAR(10) NOT NULL DEFAULT 'v1',
            status          VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            attempt_count   INTEGER NOT NULL DEFAULT 0,
            max_attempts    INTEGER NOT NULL DEFAULT 5,
            next_retry_at   TIMESTAMPTZ,
            last_error      TEXT,
            delivered_at    TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_poeo_status_retry ON partner_order_events_outbox (status, next_retry_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_poeo_partner_order ON partner_order_events_outbox (partner_id, order_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_billing_plans(conn, applied: list[str]) -> None:
    name = "partner_billing_plans.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_billing_plans (
            id                     VARCHAR(36) PRIMARY KEY,
            partner_id             VARCHAR(36) NOT NULL,
            partner_type           VARCHAR(20) NOT NULL,
            plan_name              VARCHAR(128) NOT NULL,
            billing_model          VARCHAR(30) NOT NULL,
            currency               VARCHAR(8) NOT NULL DEFAULT 'BRL',
            country_code           VARCHAR(2),
            jurisdiction_code      VARCHAR(32),
            timezone               VARCHAR(64) NOT NULL DEFAULT 'UTC',
            monthly_fee_cents      BIGINT,
            fee_per_delivery_cents BIGINT,
            fee_per_pickup_cents   BIGINT,
            fee_per_day_stored_cents BIGINT,
            free_storage_hours     INTEGER NOT NULL DEFAULT 72,
            revenue_share_pct      NUMERIC(6,4),
            min_monthly_fee_cents  BIGINT,
            included_deliveries_month INTEGER,
            overage_fee_cents      BIGINT,
            valid_from             DATE NOT NULL,
            valid_until            DATE,
            is_active              BOOLEAN NOT NULL DEFAULT TRUE,
            created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pbp_partner_active ON partner_billing_plans (partner_id, is_active)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_billing_cycles(conn, applied: list[str]) -> None:
    name = "partner_billing_cycles.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_billing_cycles (
            id                    VARCHAR(36) PRIMARY KEY,
            partner_id            VARCHAR(36) NOT NULL,
            locker_id             VARCHAR(36),
            partner_type          VARCHAR(20) NOT NULL,
            billing_plan_id       VARCHAR(36) NOT NULL REFERENCES partner_billing_plans(id),
            currency              VARCHAR(8) NOT NULL DEFAULT 'BRL',
            country_code          VARCHAR(2),
            jurisdiction_code     VARCHAR(32),
            period_timezone       VARCHAR(64) NOT NULL DEFAULT 'UTC',
            period_start          DATE NOT NULL,
            period_end            DATE NOT NULL,
            total_deliveries      INTEGER NOT NULL DEFAULT 0,
            total_pickups         INTEGER NOT NULL DEFAULT 0,
            total_slot_days       NUMERIC(10,2) NOT NULL DEFAULT 0,
            total_overdue_days    NUMERIC(10,2) NOT NULL DEFAULT 0,
            base_fee_cents        BIGINT NOT NULL DEFAULT 0,
            usage_fee_cents       BIGINT NOT NULL DEFAULT 0,
            overage_fee_cents     BIGINT NOT NULL DEFAULT 0,
            sla_penalty_cents     BIGINT NOT NULL DEFAULT 0,
            discount_cents        BIGINT NOT NULL DEFAULT 0,
            tax_cents             BIGINT NOT NULL DEFAULT 0,
            total_amount_cents    BIGINT NOT NULL DEFAULT 0,
            status                VARCHAR(20) NOT NULL DEFAULT 'OPEN',
            dedupe_key            VARCHAR(160),
            computed_at           TIMESTAMPTZ,
            approved_at           TIMESTAMPTZ,
            approved_by           VARCHAR(36),
            invoiced_at           TIMESTAMPTZ,
            paid_at               TIMESTAMPTZ,
            payment_ref           VARCHAR(128),
            dispute_reason        TEXT,
            notes                 TEXT,
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pbc_partner_period ON partner_billing_cycles (partner_id, period_start, period_end)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_billing_line_items(conn, applied: list[str]) -> None:
    name = "partner_billing_line_items.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_billing_line_items (
            id               BIGSERIAL PRIMARY KEY,
            cycle_id         VARCHAR(36) NOT NULL REFERENCES partner_billing_cycles(id) ON DELETE CASCADE,
            partner_id       VARCHAR(36) NOT NULL,
            locker_id        VARCHAR(36),
            line_type        VARCHAR(40) NOT NULL,
            description      VARCHAR(255) NOT NULL,
            reference_id     VARCHAR(36),
            reference_type   VARCHAR(40),
            reference_source VARCHAR(50) NOT NULL DEFAULT 'billing_engine',
            dedupe_key       VARCHAR(180),
            quantity         NUMERIC(12,4) NOT NULL DEFAULT 1,
            unit_price_cents BIGINT NOT NULL,
            total_cents      BIGINT NOT NULL,
            currency         VARCHAR(8) NOT NULL DEFAULT 'BRL',
            country_code     VARCHAR(2),
            jurisdiction_code VARCHAR(32),
            tax_code         VARCHAR(32),
            tax_rate_pct     NUMERIC(8,4),
            period_from      TIMESTAMPTZ,
            period_to        TIMESTAMPTZ,
            metadata_json    JSONB NOT NULL DEFAULT '{}',
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pbli_cycle ON partner_billing_line_items (cycle_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_b2b_invoices(conn, applied: list[str]) -> None:
    name = "partner_b2b_invoices.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_b2b_invoices (
            id                    VARCHAR(36) PRIMARY KEY,
            cycle_id              VARCHAR(36) NOT NULL UNIQUE REFERENCES partner_billing_cycles(id),
            partner_id            VARCHAR(36) NOT NULL,
            invoice_number        VARCHAR(50),
            invoice_series        VARCHAR(20),
            access_key            VARCHAR(140),
            document_type         VARCHAR(30) NOT NULL DEFAULT 'INVOICE',
            amount_cents          BIGINT NOT NULL,
            tax_cents             BIGINT NOT NULL DEFAULT 0,
            currency              VARCHAR(8) NOT NULL DEFAULT 'BRL',
            country_code          VARCHAR(2),
            jurisdiction_code     VARCHAR(32),
            timezone              VARCHAR(64) NOT NULL DEFAULT 'UTC',
            due_date              DATE,
            payment_method        VARCHAR(30),
            emitter_tax_id        VARCHAR(32),
            emitter_name          VARCHAR(140),
            taker_tax_id          VARCHAR(32),
            taker_name            VARCHAR(140),
            taker_email           VARCHAR(128),
            status                VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
            dedupe_key            VARCHAR(180),
            external_provider_ref VARCHAR(140),
            issued_at             TIMESTAMPTZ,
            sent_at               TIMESTAMPTZ,
            viewed_at             TIMESTAMPTZ,
            paid_at               TIMESTAMPTZ,
            cancelled_at          TIMESTAMPTZ,
            cancel_reason         TEXT,
            pdf_url               VARCHAR(500),
            xml_content           JSONB,
            government_response   JSONB,
            metadata_json         JSONB NOT NULL DEFAULT '{}',
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pbi_partner_status ON partner_b2b_invoices (partner_id, status)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_credit_notes(conn, applied: list[str]) -> None:
    name = "partner_credit_notes.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_credit_notes (
            id                  VARCHAR(36) PRIMARY KEY,
            partner_id          VARCHAR(36) NOT NULL,
            original_invoice_id VARCHAR(36) REFERENCES partner_b2b_invoices(id),
            cycle_id            VARCHAR(36) REFERENCES partner_billing_cycles(id),
            reason_code         VARCHAR(40) NOT NULL,
            description         TEXT NOT NULL,
            amount_cents        BIGINT NOT NULL,
            currency            VARCHAR(8) NOT NULL DEFAULT 'BRL',
            country_code        VARCHAR(2),
            jurisdiction_code   VARCHAR(32),
            timezone            VARCHAR(64) NOT NULL DEFAULT 'UTC',
            status              VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            dedupe_key          VARCHAR(180),
            approved_by         VARCHAR(36),
            approved_at         TIMESTAMPTZ,
            applied_to_cycle_id VARCHAR(36),
            applied_at          TIMESTAMPTZ,
            expires_at          TIMESTAMPTZ,
            dispute_ref         VARCHAR(140),
            metadata_json       JSONB NOT NULL DEFAULT '{}',
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pcn_partner_status ON partner_credit_notes (partner_id, status)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_payment_holds(conn, applied: list[str]) -> None:
    name = "partner_payment_holds.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_payment_holds (
            id                  VARCHAR(36) PRIMARY KEY,
            partner_id          VARCHAR(36) NOT NULL,
            invoice_id          VARCHAR(36) NOT NULL REFERENCES partner_b2b_invoices(id),
            hold_amount_cents   BIGINT NOT NULL,
            release_schedule    VARCHAR(30) NOT NULL DEFAULT 'AFTER_15_DAYS',
            released_at         TIMESTAMPTZ,
            released_amount_cents BIGINT,
            dispute_opened_at   TIMESTAMPTZ,
            dispute_resolved_at TIMESTAMPTZ,
            dispute_result      VARCHAR(20),
            status              VARCHAR(20) NOT NULL DEFAULT 'HELD',
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_partner_payment_holds_partner_status ON partner_payment_holds (partner_id, status)"))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 6 — Logística
# ============================================================================

def _create_inbound_deliveries(conn, applied: list[str]) -> None:
    name = "inbound_deliveries.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS inbound_deliveries (
            id                  VARCHAR(36) PRIMARY KEY,
            logistics_partner_id VARCHAR(36) NOT NULL REFERENCES logistics_partners(id),
            locker_id           VARCHAR(36) NOT NULL REFERENCES lockers(id),
            slot_label          VARCHAR(20),
            tracking_code       VARCHAR(128) NOT NULL,
            barcode             VARCHAR(128),
            partner_order_ref   VARCHAR(128),
            recipient_name      VARCHAR(255),
            recipient_document  VARCHAR(32),
            recipient_phone     VARCHAR(32),
            recipient_email     VARCHAR(128),
            weight_g            INTEGER,
            width_mm            INTEGER,
            height_mm           INTEGER,
            depth_mm            INTEGER,
            declared_value_cents INTEGER,
            currency            VARCHAR(8) NOT NULL DEFAULT 'BRL',
            requires_signature  BOOLEAN NOT NULL DEFAULT FALSE,
            requires_id_check   BOOLEAN NOT NULL DEFAULT FALSE,
            status              VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            stored_at           TIMESTAMPTZ,
            first_notified_at   TIMESTAMPTZ,
            last_notified_at    TIMESTAMPTZ,
            notification_count  INTEGER NOT NULL DEFAULT 0,
            pickup_deadline_at  TIMESTAMPTZ,
            picked_up_at        TIMESTAMPTZ,
            returned_at         TIMESTAMPTZ,
            return_reason       VARCHAR(255),
            pickup_token_id     VARCHAR(36),
            carrier_payload_json JSONB,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_inbound_tracking ON inbound_deliveries (logistics_partner_id, tracking_code)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_inbound_locker_status ON inbound_deliveries (locker_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_inbound_deadline ON inbound_deliveries (pickup_deadline_at) WHERE status NOT IN ('PICKED_UP', 'RETURNED')"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_logistics_tracking_events(conn, applied: list[str]) -> None:
    name = "logistics_tracking_events.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS logistics_tracking_events (
            id               VARCHAR(36) PRIMARY KEY,
            delivery_id      VARCHAR(36) NOT NULL REFERENCES inbound_deliveries(id),
            event_code       VARCHAR(40) NOT NULL,
            event_label      VARCHAR(120) NOT NULL,
            raw_status       VARCHAR(80),
            location_city    VARCHAR(80),
            location_state   VARCHAR(80),
            location_country VARCHAR(2),
            occurred_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            source           VARCHAR(40) NOT NULL DEFAULT 'CARRIER_WEBHOOK',
            source_ref       VARCHAR(128),
            payload_json     TEXT NOT NULL DEFAULT '{}',
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lte_delivery_time ON logistics_tracking_events (delivery_id, occurred_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_logistics_delivery_attempts(conn, applied: list[str]) -> None:
    name = "logistics_delivery_attempts.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS logistics_delivery_attempts (
            id              VARCHAR(36) PRIMARY KEY,
            delivery_id     VARCHAR(36) NOT NULL REFERENCES inbound_deliveries(id),
            attempt_number  INTEGER NOT NULL,
            status          VARCHAR(20) NOT NULL,
            attempted_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            failure_reason  VARCHAR(160),
            carrier_note    TEXT,
            carrier_agent   VARCHAR(128),
            proof_url       VARCHAR(500),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(delivery_id, attempt_number)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lda_delivery_time ON logistics_delivery_attempts (delivery_id, attempted_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_logistics_shipment_labels(conn, applied: list[str]) -> None:
    name = "logistics_shipment_labels.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS logistics_shipment_labels (
            id            VARCHAR(36) PRIMARY KEY,
            delivery_id   VARCHAR(36) NOT NULL REFERENCES inbound_deliveries(id),
            carrier_code  VARCHAR(20) NOT NULL,
            tracking_code VARCHAR(128) NOT NULL UNIQUE,
            label_format  VARCHAR(10) NOT NULL DEFAULT 'PDF',
            label_url     VARCHAR(500),
            label_payload TEXT NOT NULL DEFAULT '{}',
            status        VARCHAR(20) NOT NULL DEFAULT 'GENERATED',
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at    TIMESTAMPTZ
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lsl_delivery ON logistics_shipment_labels (delivery_id, created_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_logistics_carrier_auth_config(conn, applied: list[str]) -> None:
    name = "logistics_carrier_auth_config.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS logistics_carrier_auth_config (
            id               VARCHAR(36) PRIMARY KEY,
            carrier_code     VARCHAR(20) NOT NULL UNIQUE,
            signature_header VARCHAR(64) NOT NULL DEFAULT 'X-Carrier-Signature',
            algorithm        VARCHAR(20) NOT NULL DEFAULT 'HMAC_SHA256',
            secret_key       VARCHAR(256),
            required         BOOLEAN NOT NULL DEFAULT FALSE,
            active           BOOLEAN NOT NULL DEFAULT TRUE,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_logistics_carrier_status_map(conn, applied: list[str]) -> None:
    name = "logistics_carrier_status_map.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS logistics_carrier_status_map (
            id                    VARCHAR(36) PRIMARY KEY,
            carrier_code          VARCHAR(20) NOT NULL,
            raw_status            VARCHAR(80) NOT NULL,
            normalized_event_code VARCHAR(40) NOT NULL,
            normalized_event_label VARCHAR(120) NOT NULL,
            normalized_outcome    VARCHAR(20),
            active                BOOLEAN NOT NULL DEFAULT TRUE,
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(carrier_code, raw_status)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lcsm_carrier ON logistics_carrier_status_map (carrier_code, active)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_logistics_returns(conn, applied: list[str]) -> None:
    name = "logistics_returns.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS logistics_returns (
            id          VARCHAR(36) PRIMARY KEY,
            order_id    VARCHAR(36) NOT NULL,
            partner_id  VARCHAR(36) NOT NULL,
            reason_code VARCHAR(40) NOT NULL,
            status      VARCHAR(30) NOT NULL DEFAULT 'REQUESTED',
            notes       TEXT,
            created_by  VARCHAR(36),
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lr_partner_status_created ON logistics_returns (partner_id, status, created_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_logistics_return_events(conn, applied: list[str]) -> None:
    name = "logistics_return_events.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS logistics_return_events (
            id          VARCHAR(36) PRIMARY KEY,
            return_id   VARCHAR(36) NOT NULL REFERENCES logistics_returns(id),
            from_status VARCHAR(30),
            to_status   VARCHAR(30) NOT NULL,
            reason      VARCHAR(200),
            changed_by  VARCHAR(36),
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lre_return_occurred ON logistics_return_events (return_id, occurred_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_return_reasons_catalog(conn, applied: list[str]) -> None:
    name = "return_reasons_catalog.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS return_reasons_catalog (
            id              VARCHAR(36) PRIMARY KEY,
            code            VARCHAR(30) NOT NULL UNIQUE,
            label_pt        VARCHAR(128) NOT NULL,
            label_en        VARCHAR(128),
            category        VARCHAR(30),
            requires_photo  BOOLEAN NOT NULL DEFAULT FALSE,
            requires_detail BOOLEAN NOT NULL DEFAULT FALSE,
            is_active       BOOLEAN NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_return_requests(conn, applied: list[str]) -> None:
    name = "return_requests.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS return_requests (
            id                    VARCHAR(36) PRIMARY KEY,
            original_delivery_id  VARCHAR(36) NOT NULL REFERENCES inbound_deliveries(id),
            locker_id             VARCHAR(64) REFERENCES lockers(id),
            requester_type        VARCHAR(20) NOT NULL,
            requester_id          VARCHAR(36),
            return_reason_code    VARCHAR(30) NOT NULL,
            return_reason_detail  TEXT,
            photo_url             VARCHAR(500),
            status                VARCHAR(30) NOT NULL DEFAULT 'REQUESTED',
            requested_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            approved_at           TIMESTAMPTZ,
            approved_by           VARCHAR(36),
            closed_at             TIMESTAMPTZ,
            close_reason          VARCHAR(255),
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_rr_status_requested ON return_requests (status, requested_at DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_rr_delivery_created ON return_requests (original_delivery_id, created_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_return_legs(conn, applied: list[str]) -> None:
    name = "return_legs.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS return_legs (
            id                    VARCHAR(36) PRIMARY KEY,
            return_request_id     VARCHAR(36) NOT NULL REFERENCES return_requests(id),
            logistics_partner_id  VARCHAR(36) REFERENCES logistics_partners(id),
            tracking_code         VARCHAR(128),
            label_id              VARCHAR(36) REFERENCES logistics_shipment_labels(id),
            from_locker_id        VARCHAR(64) REFERENCES lockers(id),
            to_hub_address_json   TEXT NOT NULL DEFAULT '{}',
            status                VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            shipped_at            TIMESTAMPTZ,
            received_at           TIMESTAMPTZ,
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_rl_return_status ON return_legs (return_request_id, status)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_return_tracking_events(conn, applied: list[str]) -> None:
    name = "return_tracking_events.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS return_tracking_events (
            id            VARCHAR(36) PRIMARY KEY,
            return_leg_id VARCHAR(36) NOT NULL REFERENCES return_legs(id),
            event_code    VARCHAR(30) NOT NULL,
            description   VARCHAR(255),
            location_name VARCHAR(128),
            occurred_at   TIMESTAMPTZ NOT NULL,
            source        VARCHAR(20) NOT NULL DEFAULT 'CARRIER_WEBHOOK',
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_rte_leg_time ON return_tracking_events (return_leg_id, occurred_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_sla_breach_events(conn, applied: list[str]) -> None:
    name = "sla_breach_events.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sla_breach_events (
            id                   VARCHAR(36) PRIMARY KEY,
            delivery_id          VARCHAR(36) REFERENCES inbound_deliveries(id),
            return_request_id    VARCHAR(36) REFERENCES return_requests(id),
            logistics_partner_id VARCHAR(36) REFERENCES logistics_partners(id),
            breach_type          VARCHAR(40) NOT NULL,
            severity             VARCHAR(10) NOT NULL,
            expected_at          TIMESTAMPTZ NOT NULL,
            detected_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            notified_at          TIMESTAMPTZ,
            resolved_at          TIMESTAMPTZ,
            notes                TEXT
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sbe_detected ON sla_breach_events (detected_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_logistics_manifests(conn, applied: list[str]) -> None:
    name = "logistics_manifests.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS logistics_manifests (
            id                    VARCHAR(36) PRIMARY KEY,
            logistics_partner_id  VARCHAR(36) NOT NULL REFERENCES logistics_partners(id),
            locker_id             VARCHAR(64) NOT NULL REFERENCES lockers(id),
            manifest_date         DATE NOT NULL,
            carrier_route_code    VARCHAR(64),
            carrier_vehicle_id    VARCHAR(64),
            expected_parcel_count INTEGER NOT NULL DEFAULT 0,
            actual_parcel_count   INTEGER NOT NULL DEFAULT 0,
            status                VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            dispatched_at         TIMESTAMPTZ,
            delivered_at          TIMESTAMPTZ,
            carrier_note          TEXT,
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lm_partner_date ON logistics_manifests (logistics_partner_id, manifest_date DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_logistics_manifest_items(conn, applied: list[str]) -> None:
    name = "logistics_manifest_items.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS logistics_manifest_items (
            id              BIGSERIAL PRIMARY KEY,
            manifest_id     VARCHAR(36) NOT NULL REFERENCES logistics_manifests(id),
            delivery_id     VARCHAR(36) REFERENCES inbound_deliveries(id),
            tracking_code   VARCHAR(128) NOT NULL,
            sequence_number INTEGER,
            status          VARCHAR(20) NOT NULL DEFAULT 'EXPECTED',
            exception_note  TEXT,
            processed_at    TIMESTAMPTZ
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lmi_manifest ON logistics_manifest_items (manifest_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_logistics_capacity_allocations(conn, applied: list[str]) -> None:
    name = "logistics_capacity_allocations.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS logistics_capacity_allocations (
            id                   VARCHAR(36) PRIMARY KEY,
            logistics_partner_id VARCHAR(36) NOT NULL REFERENCES logistics_partners(id),
            locker_id            VARCHAR(64) NOT NULL REFERENCES lockers(id),
            slot_size            VARCHAR(8) NOT NULL,
            reserved_slots       INTEGER NOT NULL,
            valid_from           DATE NOT NULL,
            valid_until          DATE,
            priority             INTEGER NOT NULL DEFAULT 100,
            notes                TEXT,
            is_active            BOOLEAN NOT NULL DEFAULT TRUE,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lca_partner_locker_slot ON logistics_capacity_allocations (logistics_partner_id, locker_id, slot_size)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_logistics_carrier_rates(conn, applied: list[str]) -> None:
    name = "logistics_carrier_rates.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS logistics_carrier_rates (
            id                VARCHAR(36) PRIMARY KEY,
            carrier_code      VARCHAR(20) NOT NULL,
            origin_zone       VARCHAR(10) NOT NULL,
            destination_zone  VARCHAR(10) NOT NULL,
            weight_tier_g     INTEGER NOT NULL,
            size_tier         VARCHAR(8),
            amount_cents      INTEGER NOT NULL,
            currency          VARCHAR(8) NOT NULL DEFAULT 'BRL',
            valid_from        DATE NOT NULL,
            valid_until       DATE,
            is_active         BOOLEAN NOT NULL DEFAULT TRUE,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_lcr_lookup ON logistics_carrier_rates (carrier_code, origin_zone, destination_zone, is_active)"))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 7 — Fulfillment
# ============================================================================

def _create_fulfillment_centers(conn, applied: list[str]) -> None:
    name = "fulfillment_centers.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fulfillment_centers (
            id              VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
            name            VARCHAR(128) NOT NULL,
            code            VARCHAR(32) NOT NULL UNIQUE,
            address_line    VARCHAR(255) NOT NULL,
            city            VARCHAR(100) NOT NULL,
            state           VARCHAR(50) NOT NULL,
            postal_code     VARCHAR(20) NOT NULL,
            country         VARCHAR(2) DEFAULT 'BR',
            latitude        NUMERIC(10,8),
            longitude       NUMERIC(11,8),
            capacity_slots  INTEGER DEFAULT 0,
            active          BOOLEAN DEFAULT TRUE,
            created_at      TIMESTAMPTZ DEFAULT NOW(),
            updated_at      TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_fulfillment_inventory(conn, applied: list[str]) -> None:
    name = "fulfillment_inventory.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fulfillment_inventory (
            id                  BIGSERIAL PRIMARY KEY,
            fulfillment_center_id VARCHAR(36) NOT NULL REFERENCES fulfillment_centers(id),
            product_id          VARCHAR(255) NOT NULL,
            quantity_on_hand    INTEGER NOT NULL DEFAULT 0,
            quantity_reserved   INTEGER NOT NULL DEFAULT 0,
            quantity_available  INTEGER GENERATED ALWAYS AS (quantity_on_hand - quantity_reserved) STORED,
            reorder_point       INTEGER DEFAULT 0,
            last_restocked_at   TIMESTAMPTZ,
            created_at          TIMESTAMPTZ DEFAULT NOW(),
            updated_at          TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(fulfillment_center_id, product_id)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fulfillment_inventory_center ON fulfillment_inventory (fulfillment_center_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_fulfillment_orders(conn, applied: list[str]) -> None:
    name = "fulfillment_orders.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fulfillment_orders (
            id                    VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id              VARCHAR(36) NOT NULL REFERENCES orders(id),
            fulfillment_center_id VARCHAR(36) NOT NULL REFERENCES fulfillment_centers(id),
            status                VARCHAR(30) NOT NULL DEFAULT 'PENDING',
            priority              INTEGER DEFAULT 100,
            picked_at             TIMESTAMPTZ,
            packed_at             TIMESTAMPTZ,
            shipped_at            TIMESTAMPTZ,
            delivered_to_locker_at TIMESTAMPTZ,
            tracking_code         VARCHAR(128),
            carrier               VARCHAR(50),
            created_at            TIMESTAMPTZ DEFAULT NOW(),
            updated_at            TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fulfillment_orders_order ON fulfillment_orders (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fulfillment_orders_center ON fulfillment_orders (fulfillment_center_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_omnichannel_orders(conn, applied: list[str]) -> None:
    name = "omnichannel_orders.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS omnichannel_orders (
            id           VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id     VARCHAR(36) NOT NULL UNIQUE REFERENCES orders(id),
            store_id     VARCHAR(36) NOT NULL REFERENCES partner_stores(id),
            pickup_type  VARCHAR(20) NOT NULL DEFAULT 'STORE_PICKUP',
            status       VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            ready_at     TIMESTAMPTZ,
            picked_up_at TIMESTAMPTZ,
            created_at   TIMESTAMPTZ DEFAULT NOW(),
            updated_at   TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_omnichannel_orders_store ON omnichannel_orders (store_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_omnichannel_orders_status ON omnichannel_orders (status, created_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_partner_stores(conn, applied: list[str]) -> None:
    name = "partner_stores.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS partner_stores (
            id               VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
            name             VARCHAR(128) NOT NULL,
            legal_name       VARCHAR(140),
            tax_id           VARCHAR(32) UNIQUE,
            address_line     VARCHAR(255) NOT NULL,
            city             VARCHAR(100) NOT NULL,
            state            VARCHAR(50) NOT NULL,
            postal_code      VARCHAR(20) NOT NULL,
            phone            VARCHAR(32),
            email            VARCHAR(128),
            latitude         NUMERIC(10,8),
            longitude        NUMERIC(11,8),
            operating_hours  JSONB,
            commission_pct   NUMERIC(5,2) DEFAULT 5.00,
            active           BOOLEAN DEFAULT TRUE,
            created_at       TIMESTAMPTZ DEFAULT NOW(),
            updated_at       TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_partner_stores_active ON partner_stores (active)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_store_inventory(conn, applied: list[str]) -> None:
    name = "store_inventory.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS store_inventory (
            id           BIGSERIAL PRIMARY KEY,
            store_id     VARCHAR(36) NOT NULL REFERENCES partner_stores(id),
            product_id   VARCHAR(255) NOT NULL,
            quantity     INTEGER DEFAULT 0,
            price_cents  INTEGER,
            last_sync_at TIMESTAMPTZ,
            created_at   TIMESTAMPTZ DEFAULT NOW(),
            updated_at   TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(store_id, product_id)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_store_inventory_store ON store_inventory (store_id)"))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 8 — Pedidos e Pagamentos
# ============================================================================

def _create_orders(conn, applied: list[str]) -> None:
    name = "orders.create_table_v4"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS orders (
            id                      VARCHAR(36) PRIMARY KEY,
            channel                 ORDERCHANNEL NOT NULL,
            user_id                 VARCHAR(36) REFERENCES users(id),
            region                  VARCHAR(10) NOT NULL,
            totem_id                VARCHAR(36) NOT NULL,
            amount_cents            INTEGER NOT NULL,
            currency                VARCHAR(8) NOT NULL DEFAULT 'EUR',
            status                  ORDERSTATUS NOT NULL,
            created_at              TIMESTAMPTZ NOT NULL,
            paid_at                 TIMESTAMPTZ,
            pickup_deadline_at      TIMESTAMPTZ,
            picked_up_at            TIMESTAMPTZ,
            guest_contact_email     TEXT,
            guest_contact_phone     TEXT,
            guest_marketing_opt_in  BOOLEAN NOT NULL DEFAULT FALSE,
            guest_session_id        TEXT,
            allocated_at            TIMESTAMPTZ,
            expires_at              TIMESTAMPTZ,
            customer_notes          TEXT,
            staff_notes             TEXT,
            channel_order_id        VARCHAR(100),
            kiosk_id                VARCHAR(100),
            allocated_by            VARCHAR(36),
            sku_id                  VARCHAR(255) NOT NULL DEFAULT '',
            gateway_transaction_id  VARCHAR(255),
            payment_method          PAYMENTMETHOD,
            payment_status          PAYMENTSTATUS NOT NULL,
            card_type               CARDTYPE,
            payment_updated_at      TIMESTAMPTZ,
            public_access_token_hash VARCHAR(255),
            receipt_email           VARCHAR(255),
            receipt_phone           VARCHAR(32),
            consent_marketing       INTEGER NOT NULL DEFAULT 0,
            guest_phone             VARCHAR(32),
            guest_email             VARCHAR(255),
            updated_at              TIMESTAMPTZ NOT NULL,
            site_id                 VARCHAR(100),
            tenant_id               VARCHAR(100),
            ecommerce_partner_id    VARCHAR(100),
            partner_order_ref       VARCHAR(255),
            sku_description         TEXT,
            slot_size               VARCHAR(20),
            card_last4              VARCHAR(8),
            card_brand              VARCHAR(50),
            installments            INTEGER,
            guest_name              VARCHAR(255),
            consent_analytics       BOOLEAN NOT NULL DEFAULT FALSE,
            cancelled_at            TIMESTAMPTZ,
            cancel_reason           VARCHAR(255),
            refunded_at             TIMESTAMPTZ,
            refund_reason           VARCHAR(255),
            payment_interface       VARCHAR(32),
            wallet_provider         VARCHAR(64),
            device_id               VARCHAR(128),
            ip_address              VARCHAR(64),
            user_agent              VARCHAR(500),
            idempotency_key         VARCHAR(255),
            order_metadata          JSONB,
            slot                    INTEGER,
            allocation_id           VARCHAR(36),
            allocation_expires_at   TIMESTAMPTZ,
            created_by              VARCHAR(36),
            updated_by              VARCHAR(36),
            deleted_at              TIMESTAMPTZ
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_created_at ON orders (created_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_status ON orders (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_user_id ON orders (user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_channel_status ON orders (channel, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_region_status ON orders (region, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_paid_at ON orders (paid_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_picked_up_at ON orders (picked_up_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_pickup_deadline ON orders (pickup_deadline_at) WHERE status NOT IN ('PICKED_UP','CANCELLED','REFUNDED','EXPIRED')"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_tenant_id ON orders (tenant_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_ecommerce_partner ON orders (ecommerce_partner_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_orders_partitioned(conn, applied: list[str]) -> None:
    """Tabela orders particionada por mês para escalabilidade."""
    name = "orders_partitioned.create_table_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS orders_partitioned (
            LIKE orders INCLUDING ALL
        ) PARTITION BY RANGE (created_at)
    """))

    # Criar função para criar partições futuras automaticamente
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION create_future_order_partitions()
        RETURNS VOID AS $$
        DECLARE
            future_months INT := 3;
            base_date DATE;
            partition_name TEXT;
            start_date DATE;
            end_date DATE;
        BEGIN
            FOR i IN 1..future_months LOOP
                base_date := DATE_TRUNC('month', CURRENT_DATE + (i || ' months')::INTERVAL);
                partition_name := 'orders_' || TO_CHAR(base_date, 'YYYY_MM');
                start_date := base_date;
                end_date := base_date + INTERVAL '1 month';
                
                EXECUTE format('
                    CREATE TABLE IF NOT EXISTS %I PARTITION OF orders_partitioned
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name, start_date, end_date
                );
            END LOOP;
        END;
        $$ LANGUAGE plpgsql
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_order_items(conn, applied: list[str]) -> None:
    name = "order_items.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS order_items (
            id                 BIGSERIAL PRIMARY KEY,
            order_id           VARCHAR(36) NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            sku_id             VARCHAR(255) NOT NULL,
            sku_description    TEXT,
            quantity           INTEGER NOT NULL DEFAULT 1,
            unit_amount_cents  BIGINT NOT NULL,
            total_amount_cents BIGINT NOT NULL,
            slot_preference    INTEGER,
            slot_size          VARCHAR(20),
            item_status        VARCHAR(32) NOT NULL DEFAULT 'PENDING',
            metadata_json      JSONB NOT NULL DEFAULT '{}',
            created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            ncm                VARCHAR(10)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_order_items_order_id ON order_items (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_order_items_sku_id ON order_items (sku_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_payment_transactions(conn, applied: list[str]) -> None:
    name = "payment_transactions.create_table_v2"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payment_transactions (
            id                      VARCHAR(36) PRIMARY KEY,
            order_id                VARCHAR(36) NOT NULL REFERENCES orders(id),
            gateway                 VARCHAR(50) NOT NULL,
            gateway_transaction_id  VARCHAR(128),
            gateway_idempotency_key VARCHAR(128),
            amount_cents            INTEGER NOT NULL,
            currency                VARCHAR(8) NOT NULL DEFAULT 'BRL',
            payment_method          VARCHAR(30) NOT NULL,
            card_brand              VARCHAR(20),
            card_last4              VARCHAR(4),
            card_type               VARCHAR(10),
            installments            INTEGER NOT NULL DEFAULT 1,
            nsu                     VARCHAR(50),
            authorization_code      VARCHAR(50),
            status                  VARCHAR(20) NOT NULL DEFAULT 'INITIATED',
            error_code              VARCHAR(100),
            error_message           TEXT,
            raw_request_json        TEXT,
            raw_response_json       TEXT,
            initiated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            approved_at             TIMESTAMPTZ,
            settled_at              TIMESTAMPTZ,
            refunded_at             TIMESTAMPTZ,
            refund_reason           VARCHAR(255),
            refund_amount_cents     INTEGER,
            chargeback_at           TIMESTAMPTZ,
            chargeback_reason       VARCHAR(255),
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            gateway_webhook_received_at TIMESTAMPTZ,
            gateway_webhook_payload JSONB,
            acquirer_name           VARCHAR(100),
            acquirer_message        TEXT,
            tid                     VARCHAR(50),
            arqc                    VARCHAR(50),
            nsu_sitef               VARCHAR(50),
            reconciliation_status   VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            reconciliation_batch_id VARCHAR(100),
            gateway_fee_cents       INTEGER DEFAULT 0,
            installment_fee_cents   INTEGER DEFAULT 0,
            net_amount_cents        INTEGER
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_payment_tx_order ON payment_transactions (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_payment_tx_status ON payment_transactions (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_payment_tx_gateway_id ON payment_transactions (gateway, gateway_transaction_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_payment_instructions(conn, applied: list[str]) -> None:
    name = "payment_instructions.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payment_instructions (
            id                     VARCHAR(36) PRIMARY KEY,
            order_id               VARCHAR(36) NOT NULL REFERENCES orders(id),
            instruction_type       VARCHAR(50) NOT NULL,
            amount_cents           INTEGER NOT NULL,
            currency               VARCHAR(8) NOT NULL DEFAULT 'BRL',
            status                 VARCHAR(30) NOT NULL DEFAULT 'PENDING',
            expires_at             TIMESTAMPTZ,
            qr_code                TEXT,
            qr_code_text           TEXT,
            barcode                VARCHAR(255),
            digitable_line         TEXT,
            authorization_code     VARCHAR(100),
            capture_amount_cents   INTEGER,
            captured_at            TIMESTAMPTZ,
            payment_token          VARCHAR(255),
            customer_payment_method_id VARCHAR(36),
            wallet_provider        VARCHAR(50),
            wallet_transaction_id  VARCHAR(255),
            created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            redirect_url           TEXT,
            provider_payment_id    TEXT,
            provider_name          TEXT
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_payment_instructions_order ON payment_instructions (order_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_payment_splits(conn, applied: list[str]) -> None:
    name = "payment_splits.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payment_splits (
            id             VARCHAR(36) PRIMARY KEY,
            order_id       VARCHAR(36) NOT NULL REFERENCES orders(id),
            recipient_type VARCHAR(30) NOT NULL,
            recipient_id   VARCHAR(128) NOT NULL,
            amount_cents   INTEGER NOT NULL,
            percentage     NUMERIC(5,2),
            status         VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            settled_at     TIMESTAMPTZ,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_payment_splits_order ON payment_splits (order_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_saved_payment_methods(conn, applied: list[str]) -> None:
    name = "saved_payment_methods.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS saved_payment_methods (
            id               VARCHAR(36) PRIMARY KEY,
            user_id          VARCHAR(36) NOT NULL REFERENCES users(id),
            method_code      VARCHAR(80) NOT NULL,
            gateway_token    VARCHAR(255) NOT NULL,
            last4            VARCHAR(4),
            card_brand       VARCHAR(50),
            cardholder_name  VARCHAR(255),
            expiry_month     INTEGER,
            expiry_year      INTEGER,
            is_default       BOOLEAN NOT NULL DEFAULT FALSE,
            is_active        BOOLEAN NOT NULL DEFAULT TRUE,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_saved_payment_methods_user ON saved_payment_methods (user_id, is_active)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_credits(conn, applied: list[str]) -> None:
    name = "credits.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS credits (
            id            TEXT PRIMARY KEY,
            order_id      TEXT NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
            user_id       TEXT NOT NULL REFERENCES users(id),
            type          TEXT NOT NULL,
            amount_cents  INTEGER NOT NULL,
            currency      TEXT NOT NULL DEFAULT 'EUR',
            created_at    BIGINT NOT NULL,
            meta_json     JSONB NOT NULL DEFAULT '{}',
            status        CREDITSTATUS NOT NULL DEFAULT 'AVAILABLE',
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at    TIMESTAMPTZ,
            used_at       TIMESTAMPTZ,
            revoked_at    TIMESTAMPTZ,
            source_type   VARCHAR(50),
            source_reason VARCHAR(255),
            notes         TEXT
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_credits_user_id ON credits (user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_credits_status ON credits (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_credits_expires_at ON credits (expires_at)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_financial_ledger(conn, applied: list[str]) -> None:
    name = "financial_ledger.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS financial_ledger (
            id                    VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
            order_id              VARCHAR(36) REFERENCES orders(id),
            payment_transaction_id VARCHAR(36) REFERENCES payment_transactions(id),
            wallet_id             VARCHAR(36) REFERENCES user_wallets(id),
            entry_type            VARCHAR(30) NOT NULL,
            amount_cents          BIGINT NOT NULL,
            currency              VARCHAR(8) NOT NULL DEFAULT 'BRL',
            status                VARCHAR(20) NOT NULL DEFAULT 'POSTED',
            external_reference    VARCHAR(100),
            metadata              JSONB DEFAULT '{}',
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_financial_ledger_order ON financial_ledger (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_financial_ledger_entry_type ON financial_ledger (entry_type)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_user_wallets(conn, applied: list[str]) -> None:
    name = "user_wallets.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS user_wallets (
            id                  VARCHAR(36) PRIMARY KEY,
            user_id             VARCHAR(36) NOT NULL UNIQUE REFERENCES users(id),
            balance_cents       BIGINT NOT NULL DEFAULT 0,
            currency            VARCHAR(8) NOT NULL DEFAULT 'BRL',
            status              VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
            last_transaction_at TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_wallets_user ON user_wallets (user_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_wallet_transactions(conn, applied: list[str]) -> None:
    name = "wallet_transactions.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS wallet_transactions (
            id                  VARCHAR(36) PRIMARY KEY,
            wallet_id           VARCHAR(36) NOT NULL REFERENCES user_wallets(id),
            order_id            VARCHAR(36) REFERENCES orders(id),
            type                VARCHAR(30) NOT NULL,
            amount_cents        BIGINT NOT NULL,
            balance_after_cents BIGINT NOT NULL,
            status              VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            external_reference  VARCHAR(255),
            description         TEXT,
            metadata            JSONB DEFAULT '{}',
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_wallet_transactions_wallet ON wallet_transactions (wallet_id, created_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 9 — Alocações e Pickups
# ============================================================================

def _create_allocations(conn, applied: list[str]) -> None:
    name = "allocations.create_table_v3"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS allocations (
            id              VARCHAR(36) PRIMARY KEY,
            order_id        VARCHAR(36) NOT NULL REFERENCES orders(id),
            locker_id       VARCHAR(36) REFERENCES lockers(id),
            slot            INTEGER NOT NULL,
            state           ALLOCATIONSTATE NOT NULL,
            locked_until    TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL,
            updated_at      TIMESTAMPTZ NOT NULL,
            allocated_at    TIMESTAMPTZ,
            released_at     TIMESTAMPTZ,
            release_reason  VARCHAR(255),
            slot_size       VARCHAR(20),
            ttl_seconds     INTEGER
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_allocations_order_id ON allocations (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_allocations_state ON allocations (state)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_allocations_locker_slot_state ON allocations (locker_id, slot, state)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_pickups(conn, applied: list[str]) -> None:
    name = "pickups.create_table_v4"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS pickups (
            id                  VARCHAR(36) PRIMARY KEY,
            order_id            VARCHAR(36) NOT NULL UNIQUE REFERENCES orders(id),
            channel             PICKUPCHANNEL NOT NULL,
            region              VARCHAR(10) NOT NULL,
            locker_id           VARCHAR(36),
            machine_id          VARCHAR(100),
            slot                VARCHAR(20),
            operator_id         VARCHAR(64),
            tenant_id           VARCHAR(100),
            site_id             VARCHAR(100),
            status              PICKUPSTATUS NOT NULL,
            lifecycle_stage     PICKUPLIFECYCLESTAGE NOT NULL,
            current_token_id    VARCHAR(36),
            activated_at        TIMESTAMPTZ NOT NULL,
            ready_at            TIMESTAMPTZ,
            expires_at          TIMESTAMPTZ,
            door_opened_at      TIMESTAMPTZ,
            item_removed_at     TIMESTAMPTZ,
            door_closed_at      TIMESTAMPTZ,
            redeemed_at         TIMESTAMPTZ,
            redeemed_via        PICKUPREDEEMVIA,
            expired_at          TIMESTAMPTZ,
            cancelled_at        TIMESTAMPTZ,
            cancel_reason       VARCHAR(255),
            correlation_id      VARCHAR(255),
            source_event_id     VARCHAR(255),
            sensor_event_id     VARCHAR(255),
            notes               VARCHAR(255),
            created_at          TIMESTAMPTZ NOT NULL,
            updated_at          TIMESTAMPTZ NOT NULL,
            machine_state       VARCHAR(50),
            pickup_phase        PICKUP_PHASE,
            evidence_score      INTEGER DEFAULT 0,
            evidence_strength   VARCHAR(10) DEFAULT 'NONE',
            dispute_state       DISPUTE_STATE NOT NULL DEFAULT 'NONE',
            verified_at         TIMESTAMPTZ,
            verified_by         VARCHAR(255),
            disputed_at         TIMESTAMPTZ,
            dispute_reason      TEXT,
            reconciled_at       TIMESTAMPTZ,
            reconciled_by       VARCHAR(255),
            aggregate_version   BIGINT NOT NULL DEFAULT 0,
            fraud_flag          BOOLEAN NOT NULL DEFAULT FALSE,
            fraud_reason        TEXT
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_order_id ON pickups (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_status ON pickups (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_pickup_phase ON pickups (pickup_phase)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_locker_status ON pickups (locker_id, status)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_pickup_tokens(conn, applied: list[str]) -> None:
    name = "pickup_tokens.create_table_v2"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS pickup_tokens (
            order_id              VARCHAR(36) NOT NULL PRIMARY KEY REFERENCES orders(id) ON DELETE CASCADE,
            secret                VARCHAR(255) NOT NULL,
            window_start_at       TIMESTAMPTZ NOT NULL,
            window_end_at         TIMESTAMPTZ NOT NULL,
            rotation_step_sec     INTEGER NOT NULL DEFAULT 600,
            created_at            TIMESTAMPTZ NOT NULL,
            id                    VARCHAR(36),
            pickup_id             VARCHAR(36) REFERENCES pickups(id),
            token_hash            VARCHAR(255),
            expires_at            TIMESTAMPTZ,
            used_at               TIMESTAMPTZ,
            is_active             BOOLEAN NOT NULL DEFAULT TRUE,
            manual_code           VARCHAR(255),
            manual_code_encrypted VARCHAR(255)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickup_tokens_pickup ON pickup_tokens (pickup_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickup_tokens_active ON pickup_tokens (pickup_id, is_active) WHERE is_active = TRUE"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_pickup_events(conn, applied: list[str]) -> None:
    name = "pickup_events.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS pickup_events (
            id              BIGSERIAL PRIMARY KEY,
            pickup_id       VARCHAR(36) NOT NULL REFERENCES pickups(id) ON DELETE CASCADE,
            version         BIGINT NOT NULL,
            event_type      VARCHAR(100) NOT NULL,
            payload         JSONB NOT NULL DEFAULT '{}',
            source          VARCHAR(100) NOT NULL DEFAULT 'migration',
            idempotency_key VARCHAR(255),
            occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_pickup_events_pickup_version ON pickup_events (pickup_id, version)"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_pickup_events_pickup_idempotency ON pickup_events (pickup_id, idempotency_key) WHERE idempotency_key IS NOT NULL"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_pickup_attempts(conn, applied: list[str]) -> None:
    name = "pickup_attempts.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS pickup_attempts (
            id                  TEXT PRIMARY KEY,
            order_id            TEXT NOT NULL,
            gateway_id          TEXT NOT NULL,
            created_at          BIGINT NOT NULL,
            ok                  BOOLEAN NOT NULL,
            reason              TEXT,
            provided_step_index INTEGER,
            payload_json        JSONB NOT NULL DEFAULT '{}'
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickup_attempts_order_created ON pickup_attempts (order_id, created_at)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_slot_occupancy_history(conn, applied: list[str]) -> None:
    name = "slot_occupancy_history.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS slot_occupancy_history (
            id              VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
            locker_id       VARCHAR(36) NOT NULL,
            slot_label      VARCHAR(20) NOT NULL,
            allocation_id   VARCHAR(36),
            previous_state  VARCHAR(40),
            current_state   VARCHAR(40) NOT NULL,
            triggered_by    VARCHAR(50),
            occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metadata        JSONB DEFAULT '{}'
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_slot_hist_locker_slot ON slot_occupancy_history (locker_id, slot_label, occurred_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 10 — Documentos Fiscais e Notificações
# ============================================================================

def _create_fiscal_documents(conn, applied: list[str]) -> None:
    name = "fiscal_documents.create_table_v3"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fiscal_documents (
            id                    VARCHAR(36) PRIMARY KEY,
            order_id              VARCHAR(36) NOT NULL UNIQUE REFERENCES orders(id),
            receipt_code          VARCHAR(64) NOT NULL UNIQUE,
            document_type         VARCHAR(50) NOT NULL,
            channel               VARCHAR(20),
            region                VARCHAR(10),
            amount_cents          INTEGER NOT NULL,
            currency              VARCHAR(10) NOT NULL,
            delivery_mode         VARCHAR(20),
            send_status           VARCHAR(50),
            send_target           VARCHAR(255),
            print_status          VARCHAR(50),
            print_site_path       VARCHAR(255),
            payload_json          TEXT NOT NULL,
            issued_at             TIMESTAMPTZ NOT NULL,
            created_at            TIMESTAMPTZ NOT NULL,
            updated_at            TIMESTAMPTZ NOT NULL,
            cancel_reason         TEXT,
            cancelled_at          TIMESTAMPTZ,
            chave_acesso          VARCHAR(255),
            printed_at            TIMESTAMPTZ,
            sent_at               TIMESTAMPTZ,
            tax_amount_cents      BIGINT,
            tax_breakdown_json    JSONB,
            tenant_id             VARCHAR(64),
            xml_signed            BYTEA,
            attempt               INTEGER NOT NULL DEFAULT 1,
            previous_receipt_code VARCHAR(64),
            regenerated_at        TIMESTAMPTZ,
            regenerate_reason     VARCHAR(255)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_fiscal_documents_order ON fiscal_documents (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_fiscal_docs_issued ON fiscal_documents (issued_at)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_invoices(conn, applied: list[str]) -> None:
    name = "invoices.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS invoices (
            id                  VARCHAR(50) PRIMARY KEY,
            order_id            VARCHAR(100) NOT NULL UNIQUE,
            tenant_id           VARCHAR(100),
            country             VARCHAR(5) NOT NULL,
            invoice_type        VARCHAR(20) NOT NULL,
            status              INVOICESTATUS NOT NULL,
            xml_content         JSONB,
            payload_json        JSONB,
            error_message       VARCHAR(500),
            created_at          TIMESTAMPTZ NOT NULL,
            updated_at          TIMESTAMPTZ NOT NULL,
            invoice_number      VARCHAR(50),
            invoice_series      VARCHAR(50),
            access_key          VARCHAR(120),
            payment_method      VARCHAR(50),
            currency            VARCHAR(10),
            tax_details         JSONB,
            government_response JSONB,
            issued_at           TIMESTAMPTZ,
            processing_started_at TIMESTAMPTZ,
            region              VARCHAR(20),
            amount_cents        BIGINT,
            order_snapshot      JSONB,
            last_error_code     VARCHAR(120),
            retry_count         INTEGER DEFAULT 0,
            next_retry_at       TIMESTAMPTZ,
            last_attempt_at     TIMESTAMPTZ,
            dead_lettered_at    TIMESTAMPTZ,
            locked_by           VARCHAR(120),
            locked_at           TIMESTAMPTZ,
            locker_id           VARCHAR(64),
            totem_id            VARCHAR(64),
            slot_label          VARCHAR(32),
            fiscal_doc_subtype  VARCHAR(20) NOT NULL DEFAULT 'NFC_E_65',
            emission_mode       VARCHAR(20) NOT NULL DEFAULT 'ONLINE',
            emitter_cnpj        VARCHAR(18),
            emitter_name        VARCHAR(140),
            consumer_cpf        VARCHAR(14),
            consumer_name       VARCHAR(140),
            locker_address      JSONB,
            items_json          JSONB,
            tax_breakdown_json  JSONB,
            ecommerce_partner_id VARCHAR(100)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invoices_order_id ON invoices (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invoices_status ON invoices (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invoices_locker_id ON invoices (locker_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_notification_logs(conn, applied: list[str]) -> None:
    name = "notification_logs.create_table_v3"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS notification_logs (
            id                   INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            user_id              VARCHAR(36) REFERENCES users(id),
            order_id             VARCHAR(64),
            channel              VARCHAR(32) NOT NULL,
            template_key         VARCHAR(100) NOT NULL,
            destination_masked   VARCHAR(255),
            destination_value    VARCHAR(255),
            dedupe_key           VARCHAR(255),
            provider_name        VARCHAR(100),
            provider_message_id  VARCHAR(255),
            status               VARCHAR(50) NOT NULL,
            attempt_count        INTEGER NOT NULL,
            error_message        TEXT,
            payload_json         JSON,
            processing_started_at TIMESTAMPTZ,
            last_attempt_at      TIMESTAMPTZ,
            next_attempt_at      TIMESTAMPTZ,
            created_at           TIMESTAMPTZ NOT NULL,
            sent_at              TIMESTAMPTZ,
            delivered_at         TIMESTAMPTZ,
            failed_at            TIMESTAMPTZ,
            pickup_id            UUID,
            delivery_id          UUID,
            rental_id            UUID,
            provider_status      VARCHAR(100),
            error_detail         TEXT,
            locale               VARCHAR(10)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_order_id ON notification_logs (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notification_logs_status_next ON notification_logs (status, next_attempt_at)"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_notification_logs_dedupe ON notification_logs (dedupe_key)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_notifications(conn, applied: list[str]) -> None:
    name = "notifications.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS notifications (
            id          VARCHAR(36) PRIMARY KEY,
            channel     VARCHAR(16) NOT NULL,
            payload     TEXT NOT NULL,
            status      VARCHAR(32) NOT NULL,
            attempts    INTEGER NOT NULL,
            last_error  TEXT,
            created_at  TIMESTAMPTZ NOT NULL,
            updated_at  TIMESTAMPTZ NOT NULL
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 11 — Outbox e Eventos
# ============================================================================

def _create_domain_event_outbox(conn, applied: list[str]) -> None:
    name = "domain_event_outbox.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS domain_event_outbox (
            id                  VARCHAR(36) PRIMARY KEY,
            event_key           VARCHAR(255) NOT NULL,
            aggregate_type      VARCHAR(100),
            aggregate_id        VARCHAR(100),
            event_name          VARCHAR(100),
            event_version       INTEGER,
            status              VARCHAR(50),
            payload_json        TEXT,
            occurred_at         TIMESTAMPTZ,
            published_at        TIMESTAMPTZ,
            last_error          TEXT,
            created_at          TIMESTAMPTZ NOT NULL,
            updated_at          TIMESTAMPTZ NOT NULL,
            retry_count         INTEGER NOT NULL DEFAULT 0,
            next_retry_at       TIMESTAMPTZ,
            processing_started_at TIMESTAMPTZ
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_outbox_status_occurred ON domain_event_outbox (status, occurred_at) WHERE status = 'PENDING'"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_domain_events(conn, applied: list[str]) -> None:
    name = "domain_events.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS domain_events (
            id              UUID PRIMARY KEY,
            event_key       VARCHAR(200) NOT NULL UNIQUE,
            aggregate_type  VARCHAR(100) NOT NULL,
            aggregate_id    VARCHAR(100) NOT NULL,
            event_name      VARCHAR(150) NOT NULL,
            event_version   INTEGER NOT NULL,
            status          EVENT_STATUS_ENUM NOT NULL,
            payload         JSONB NOT NULL,
            occurred_at     TIMESTAMPTZ NOT NULL,
            published_at    TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_domain_events_aggregate_id ON domain_events (aggregate_id, event_name, occurred_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_billing_processed_events(conn, applied: list[str]) -> None:
    name = "billing_processed_events.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS billing_processed_events (
            id           UUID PRIMARY KEY,
            event_key    VARCHAR(200) NOT NULL UNIQUE,
            order_id     VARCHAR(100) NOT NULL,
            status       VARCHAR(50) NOT NULL,
            error_message TEXT,
            created_at   TIMESTAMPTZ NOT NULL
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_billing_processed_events_order ON billing_processed_events (order_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_lifecycle_deadlines(conn, applied: list[str]) -> None:
    name = "lifecycle_deadlines.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS lifecycle_deadlines (
            id              UUID PRIMARY KEY,
            deadline_key    VARCHAR(200) NOT NULL UNIQUE,
            order_id        VARCHAR(100) NOT NULL,
            order_channel   VARCHAR(50),
            deadline_type   DEADLINE_TYPE_ENUM NOT NULL,
            status          DEADLINE_STATUS_ENUM NOT NULL,
            due_at          TIMESTAMPTZ NOT NULL,
            locked_at       TIMESTAMPTZ,
            executed_at     TIMESTAMPTZ,
            cancelled_at    TIMESTAMPTZ,
            failure_count   INTEGER NOT NULL,
            payload         JSONB NOT NULL,
            created_at      TIMESTAMPTZ NOT NULL,
            updated_at      TIMESTAMPTZ NOT NULL
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_lifecycle_deadlines_order ON lifecycle_deadlines (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_lifecycle_deadlines_due_at ON lifecycle_deadlines (due_at, status)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_analytics_facts(conn, applied: list[str]) -> None:
    name = "analytics_facts.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS analytics_facts (
            id            UUID PRIMARY KEY,
            fact_key      VARCHAR(200) NOT NULL UNIQUE,
            fact_name     VARCHAR(150) NOT NULL,
            order_id      VARCHAR(100) NOT NULL,
            order_channel VARCHAR(50),
            region_code   VARCHAR(20),
            slot_id       VARCHAR(100),
            payload       JSONB NOT NULL,
            occurred_at   TIMESTAMPTZ NOT NULL,
            created_at    TIMESTAMPTZ NOT NULL
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_analytics_facts_order ON analytics_facts (order_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_reconciliation_pending(conn, applied: list[str]) -> None:
    name = "reconciliation_pending.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS reconciliation_pending (
            id                    VARCHAR(40) PRIMARY KEY,
            dedupe_key            VARCHAR(180) NOT NULL UNIQUE,
            order_id              VARCHAR(36) NOT NULL REFERENCES orders(id),
            reason                VARCHAR(80) NOT NULL,
            status                VARCHAR(24) NOT NULL DEFAULT 'PENDING',
            payload_json          TEXT,
            attempt_count         INTEGER NOT NULL DEFAULT 0,
            max_attempts          INTEGER NOT NULL DEFAULT 5,
            next_retry_at         TIMESTAMPTZ,
            processing_started_at TIMESTAMPTZ,
            last_error            TEXT,
            completed_at          TIMESTAMPTZ,
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_recon_pending_status_next ON reconciliation_pending (status, next_retry_at)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_ops_action_audit(conn, applied: list[str]) -> None:
    name = "ops_action_audit.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ops_action_audit (
            id            VARCHAR(40) PRIMARY KEY,
            action        VARCHAR(120) NOT NULL,
            result        VARCHAR(20) NOT NULL,
            correlation_id VARCHAR(80) NOT NULL,
            user_id       VARCHAR(36),
            role          VARCHAR(80),
            order_id      VARCHAR(36),
            error_message TEXT,
            details_json  TEXT,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ops_audit_created_at ON ops_action_audit (created_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ops_audit_order_id ON ops_action_audit (order_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_ops_outbox_replay_priority_runs(conn, applied: list[str]) -> None:
    name = "ops_outbox_replay_priority_runs.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ops_outbox_replay_priority_runs (
            id                     VARCHAR(36) PRIMARY KEY,
            created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by_role        VARCHAR(30) NOT NULL DEFAULT 'ops_user',
            dry_run                BOOLEAN NOT NULL DEFAULT TRUE,
            run_after_replay       BOOLEAN NOT NULL DEFAULT FALSE,
            top_n_groups           INTEGER NOT NULL DEFAULT 5,
            max_items              INTEGER NOT NULL DEFAULT 100,
            total_groups_selected  INTEGER NOT NULL DEFAULT 0,
            total_candidates       INTEGER NOT NULL DEFAULT 0,
            selected_count         INTEGER NOT NULL DEFAULT 0,
            replayed_count         INTEGER NOT NULL DEFAULT 0,
            skipped_count          INTEGER NOT NULL DEFAULT 0,
            filters_json           JSONB NOT NULL DEFAULT '{}',
            selected_groups_json   JSONB NOT NULL DEFAULT '[]',
            worker_run_json        JSONB
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_oorp_runs_created_at ON ops_outbox_replay_priority_runs (created_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_order_fulfillment_tracking(conn, applied: list[str]) -> None:
    name = "order_fulfillment_tracking.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS order_fulfillment_tracking (
            id                  VARCHAR(36) PRIMARY KEY,
            order_id            VARCHAR(36) NOT NULL UNIQUE REFERENCES orders(id),
            fulfillment_type    VARCHAR(30) NOT NULL DEFAULT 'ECOMMERCE_PARTNER',
            partner_id          VARCHAR(36),
            status              VARCHAR(30) NOT NULL DEFAULT 'PENDING',
            last_event_type     VARCHAR(50),
            last_outbox_status  VARCHAR(20),
            allocated_at        TIMESTAMPTZ,
            dispensed_at        TIMESTAMPTZ,
            picked_up_at        TIMESTAMPTZ,
            returned_at         TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_oft_status_updated ON order_fulfillment_tracking (status, updated_at)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_webhook_endpoints(conn, applied: list[str]) -> None:
    name = "webhook_endpoints.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS webhook_endpoints (
            id            VARCHAR(36) PRIMARY KEY,
            partner_type  VARCHAR(20) NOT NULL,
            partner_id    VARCHAR(36) NOT NULL,
            url           VARCHAR(500) NOT NULL,
            events        TEXT NOT NULL,
            secret_ref    VARCHAR(255),
            signing_algo  VARCHAR(20) NOT NULL DEFAULT 'HMAC_SHA256',
            active        BOOLEAN NOT NULL DEFAULT TRUE,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_webhook_endpoints_partner ON webhook_endpoints (partner_type, partner_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_webhook_deliveries(conn, applied: list[str]) -> None:
    name = "webhook_deliveries.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS webhook_deliveries (
            id                  VARCHAR(36) PRIMARY KEY,
            endpoint_id         VARCHAR(36) NOT NULL REFERENCES webhook_endpoints(id),
            event_name          VARCHAR(100) NOT NULL,
            aggregate_type      VARCHAR(50),
            aggregate_id        VARCHAR(36),
            payload_json        TEXT NOT NULL,
            status              VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            attempt_count       INTEGER NOT NULL DEFAULT 0,
            max_attempts        INTEGER NOT NULL DEFAULT 5,
            last_status_code    INTEGER,
            last_response_body  TEXT,
            last_attempt_at     TIMESTAMPTZ,
            next_attempt_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            delivered_at        TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_webhook_deliveries_status_next ON webhook_deliveries (status, next_attempt_at) WHERE status IN ('PENDING', 'FAILED')"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_webhook_deliveries_endpoint ON webhook_deliveries (endpoint_id)"))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 12 — Assinaturas e Marketplace
# ============================================================================

def _create_subscription_plans(conn, applied: list[str]) -> None:
    name = "subscription_plans.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS subscription_plans (
            id                 VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
            name               VARCHAR(50) NOT NULL,
            code               VARCHAR(20) NOT NULL UNIQUE,
            description        TEXT,
            monthly_fee_cents  INTEGER NOT NULL,
            yearly_fee_cents   INTEGER,
            free_shipping      BOOLEAN DEFAULT FALSE,
            priority_shelf     BOOLEAN DEFAULT FALSE,
            exclusive_deals    BOOLEAN DEFAULT FALSE,
            priority_support   BOOLEAN DEFAULT FALSE,
            max_orders_per_month INTEGER,
            max_discount_pct   NUMERIC(5,2),
            features_json      JSONB DEFAULT '{}',
            is_active          BOOLEAN DEFAULT TRUE,
            created_at         TIMESTAMPTZ DEFAULT NOW(),
            updated_at         TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_customer_subscriptions(conn, applied: list[str]) -> None:
    name = "customer_subscriptions.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS customer_subscriptions (
            id                  VARCHAR(36) PRIMARY KEY,
            user_id             VARCHAR(36) REFERENCES users(id),
            plan_type           VARCHAR(30) NOT NULL,
            status              VARCHAR(20) DEFAULT 'ACTIVE',
            monthly_fee_cents   INTEGER NOT NULL,
            free_shipping       BOOLEAN DEFAULT FALSE,
            priority_shelf      BOOLEAN DEFAULT FALSE,
            exclusive_deals     BOOLEAN DEFAULT FALSE,
            started_at          TIMESTAMPTZ,
            next_billing_at     TIMESTAMPTZ,
            cancelled_at        TIMESTAMPTZ,
            payment_method_id   VARCHAR(36),
            billing_cycle       VARCHAR(20) DEFAULT 'MONTHLY',
            cancel_at_period_end BOOLEAN DEFAULT FALSE,
            trial_start         TIMESTAMPTZ,
            trial_end           TIMESTAMPTZ,
            current_period_start TIMESTAMPTZ,
            current_period_end  TIMESTAMPTZ,
            created_at          TIMESTAMPTZ DEFAULT NOW(),
            updated_at          TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_customer_subscriptions_user ON customer_subscriptions (user_id, status)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_subscription_benefits_usage(conn, applied: list[str]) -> None:
    name = "subscription_benefits_usage.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS subscription_benefits_usage (
            id              BIGSERIAL PRIMARY KEY,
            subscription_id VARCHAR(36) NOT NULL REFERENCES customer_subscriptions(id),
            usage_month     DATE NOT NULL,
            benefit_type    VARCHAR(30) NOT NULL,
            usage_count     INTEGER DEFAULT 0,
            usage_limit     INTEGER,
            created_at      TIMESTAMPTZ DEFAULT NOW(),
            updated_at      TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_marketplace_sellers(conn, applied: list[str]) -> None:
    name = "marketplace_sellers.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS marketplace_sellers (
            id                  VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
            legal_name          VARCHAR(140) NOT NULL,
            trade_name          VARCHAR(140),
            tax_id              VARCHAR(32) NOT NULL UNIQUE,
            email               VARCHAR(128) NOT NULL,
            phone               VARCHAR(32),
            website             VARCHAR(255),
            status              VARCHAR(20) NOT NULL DEFAULT 'PENDING_APPROVAL',
            commission_pct      NUMERIC(5,2) NOT NULL DEFAULT 5.00,
            monthly_fee_cents   BIGINT NOT NULL DEFAULT 0,
            seller_rating       NUMERIC(3,2) DEFAULT 0,
            total_sales_cents   BIGINT DEFAULT 0,
            total_orders        INTEGER DEFAULT 0,
            joined_at           TIMESTAMPTZ DEFAULT NOW(),
            approved_at         TIMESTAMPTZ,
            suspended_at        TIMESTAMPTZ,
            created_at          TIMESTAMPTZ DEFAULT NOW(),
            updated_at          TIMESTAMPTZ DEFAULT NOW(),
            created_by          VARCHAR(36),
            updated_by          VARCHAR(36),
            deleted_at          TIMESTAMPTZ
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_marketplace_sellers_status ON marketplace_sellers (status)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_seller_products(conn, applied: list[str]) -> None:
    name = "seller_products.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS seller_products (
            id                      VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
            seller_id               VARCHAR(36) NOT NULL REFERENCES marketplace_sellers(id),
            locker_id               VARCHAR(36) NOT NULL REFERENCES lockers(id),
            product_id              VARCHAR(255) NOT NULL,
            seller_sku              VARCHAR(64),
            price_cents             INTEGER NOT NULL,
            quantity                INTEGER NOT NULL DEFAULT 0,
            max_quantity_per_order  INTEGER DEFAULT 10,
            status                  VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
            priority                INTEGER DEFAULT 100,
            created_at              TIMESTAMPTZ DEFAULT NOW(),
            updated_at              TIMESTAMPTZ DEFAULT NOW(),
            deleted_at              TIMESTAMPTZ,
            UNIQUE(seller_id, locker_id, product_id)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_seller_products_seller ON seller_products (seller_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_seller_products_locker ON seller_products (locker_id, status)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_marketplace_commissions(conn, applied: list[str]) -> None:
    name = "marketplace_commissions.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS marketplace_commissions (
            id                        VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
            seller_id                 VARCHAR(36) NOT NULL REFERENCES marketplace_sellers(id),
            order_id                  VARCHAR(36) NOT NULL REFERENCES orders(id),
            order_item_id             BIGINT REFERENCES order_items(id),
            commission_rate_pct       NUMERIC(5,2) NOT NULL,
            commission_amount_cents   INTEGER NOT NULL,
            ellan_fee_cents           INTEGER NOT NULL,
            payment_gateway_fee_cents INTEGER NOT NULL,
            net_to_seller_cents       INTEGER NOT NULL,
            status                    VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            settled_at                TIMESTAMPTZ,
            created_at                TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_marketplace_commissions_order ON marketplace_commissions (order_id, status)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_seller_reviews(conn, applied: list[str]) -> None:
    name = "seller_reviews.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS seller_reviews (
            id                   VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid(),
            seller_id            VARCHAR(36) NOT NULL REFERENCES marketplace_sellers(id),
            order_id             VARCHAR(36) NOT NULL REFERENCES orders(id),
            user_id              VARCHAR(36) REFERENCES users(id),
            rating               INTEGER NOT NULL,
            comment              TEXT,
            delivery_rating      INTEGER,
            product_quality_rating INTEGER,
            communication_rating INTEGER,
            verified_purchase    BOOLEAN DEFAULT TRUE,
            created_at           TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_seller_reviews_seller ON seller_reviews (seller_id, rating)"))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 13 — Rental (Aluguel de Slots)
# ============================================================================

def _create_rental_plans(conn, applied: list[str]) -> None:
    name = "rental_plans.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS rental_plans (
            id                 VARCHAR(36) PRIMARY KEY,
            locker_id          VARCHAR(36) REFERENCES lockers(id),
            slot_size          VARCHAR(8),
            name               VARCHAR(128) NOT NULL,
            description        TEXT,
            billing_cycle      VARCHAR(20) NOT NULL,
            amount_cents       INTEGER NOT NULL,
            currency           VARCHAR(8) NOT NULL DEFAULT 'BRL',
            max_duration_days  INTEGER,
            grace_period_hours INTEGER NOT NULL DEFAULT 24,
            active             BOOLEAN NOT NULL DEFAULT TRUE,
            created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_rental_plans_locker ON rental_plans (locker_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_rental_contracts(conn, applied: list[str]) -> None:
    name = "rental_contracts.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS rental_contracts (
            id                VARCHAR(36) PRIMARY KEY,
            locker_id         VARCHAR(36) NOT NULL REFERENCES lockers(id),
            slot_label        VARCHAR(20) NOT NULL,
            plan_id           VARCHAR(36) REFERENCES rental_plans(id),
            tenant_id         VARCHAR(100),
            renter_user_id    VARCHAR(36) REFERENCES users(id),
            renter_name       VARCHAR(255),
            renter_document   VARCHAR(32),
            renter_phone      VARCHAR(32),
            renter_email      VARCHAR(128),
            amount_cents      INTEGER NOT NULL,
            currency          VARCHAR(8) NOT NULL DEFAULT 'BRL',
            billing_cycle     VARCHAR(20) NOT NULL,
            next_billing_at   TIMESTAMPTZ,
            auto_renew        BOOLEAN NOT NULL DEFAULT FALSE,
            status            VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            started_at        TIMESTAMPTZ,
            ends_at           TIMESTAMPTZ,
            cancelled_at      TIMESTAMPTZ,
            cancel_reason     VARCHAR(255),
            ended_at          TIMESTAMPTZ,
            access_pin_hash   VARCHAR(255),
            access_token_ref  VARCHAR(255),
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_rental_contracts_locker ON rental_contracts (locker_id, slot_label)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_rental_contracts_status ON rental_contracts (status)"))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 14 — Métricas e ML
# ============================================================================

def _create_demand_forecast(conn, applied: list[str]) -> None:
    name = "demand_forecast.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS demand_forecast (
            id                  BIGSERIAL PRIMARY KEY,
            locker_id           VARCHAR(36) NOT NULL REFERENCES lockers(id),
            forecast_date       DATE NOT NULL,
            predicted_orders    INTEGER NOT NULL,
            predicted_revenue_cents BIGINT NOT NULL,
            confidence_lower    INTEGER,
            confidence_upper    INTEGER,
            model_version       VARCHAR(50),
            generated_at        TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(locker_id, forecast_date)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_demand_forecast_locker ON demand_forecast (locker_id, forecast_date DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_ml_features_daily(conn, applied: list[str]) -> None:
    name = "ml_features_daily.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ml_features_daily (
            id                 BIGSERIAL PRIMARY KEY,
            locker_id          VARCHAR(36) NOT NULL REFERENCES lockers(id) ON DELETE CASCADE,
            feature_date       DATE NOT NULL,
            temperature_mean   NUMERIC(10,4),
            humidity_mean      NUMERIC(10,4),
            battery_min        NUMERIC(10,2),
            door_failures_7d   INTEGER NOT NULL DEFAULT 0,
            usage_events_7d    INTEGER NOT NULL DEFAULT 0,
            uptime_hours_7d    NUMERIC(10,2) NOT NULL DEFAULT 0,
            failure_label_7d   SMALLINT NOT NULL DEFAULT 0,
            created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            temperature_avg_70d NUMERIC(10,4),
            humidity_avg_70d   NUMERIC(10,4),
            battery_min_70d    NUMERIC(10,2),
            door_failures_70d  INTEGER,
            usage_events_70d   INTEGER,
            uptime_hours_70d   NUMERIC(10,2),
            failure_label_70d  SMALLINT,
            UNIQUE(locker_id, feature_date)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ml_features_daily_locker_date ON ml_features_daily (locker_id, feature_date DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_ml_predictions_log(conn, applied: list[str]) -> None:
    name = "ml_predictions_log.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ml_predictions_log (
            id                  BIGSERIAL PRIMARY KEY,
            locker_id           VARCHAR(36) NOT NULL,
            predicted_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            failure_probability NUMERIC(8,6) NOT NULL,
            health_score        NUMERIC(8,2) NOT NULL,
            model_version       VARCHAR(64) NOT NULL
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ml_predictions_locker_time ON ml_predictions_log (locker_id, predicted_at DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_ml_model_metadata(conn, applied: list[str]) -> None:
    name = "ml_model_metadata.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ml_model_metadata (
            id             BIGSERIAL PRIMARY KEY,
            model_version  VARCHAR(64) NOT NULL UNIQUE,
            trained_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            metrics_json   JSONB NOT NULL DEFAULT '{}',
            status         VARCHAR(32) NOT NULL DEFAULT 'ACTIVE'
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_ml_prediction_feedback(conn, applied: list[str]) -> None:
    name = "ml_prediction_feedback.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ml_prediction_feedback (
            id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            prediction_id            BIGINT REFERENCES ml_predictions_log(id) ON DELETE CASCADE,
            actual_value             DOUBLE PRECISION,
            error_pct                NUMERIC(5,2),
            feedback_at              TIMESTAMPTZ DEFAULT NOW(),
            model_performance_status VARCHAR(50),
            created_at               TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ml_feedback_prediction ON ml_prediction_feedback (prediction_id)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_locker_slot_hourly_occupancy(conn, applied: list[str]) -> None:
    name = "locker_slot_hourly_occupancy.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS locker_slot_hourly_occupancy (
            id                    BIGSERIAL PRIMARY KEY,
            locker_id             VARCHAR(36) NOT NULL,
            slot_number           INTEGER NOT NULL,
            hour_bucket           TIMESTAMPTZ NOT NULL,
            is_occupied           BOOLEAN NOT NULL,
            delivery_id           VARCHAR(36),
            occupied_duration_minutes INTEGER NOT NULL DEFAULT 0,
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(locker_id, slot_number, hour_bucket)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_lsho_locker_hour ON locker_slot_hourly_occupancy (locker_id, hour_bucket)"))

    _mark_migration(conn, name)
    applied.append(name)


def _create_locker_utilization_snapshots(conn, applied: list[str]) -> None:
    name = "locker_utilization_snapshots.create_table_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS locker_utilization_snapshots (
            id                       BIGSERIAL PRIMARY KEY,
            snapshot_date            DATE NOT NULL,
            partner_id               VARCHAR(36) NOT NULL,
            locker_id                VARCHAR(36) NOT NULL,
            country_code             VARCHAR(2),
            jurisdiction_code        VARCHAR(32),
            currency                 VARCHAR(8) NOT NULL DEFAULT 'BRL',
            timezone                 VARCHAR(64) NOT NULL DEFAULT 'UTC',
            measured_occupied_minutes INTEGER NOT NULL DEFAULT 0,
            measured_occupied_hours  NUMERIC(12,4) NOT NULL DEFAULT 0,
            billed_storage_units     NUMERIC(12,4) NOT NULL DEFAULT 0,
            billed_storage_hours     NUMERIC(12,4) NOT NULL DEFAULT 0,
            billed_storage_amount_cents BIGINT NOT NULL DEFAULT 0,
            difference_hours         NUMERIC(12,4) NOT NULL DEFAULT 0,
            difference_pct           NUMERIC(10,4),
            divergence_status        VARCHAR(20) NOT NULL DEFAULT 'OK',
            dedupe_key               VARCHAR(180),
            metadata_json            JSONB NOT NULL DEFAULT '{}',
            created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(partner_id, locker_id, snapshot_date)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_lus_snapshot_date ON locker_utilization_snapshots (snapshot_date)"))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 15 — BI e Analytics (Metabase)
# ============================================================================

def _create_metabase_tables(conn, applied: list[str]) -> None:
    """Tabelas do Metabase para BI."""
    name = "metabase_tables.create_v1"
    if _migration_applied(conn, name):
        return

    # metabase_database
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS metabase_database (
            id                         INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            created_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            name                       VARCHAR(254) NOT NULL,
            description                TEXT,
            details                    TEXT NOT NULL,
            engine                     VARCHAR(254) NOT NULL,
            is_sample                  BOOLEAN NOT NULL DEFAULT FALSE,
            is_full_sync               BOOLEAN NOT NULL DEFAULT TRUE,
            points_of_interest         TEXT,
            caveats                    TEXT,
            metadata_sync_schedule     VARCHAR(254) NOT NULL DEFAULT '0 50 * * * ? *',
            cache_field_values_schedule VARCHAR(254) NOT NULL DEFAULT '0 50 0 * * ? *',
            timezone                   VARCHAR(254),
            is_on_demand               BOOLEAN NOT NULL DEFAULT FALSE,
            auto_run_queries           BOOLEAN NOT NULL DEFAULT TRUE,
            refingerprint              BOOLEAN,
            cache_ttl                  INTEGER,
            initial_sync_status        VARCHAR(32) NOT NULL DEFAULT 'complete',
            creator_id                 INTEGER REFERENCES core_user(id),
            settings                   TEXT,
            dbms_version               TEXT,
            is_audit                   BOOLEAN NOT NULL DEFAULT FALSE
        )
    """))

    # metabase_table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS metabase_table (
            id                         INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            created_at                 TIMESTAMPTZ NOT NULL,
            updated_at                 TIMESTAMPTZ NOT NULL,
            name                       VARCHAR(256) NOT NULL,
            description                TEXT,
            entity_type                VARCHAR(254),
            active                     BOOLEAN NOT NULL,
            db_id                      INTEGER NOT NULL REFERENCES metabase_database(id) ON DELETE CASCADE,
            display_name               VARCHAR(256),
            visibility_type            VARCHAR(254),
            schema                     VARCHAR(254),
            points_of_interest         TEXT,
            caveats                    TEXT,
            show_in_getting_started    BOOLEAN NOT NULL DEFAULT FALSE,
            field_order                VARCHAR(254) NOT NULL DEFAULT 'database',
            initial_sync_status        VARCHAR(32) NOT NULL DEFAULT 'complete',
            is_upload                  BOOLEAN NOT NULL DEFAULT FALSE,
            database_require_filter    BOOLEAN,
            UNIQUE(db_id, schema, name)
        )
    """))

    # metabase_field
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS metabase_field (
            id                         INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            created_at                 TIMESTAMPTZ NOT NULL,
            updated_at                 TIMESTAMPTZ NOT NULL,
            name                       VARCHAR(254) NOT NULL,
            base_type                  VARCHAR(255) NOT NULL,
            semantic_type              VARCHAR(255),
            active                     BOOLEAN NOT NULL DEFAULT TRUE,
            description                TEXT,
            preview_display            BOOLEAN NOT NULL DEFAULT TRUE,
            position                   INTEGER NOT NULL DEFAULT 0,
            table_id                   INTEGER NOT NULL REFERENCES metabase_table(id) ON DELETE CASCADE,
            parent_id                  INTEGER REFERENCES metabase_field(id) ON DELETE CASCADE,
            display_name               VARCHAR(254),
            visibility_type            VARCHAR(32) NOT NULL DEFAULT 'normal',
            fk_target_field_id         INTEGER REFERENCES metabase_field(id),
            last_analyzed              TIMESTAMPTZ,
            points_of_interest         TEXT,
            caveats                    TEXT,
            fingerprint                TEXT,
            fingerprint_version        INTEGER NOT NULL DEFAULT 0,
            database_type              TEXT NOT NULL,
            has_field_values           TEXT,
            settings                   TEXT,
            database_position          INTEGER NOT NULL DEFAULT 0,
            custom_position            INTEGER NOT NULL DEFAULT 0,
            effective_type             VARCHAR(255),
            coercion_strategy          VARCHAR(255),
            nfc_path                   VARCHAR(254),
            database_required          BOOLEAN NOT NULL DEFAULT FALSE,
            json_unfolding             BOOLEAN NOT NULL DEFAULT FALSE,
            database_is_auto_increment BOOLEAN NOT NULL DEFAULT FALSE,
            database_indexed           BOOLEAN,
            database_partitioned       BOOLEAN,
            UNIQUE(table_id, parent_id, name)
        )
    """))

    # metabase_fieldvalues
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS metabase_fieldvalues (
            id                     INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            created_at             TIMESTAMPTZ NOT NULL,
            updated_at             TIMESTAMPTZ NOT NULL,
            values                 TEXT,
            human_readable_values  TEXT,
            field_id               INTEGER NOT NULL REFERENCES metabase_field(id) ON DELETE CASCADE,
            has_more_values        BOOLEAN DEFAULT FALSE,
            type                   VARCHAR(32) NOT NULL DEFAULT 'full',
            hash_key               TEXT,
            last_used_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    # report_card (questions)
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS report_card (
            id                     INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            created_at             TIMESTAMPTZ NOT NULL,
            updated_at             TIMESTAMPTZ NOT NULL,
            name                   VARCHAR(254) NOT NULL,
            description            TEXT,
            display                VARCHAR(254) NOT NULL,
            dataset_query          TEXT NOT NULL,
            visualization_settings TEXT NOT NULL,
            creator_id             INTEGER NOT NULL REFERENCES core_user(id) ON DELETE CASCADE,
            database_id            INTEGER NOT NULL REFERENCES metabase_database(id) ON DELETE CASCADE,
            table_id               INTEGER REFERENCES metabase_table(id) ON DELETE CASCADE,
            query_type             VARCHAR(16),
            archived               BOOLEAN NOT NULL DEFAULT FALSE,
            collection_id          INTEGER REFERENCES collection(id) ON DELETE SET NULL,
            public_uuid            CHAR(36),
            made_public_by_id      INTEGER REFERENCES core_user(id) ON DELETE CASCADE,
            enable_embedding       BOOLEAN NOT NULL DEFAULT FALSE,
            embedding_params       TEXT,
            cache_ttl              INTEGER,
            result_metadata        TEXT,
            collection_position    SMALLINT,
            dataset                BOOLEAN NOT NULL DEFAULT FALSE,
            entity_id              CHAR(21) UNIQUE,
            parameters             TEXT,
            parameter_mappings     TEXT,
            collection_preview     BOOLEAN NOT NULL DEFAULT TRUE,
            metabase_version       VARCHAR(100)
        )
    """))

    # report_dashboard
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS report_dashboard (
            id                     INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            created_at             TIMESTAMPTZ NOT NULL,
            updated_at             TIMESTAMPTZ NOT NULL,
            name                   VARCHAR(254) NOT NULL,
            description            TEXT,
            creator_id             INTEGER NOT NULL REFERENCES core_user(id) ON DELETE CASCADE,
            parameters             TEXT NOT NULL,
            points_of_interest     TEXT,
            caveats                TEXT,
            show_in_getting_started BOOLEAN NOT NULL DEFAULT FALSE,
            public_uuid            CHAR(36),
            made_public_by_id      INTEGER REFERENCES core_user(id) ON DELETE CASCADE,
            enable_embedding       BOOLEAN NOT NULL DEFAULT FALSE,
            embedding_params       TEXT,
            archived               BOOLEAN NOT NULL DEFAULT FALSE,
            position               INTEGER,
            collection_id          INTEGER REFERENCES collection(id) ON DELETE SET NULL,
            collection_position    SMALLINT,
            cache_ttl              INTEGER,
            entity_id              CHAR(21) UNIQUE,
            auto_apply_filters     BOOLEAN NOT NULL DEFAULT TRUE
        )
    """))

    # report_dashboardcard
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS report_dashboardcard (
            id                     INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            size_x                 INTEGER NOT NULL,
            size_y                 INTEGER NOT NULL,
            row                    INTEGER NOT NULL,
            col                    INTEGER NOT NULL,
            card_id                INTEGER REFERENCES report_card(id),
            dashboard_id           INTEGER NOT NULL REFERENCES report_dashboard(id),
            parameter_mappings     TEXT NOT NULL,
            visualization_settings TEXT NOT NULL,
            entity_id              CHAR(21) UNIQUE,
            action_id              INTEGER REFERENCES action(id) ON DELETE CASCADE,
            dashboard_tab_id       INTEGER REFERENCES dashboard_tab(id) ON DELETE CASCADE
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_metabase_support_tables(conn, applied: list[str]) -> None:
    """Tabelas auxiliares do Metabase."""
    name = "metabase_support_tables.create_v1"
    if _migration_applied(conn, name):
        return

    # action
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS action (
            id                     INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            type                   TEXT NOT NULL,
            model_id               INTEGER NOT NULL,
            name                   VARCHAR(254) NOT NULL,
            description            TEXT,
            parameters             TEXT,
            parameter_mappings     TEXT,
            visualization_settings TEXT,
            public_uuid            CHAR(36) UNIQUE,
            made_public_by_id      INTEGER REFERENCES core_user(id) ON DELETE CASCADE,
            creator_id             INTEGER REFERENCES core_user(id),
            archived               BOOLEAN NOT NULL DEFAULT FALSE,
            entity_id              CHAR(21) UNIQUE
        )
    """))

    # collection
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS collection (
            id                     INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            name                   TEXT NOT NULL,
            description            TEXT,
            archived               BOOLEAN NOT NULL DEFAULT FALSE,
            location               VARCHAR(254) NOT NULL DEFAULT '/',
            personal_owner_id      INTEGER UNIQUE REFERENCES core_user(id) ON DELETE CASCADE,
            slug                   VARCHAR(510) NOT NULL,
            namespace              VARCHAR(254),
            authority_level        VARCHAR(255),
            entity_id              CHAR(21) UNIQUE,
            created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            type                   VARCHAR(256)
        )
    """))

    # dashboard_tab
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS dashboard_tab (
            id                     INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            dashboard_id           INTEGER NOT NULL REFERENCES report_dashboard(id),
            name                   TEXT NOT NULL,
            position               INTEGER NOT NULL,
            entity_id              CHAR(21) UNIQUE,
            created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    # metric
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS metric (
            id                     INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            table_id               INTEGER NOT NULL REFERENCES metabase_table(id) ON DELETE CASCADE,
            creator_id             INTEGER NOT NULL REFERENCES core_user(id) ON DELETE CASCADE,
            name                   VARCHAR(254) NOT NULL,
            description            TEXT,
            archived               BOOLEAN NOT NULL DEFAULT FALSE,
            definition             TEXT NOT NULL,
            created_at             TIMESTAMPTZ NOT NULL,
            updated_at             TIMESTAMPTZ NOT NULL,
            points_of_interest     TEXT,
            caveats                TEXT,
            how_is_this_calculated TEXT,
            show_in_getting_started BOOLEAN NOT NULL DEFAULT FALSE,
            entity_id              CHAR(21) UNIQUE
        )
    """))

    # segment
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS segment (
            id                     INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            table_id               INTEGER NOT NULL REFERENCES metabase_table(id) ON DELETE CASCADE,
            creator_id             INTEGER NOT NULL REFERENCES core_user(id) ON DELETE CASCADE,
            name                   VARCHAR(254) NOT NULL,
            description            TEXT,
            archived               BOOLEAN NOT NULL DEFAULT FALSE,
            definition             TEXT NOT NULL,
            created_at             TIMESTAMPTZ NOT NULL,
            updated_at             TIMESTAMPTZ NOT NULL,
            points_of_interest     TEXT,
            caveats                TEXT,
            show_in_getting_started BOOLEAN NOT NULL DEFAULT FALSE,
            entity_id              CHAR(21) UNIQUE
        )
    """))

    # pulse (subscriptions/alerts)
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS pulse (
            id                     INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            creator_id             INTEGER NOT NULL REFERENCES core_user(id) ON DELETE CASCADE,
            name                   VARCHAR(254),
            created_at             TIMESTAMPTZ NOT NULL,
            updated_at             TIMESTAMPTZ NOT NULL,
            skip_if_empty          BOOLEAN NOT NULL DEFAULT FALSE,
            alert_condition        VARCHAR(254),
            alert_first_only       BOOLEAN,
            alert_above_goal       BOOLEAN,
            collection_id          INTEGER REFERENCES collection(id) ON DELETE SET NULL,
            collection_position    SMALLINT,
            archived               BOOLEAN DEFAULT FALSE,
            dashboard_id           INTEGER REFERENCES report_dashboard(id),
            parameters             TEXT NOT NULL,
            entity_id              CHAR(21) UNIQUE
        )
    """))

    # dashboardcard_series
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS dashboardcard_series (
            id                     INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            dashboardcard_id       INTEGER NOT NULL REFERENCES report_dashboardcard(id),
            card_id                INTEGER NOT NULL REFERENCES report_card(id),
            position               INTEGER NOT NULL
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_metabase_audit_tables(conn, applied: list[str]) -> None:
    """Tabelas de auditoria do Metabase."""
    name = "metabase_audit_tables.create_v1"
    if _migration_applied(conn, name):
        return

    # activity
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS activity (
            id                 INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            topic              VARCHAR(32) NOT NULL,
            timestamp          TIMESTAMPTZ NOT NULL,
            user_id            INTEGER REFERENCES core_user(id) ON DELETE CASCADE,
            model              VARCHAR(32),
            model_id           INTEGER,
            database_id        INTEGER,
            table_id           INTEGER,
            custom_id          VARCHAR(48),
            details            TEXT NOT NULL
        )
    """))

    # audit_log
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id                 INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            topic              VARCHAR(32) NOT NULL,
            timestamp          TIMESTAMPTZ NOT NULL,
            end_timestamp      TIMESTAMPTZ,
            user_id            INTEGER REFERENCES core_user(id),
            model              VARCHAR(32),
            model_id           INTEGER,
            details            TEXT NOT NULL
        )
    """))

    # query_execution
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS query_execution (
            id                 INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            hash               BYTEA NOT NULL,
            started_at         TIMESTAMPTZ NOT NULL,
            running_time       INTEGER NOT NULL,
            result_rows        INTEGER NOT NULL,
            native             BOOLEAN NOT NULL,
            context            VARCHAR(32),
            error              TEXT,
            executor_id        INTEGER REFERENCES core_user(id),
            card_id            INTEGER REFERENCES report_card(id),
            dashboard_id       INTEGER REFERENCES report_dashboard(id),
            pulse_id           INTEGER REFERENCES pulse(id),
            database_id        INTEGER REFERENCES metabase_database(id),
            cache_hit          BOOLEAN,
            action_id          INTEGER REFERENCES action(id),
            is_sandboxed       BOOLEAN,
            cache_hash         BYTEA
        )
    """))

    # view_log
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS view_log (
            id                 INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            user_id            INTEGER REFERENCES core_user(id) ON DELETE CASCADE,
            model              VARCHAR(16) NOT NULL,
            model_id           INTEGER NOT NULL,
            timestamp          TIMESTAMPTZ NOT NULL,
            metadata           TEXT,
            has_access         BOOLEAN,
            context            VARCHAR(32)
        )
    """))

    # revision
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS revision (
            id                 INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            model              VARCHAR(16) NOT NULL,
            model_id           INTEGER NOT NULL,
            user_id            INTEGER NOT NULL REFERENCES core_user(id) ON DELETE CASCADE,
            timestamp          TIMESTAMPTZ NOT NULL,
            object             TEXT NOT NULL,
            is_reversion       BOOLEAN NOT NULL DEFAULT FALSE,
            is_creation        BOOLEAN NOT NULL DEFAULT FALSE,
            message            TEXT,
            most_recent        BOOLEAN NOT NULL DEFAULT FALSE,
            metabase_version   VARCHAR(100)
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_metabase_permission_tables(conn, applied: list[str]) -> None:
    """Tabelas de permissões do Metabase."""
    name = "metabase_permission_tables.create_v1"
    if _migration_applied(conn, name):
        return

    # permissions_group
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS permissions_group (
            id                     INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            name                   VARCHAR(255) NOT NULL UNIQUE
        )
    """))

    # permissions
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS permissions (
            id                     INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            object                 VARCHAR(254) NOT NULL,
            group_id               INTEGER NOT NULL REFERENCES permissions_group(id) ON DELETE CASCADE,
            UNIQUE(group_id, object)
        )
    """))

    # permissions_group_membership
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS permissions_group_membership (
            id                     INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            user_id                INTEGER NOT NULL REFERENCES core_user(id) ON DELETE CASCADE,
            group_id               INTEGER NOT NULL REFERENCES permissions_group(id) ON DELETE CASCADE,
            is_group_manager       BOOLEAN NOT NULL DEFAULT FALSE,
            UNIQUE(user_id, group_id)
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_metabase_scheduler_tables(conn, applied: list[str]) -> None:
    """Tabelas do Quartz Scheduler do Metabase."""
    name = "metabase_scheduler_tables.create_v1"
    if _migration_applied(conn, name):
        return

    # qrtz_job_details
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS qrtz_job_details (
            sched_name        VARCHAR(120) NOT NULL,
            job_name          VARCHAR(200) NOT NULL,
            job_group         VARCHAR(200) NOT NULL,
            description       VARCHAR(250),
            job_class_name    VARCHAR(250) NOT NULL,
            is_durable        BOOLEAN NOT NULL,
            is_nonconcurrent  BOOLEAN NOT NULL,
            is_update_data    BOOLEAN NOT NULL,
            requests_recovery BOOLEAN NOT NULL,
            job_data          BYTEA,
            PRIMARY KEY (sched_name, job_name, job_group)
        )
    """))

    # qrtz_triggers
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS qrtz_triggers (
            sched_name        VARCHAR(120) NOT NULL,
            trigger_name      VARCHAR(200) NOT NULL,
            trigger_group     VARCHAR(200) NOT NULL,
            job_name          VARCHAR(200) NOT NULL,
            job_group         VARCHAR(200) NOT NULL,
            description       VARCHAR(250),
            next_fire_time    BIGINT,
            prev_fire_time    BIGINT,
            priority          INTEGER,
            trigger_state     VARCHAR(16) NOT NULL,
            trigger_type      VARCHAR(8) NOT NULL,
            start_time        BIGINT NOT NULL,
            end_time          BIGINT,
            calendar_name     VARCHAR(200),
            misfire_instr     SMALLINT,
            job_data          BYTEA,
            PRIMARY KEY (sched_name, trigger_name, trigger_group),
            FOREIGN KEY (sched_name, job_name, job_group)
                REFERENCES qrtz_job_details(sched_name, job_name, job_group)
        )
    """))

    # qrtz_cron_triggers
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS qrtz_cron_triggers (
            sched_name        VARCHAR(120) NOT NULL,
            trigger_name      VARCHAR(200) NOT NULL,
            trigger_group     VARCHAR(200) NOT NULL,
            cron_expression   VARCHAR(120) NOT NULL,
            time_zone_id      VARCHAR(80),
            PRIMARY KEY (sched_name, trigger_name, trigger_group),
            FOREIGN KEY (sched_name, trigger_name, trigger_group)
                REFERENCES qrtz_triggers(sched_name, trigger_name, trigger_group)
        )
    """))

    # qrtz_simple_triggers
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS qrtz_simple_triggers (
            sched_name        VARCHAR(120) NOT NULL,
            trigger_name      VARCHAR(200) NOT NULL,
            trigger_group     VARCHAR(200) NOT NULL,
            repeat_count      BIGINT NOT NULL,
            repeat_interval   BIGINT NOT NULL,
            times_triggered   BIGINT NOT NULL,
            PRIMARY KEY (sched_name, trigger_name, trigger_group),
            FOREIGN KEY (sched_name, trigger_name, trigger_group)
                REFERENCES qrtz_triggers(sched_name, trigger_name, trigger_group)
        )
    """))

    # qrtz_blob_triggers
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS qrtz_blob_triggers (
            sched_name        VARCHAR(120) NOT NULL,
            trigger_name      VARCHAR(200) NOT NULL,
            trigger_group     VARCHAR(200) NOT NULL,
            blob_data         BYTEA,
            PRIMARY KEY (sched_name, trigger_name, trigger_group),
            FOREIGN KEY (sched_name, trigger_name, trigger_group)
                REFERENCES qrtz_triggers(sched_name, trigger_name, trigger_group)
        )
    """))

    # qrtz_simprop_triggers
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS qrtz_simprop_triggers (
            sched_name        VARCHAR(120) NOT NULL,
            trigger_name      VARCHAR(200) NOT NULL,
            trigger_group     VARCHAR(200) NOT NULL,
            str_prop_1        VARCHAR(512),
            str_prop_2        VARCHAR(512),
            str_prop_3        VARCHAR(512),
            int_prop_1        INTEGER,
            int_prop_2        INTEGER,
            long_prop_1       BIGINT,
            long_prop_2       BIGINT,
            dec_prop_1        NUMERIC(13,4),
            dec_prop_2        NUMERIC(13,4),
            bool_prop_1       BOOLEAN,
            bool_prop_2       BOOLEAN,
            PRIMARY KEY (sched_name, trigger_name, trigger_group),
            FOREIGN KEY (sched_name, trigger_name, trigger_group)
                REFERENCES qrtz_triggers(sched_name, trigger_name, trigger_group)
        )
    """))

    # qrtz_fired_triggers
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS qrtz_fired_triggers (
            sched_name        VARCHAR(120) NOT NULL,
            entry_id          VARCHAR(95) NOT NULL,
            trigger_name      VARCHAR(200) NOT NULL,
            trigger_group     VARCHAR(200) NOT NULL,
            instance_name     VARCHAR(200) NOT NULL,
            fired_time        BIGINT NOT NULL,
            sched_time        BIGINT,
            priority          INTEGER NOT NULL,
            state             VARCHAR(16) NOT NULL,
            job_name          VARCHAR(200),
            job_group         VARCHAR(200),
            is_nonconcurrent  BOOLEAN,
            requests_recovery BOOLEAN,
            PRIMARY KEY (sched_name, entry_id)
        )
    """))

    # qrtz_scheduler_state
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS qrtz_scheduler_state (
            sched_name        VARCHAR(120) NOT NULL,
            instance_name     VARCHAR(200) NOT NULL,
            last_checkin_time BIGINT NOT NULL,
            checkin_interval  BIGINT NOT NULL,
            PRIMARY KEY (sched_name, instance_name)
        )
    """))

    # qrtz_locks
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS qrtz_locks (
            sched_name        VARCHAR(120) NOT NULL,
            lock_name         VARCHAR(40) NOT NULL,
            PRIMARY KEY (sched_name, lock_name)
        )
    """))

    # qrtz_paused_trigger_grps
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS qrtz_paused_trigger_grps (
            sched_name        VARCHAR(120) NOT NULL,
            trigger_group     VARCHAR(200) NOT NULL,
            PRIMARY KEY (sched_name, trigger_group)
        )
    """))

    # qrtz_calendars
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS qrtz_calendars (
            sched_name        VARCHAR(120) NOT NULL,
            calendar_name     VARCHAR(200) NOT NULL,
            calendar          BYTEA NOT NULL,
            PRIMARY KEY (sched_name, calendar_name)
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_metabase_embedding_tables(conn, applied: list[str]) -> None:
    """Tabelas para embedding e ações do Metabase."""
    name = "metabase_embedding_tables.create_v1"
    if _migration_applied(conn, name):
        return

    # parameter_card
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS parameter_card (
            id                       INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            card_id                  INTEGER NOT NULL REFERENCES report_card(id),
            parameterized_object_type VARCHAR(32) NOT NULL,
            parameterized_object_id  INTEGER NOT NULL,
            parameter_id             VARCHAR(36) NOT NULL,
            UNIQUE(parameterized_object_id, parameterized_object_type, parameter_id)
        )
    """))

    # native_query_snippet
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS native_query_snippet (
            id                 INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            name               VARCHAR(254) NOT NULL UNIQUE,
            description        TEXT,
            content            TEXT NOT NULL,
            creator_id         INTEGER NOT NULL REFERENCES core_user(id) ON DELETE CASCADE,
            archived           BOOLEAN NOT NULL DEFAULT FALSE,
            created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            collection_id      INTEGER REFERENCES collection(id) ON DELETE SET NULL,
            entity_id          CHAR(21) UNIQUE
        )
    """))

    # persisted_info (cached questions)
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS persisted_info (
            id                 INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            database_id        INTEGER NOT NULL REFERENCES metabase_database(id) ON DELETE CASCADE,
            card_id            INTEGER NOT NULL UNIQUE REFERENCES report_card(id),
            question_slug      TEXT NOT NULL,
            table_name         TEXT NOT NULL,
            definition         TEXT,
            query_hash         TEXT,
            active             BOOLEAN NOT NULL DEFAULT FALSE,
            state              TEXT NOT NULL,
            refresh_begin      TIMESTAMPTZ NOT NULL,
            refresh_end        TIMESTAMPTZ,
            state_change_at    TIMESTAMPTZ,
            error              TEXT,
            created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            creator_id         INTEGER REFERENCES core_user(id)
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_metabase_version_tables(conn, applied: list[str]) -> None:
    """Tabelas de versionamento do Metabase."""
    name = "metabase_version_tables.create_v1"
    if _migration_applied(conn, name):
        return

    # databasechangelog
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS databasechangelog (
            id            VARCHAR(255) NOT NULL,
            author        VARCHAR(255) NOT NULL,
            filename      VARCHAR(255) NOT NULL,
            dateexecuted  TIMESTAMP NOT NULL,
            orderexecuted INTEGER NOT NULL,
            exectype      VARCHAR(10) NOT NULL,
            md5sum        VARCHAR(35),
            description   VARCHAR(255),
            comments      VARCHAR(255),
            tag           VARCHAR(255),
            liquibase     VARCHAR(20),
            contexts      VARCHAR(255),
            labels        VARCHAR(255),
            deployment_id VARCHAR(10),
            CONSTRAINT idx_databasechangelog_id_author_filename UNIQUE (id, author, filename)
        )
    """))

    # databasechangeloglock
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS databasechangeloglock (
            id          INTEGER NOT NULL PRIMARY KEY,
            locked      BOOLEAN NOT NULL,
            lockgranted TIMESTAMP,
            lockedby    VARCHAR(255)
        )
    """))

    # setting
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS setting (
            key   VARCHAR(254) NOT NULL PRIMARY KEY,
            value TEXT NOT NULL
        )
    """))

    # task_history
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS task_history (
            id            INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            task          VARCHAR(254) NOT NULL,
            db_id         INTEGER REFERENCES metabase_database(id),
            started_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ended_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            duration      INTEGER NOT NULL,
            task_details  TEXT
        )
    """))

    # secret
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS secret (
            id           INTEGER PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
            version      INTEGER NOT NULL DEFAULT 1,
            creator_id   INTEGER REFERENCES core_user(id),
            created_at   TIMESTAMPTZ NOT NULL,
            updated_at   TIMESTAMPTZ,
            name         VARCHAR(254) NOT NULL,
            kind         VARCHAR(254) NOT NULL,
            source       VARCHAR(254),
            value        BYTEA NOT NULL,
            PRIMARY KEY (id, version)
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 16 — Funções, Triggers e Views Materializadas
# ============================================================================

def _create_functions(conn, applied: list[str]) -> None:
    """Cria todas as funções PL/pgSQL do sistema."""
    name = "functions.create_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    # Função de cálculo de gateway fee
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION calculate_gateway_fee(
            p_amount_cents INTEGER,
            p_payment_method VARCHAR,
            p_card_brand VARCHAR,
            p_installments INTEGER DEFAULT 1
        ) RETURNS INTEGER AS $$
        DECLARE
            v_fee_pct DECIMAL(5,4);
            v_fee_cents INTEGER;
            v_installment_fee_cents INTEGER := 0;
        BEGIN
            v_fee_pct := CASE 
                WHEN p_payment_method IN ('creditCard', 'CARTAO_CREDITO') THEN 
                    CASE 
                        WHEN p_card_brand IN ('amex', 'elite') THEN 0.045
                        ELSE 0.039
                    END
                WHEN p_payment_method IN ('debitCard', 'CARTAO_DEBITO') THEN 0.025
                WHEN p_payment_method = 'pix' THEN 0.008
                WHEN p_payment_method = 'boleto' THEN 0.025
                WHEN p_payment_method IN ('apple_pay', 'google_pay') THEN 0.035
                ELSE 0.03
            END;
            
            IF p_installments > 1 THEN
                v_installment_fee_cents := ROUND(p_amount_cents * 0.005 * (p_installments - 1));
            END IF;
            
            v_fee_cents := ROUND(p_amount_cents * v_fee_pct) + v_installment_fee_cents;
            RETURN LEAST(v_fee_cents, p_amount_cents * 0.1);
        END;
        $$ LANGUAGE plpgsql IMMUTABLE
    """))

    # Função de derivar evidência
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION fn_derive_evidence_strength(p_score INTEGER)
        RETURNS VARCHAR AS $$
        SELECT CASE
            WHEN COALESCE(p_score, 0) = 0 THEN 'NONE'
            WHEN p_score BETWEEN 1 AND 39 THEN 'WEAK'
            WHEN p_score BETWEEN 40 AND 79 THEN 'MEDIUM'
            WHEN p_score BETWEEN 80 AND 99 THEN 'STRONG'
            WHEN p_score = 100 THEN 'FINAL'
            ELSE NULL
        END;
        $$ LANGUAGE sql IMMUTABLE
    """))

    # Função de atualização de updated_at
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """))

    # Função de set_row_updated_at
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION set_row_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_triggers(conn, applied: list[str]) -> None:
    """Cria todos os triggers do sistema."""
    name = "triggers.create_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    # Trigger para payment_transactions
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION trg_payment_transactions_calc_fees()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.status = 'APPROVED' AND NEW.gateway_fee_cents IS NULL THEN
                NEW.gateway_fee_cents := calculate_gateway_fee(
                    NEW.amount_cents,
                    NEW.payment_method,
                    NEW.card_brand,
                    COALESCE(NEW.installments, 1)
                );
                NEW.net_amount_cents := NEW.amount_cents - NEW.gateway_fee_cents;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """))
    conn.execute(text("DROP TRIGGER IF EXISTS trg_payment_transactions_calc_fees ON payment_transactions"))
    conn.execute(text("CREATE TRIGGER trg_payment_transactions_calc_fees BEFORE INSERT OR UPDATE OF status ON payment_transactions FOR EACH ROW EXECUTE FUNCTION trg_payment_transactions_calc_fees()"))

    # Trigger para slot_occupancy_history
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION trg_log_slot_state_change()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.status IS DISTINCT FROM OLD.status THEN
                INSERT INTO slot_occupancy_history (
                    locker_id, slot_label, allocation_id,
                    previous_state, current_state, triggered_by, metadata
                ) VALUES (
                    NEW.locker_id, NEW.slot_label, NEW.current_allocation_id,
                    OLD.status, NEW.status, 'SYSTEM',
                    jsonb_build_object('fault_code', NEW.fault_code)
                );
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """))
    conn.execute(text("DROP TRIGGER IF EXISTS trg_slot_occupancy_history ON locker_slots"))
    conn.execute(text("CREATE TRIGGER trg_slot_occupancy_history AFTER UPDATE ON locker_slots FOR EACH ROW EXECUTE FUNCTION trg_log_slot_state_change()"))

    # Trigger para pickups sync
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION trg_pickups_sync_v2_derived()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.evidence_score := COALESCE(NEW.evidence_score, 0);
            IF NEW.dispute_state IS NULL THEN
                NEW.dispute_state := 'NONE';
            END IF;
            NEW.evidence_strength := fn_derive_evidence_strength(NEW.evidence_score);
            IF NEW.pickup_phase = 'COMPLETED_VERIFIED' AND NEW.verified_at IS NULL THEN
                NEW.verified_at := now();
            END IF;
            IF NEW.redeemed_via = 'BLE' AND NEW.pickup_phase = 'COMPLETED_UNVERIFIED' THEN
                NEW.evidence_score := GREATEST(NEW.evidence_score, 85);
                NEW.evidence_strength := fn_derive_evidence_strength(NEW.evidence_score);
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """))
    conn.execute(text("DROP TRIGGER IF EXISTS trg_pickups_sync_v2_derived ON pickups"))
    conn.execute(text("CREATE TRIGGER trg_pickups_sync_v2_derived BEFORE INSERT OR UPDATE OF evidence_score, pickup_phase, dispute_state ON pickups FOR EACH ROW EXECUTE FUNCTION trg_pickups_sync_v2_derived()"))

    _mark_migration(conn, name)
    applied.append(name)


# Continuação do BLOCO 16 — Funções, Triggers e Views Materializadas (parte 2)

def _create_materialized_views(conn, applied: list[str]) -> None:
    """Cria todas as materialized views do sistema."""
    name = "materialized_views.create_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    # ... (código anterior das MVs) ...

    # mv_realtime_kpis (continuação)
    conn.execute(text("""
        DROP MATERIALIZED VIEW IF EXISTS mv_realtime_kpis CASCADE;
        CREATE MATERIALIZED VIEW mv_realtime_kpis AS
        WITH last_hour_stats AS (
            SELECT COUNT(DISTINCT id) AS orders_last_hour,
                   SUM(amount_cents) / 100 AS revenue_last_hour
            FROM orders
            WHERE created_at >= NOW() - INTERVAL '1 hour'
              AND deleted_at IS NULL
        ),
        last_24h_stats AS (
            SELECT COUNT(DISTINCT id) AS orders_last_24h,
                   COUNT(DISTINCT user_id) AS unique_customers_24h,
                   SUM(amount_cents) / 100 AS revenue_last_24h
            FROM orders
            WHERE created_at >= NOW() - INTERVAL '24 hours'
              AND deleted_at IS NULL
        ),
        pickup_stats AS (
            SELECT AVG(EXTRACT(epoch FROM (redeemed_at - activated_at)) / 60)::integer AS avg_pickup_minutes
            FROM pickups
            WHERE redeemed_at >= NOW() - INTERVAL '24 hours'
        ),
        offline_lockers AS (
            SELECT COUNT(DISTINCT id) AS offline_lockers
            FROM lockers
            WHERE active = false AND deleted_at IS NULL
        ),
        active_sellers AS (
            SELECT COUNT(DISTINCT id) AS active_sellers
            FROM marketplace_sellers
            WHERE status = 'ACTIVE'
        ),
        pending_orders AS (
            SELECT COUNT(CASE WHEN status = 'PAYMENT_PENDING' THEN 1 END) AS pending_payment,
                   COUNT(CASE WHEN status = 'PAID_PENDING_PICKUP' AND pickup_deadline_at < NOW() THEN 1 END) AS expired_pickup
            FROM orders
            WHERE deleted_at IS NULL
        ),
        alert_summary AS (
            SELECT COUNT(CASE WHEN severity = 'CRITICAL' AND resolved_at IS NULL THEN 1 END) AS critical_alerts,
                   COUNT(CASE WHEN severity = 'HIGH' AND resolved_at IS NULL THEN 1 END) AS high_alerts
            FROM sla_breach_events
            WHERE detected_at >= NOW() - INTERVAL '24 hours'
        )
        SELECT NOW() AS snapshot_time,
               lh.orders_last_hour,
               lh.revenue_last_hour,
               l24.orders_last_24h,
               l24.unique_customers_24h,
               l24.revenue_last_24h,
               ps.avg_pickup_minutes,
               ol.offline_lockers,
               asellers.active_sellers,
               po.pending_payment,
               po.expired_pickup,
               als.critical_alerts,
               als.high_alerts
        FROM last_hour_stats lh
        CROSS JOIN last_24h_stats l24
        CROSS JOIN pickup_stats ps
        CROSS JOIN offline_lockers ol
        CROSS JOIN active_sellers asellers
        CROSS JOIN pending_orders po
        CROSS JOIN alert_summary als;
    """))

    # Criar índices únicos para as MVs
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_ml_features_daily_mv_locker_date ON ml_features_daily_mv (locker_id, feature_date)"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_locker_pnl_pk ON mv_locker_monthly_pnl (month_ref, locker_id)"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_profitability_locker_month ON mv_locker_monthly_profitability (locker_id, month)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_mv_profitability_month ON mv_locker_monthly_profitability (month DESC)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_mv_profitability_net_profit ON mv_locker_monthly_profitability (net_profit_cents DESC)"))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 17 — Views Analíticas
# ============================================================================

def _create_analytical_views(conn, applied: list[str]) -> None:
    """Cria todas as views analíticas do sistema."""
    name = "analytical_views.create_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    # v_locker_roi_analysis
    conn.execute(text("DROP VIEW IF EXISTS v_locker_roi_analysis CASCADE"))
    conn.execute(text("""
        CREATE VIEW v_locker_roi_analysis AS
        WITH locker_investment AS (
            SELECT l.id AS locker_id, l.external_id, l.display_name, l.city, l.region,
                   l.created_at AS installation_date,
                   COALESCE(lcd.equipment_cost_cents, 0) + COALESCE(lcd.installation_cost_cents, 0) +
                   COALESCE(lcd.connectivity_setup_cents, 0) + COALESCE(lcd.go_live_cost_cents, 0) AS total_capex_cents,
                   lcd.useful_life_months, lcd.salvage_value_cents
            FROM lockers l
            LEFT JOIN locker_capex_details lcd ON lcd.locker_id = l.id
            WHERE l.active = true OR l.deleted_at IS NULL
        ),
        locker_profitability AS (
            SELECT locker_id, AVG(net_profit_cents) AS avg_monthly_profit_cents,
                   STDDEV(net_profit_cents) AS profit_volatility_cents,
                   MIN(month) AS first_profit_month, COUNT(*) AS months_operating,
                   SUM(net_profit_cents) AS cumulative_profit_cents
            FROM mv_locker_monthly_profitability
            WHERE net_profit_cents > 0
            GROUP BY locker_id
        ),
        locker_performance AS (
            SELECT locker_id, COUNT(*) AS total_months,
                   SUM(sales_revenue_cents) AS lifetime_revenue_cents,
                   SUM(total_costs_cents) AS lifetime_costs_cents,
                   SUM(net_profit_cents) AS lifetime_profit_cents,
                   AVG(net_margin_pct) AS avg_margin_pct,
                   MAX(CASE WHEN net_profit_cents > 0 THEN month END) AS last_profitable_month
            FROM mv_locker_monthly_profitability
            GROUP BY locker_id
        )
        SELECT li.locker_id, li.external_id, li.display_name, li.city, li.region,
               li.installation_date, ROUND(li.total_capex_cents / 100.0, 2) AS total_investment_brl,
               li.useful_life_months AS expected_life_months,
               ROUND(COALESCE(li.salvage_value_cents, 0) / 100.0, 2) AS salvage_value_brl,
               COALESCE(lp.avg_monthly_profit_cents, 0) / 100.0 AS avg_monthly_profit_brl,
               COALESCE(lp.profit_volatility_cents, 0) / 100.0 AS profit_volatility_brl,
               COALESCE(lp.first_profit_month::text, 'N/A') AS first_profit_month,
               COALESCE(lp.months_operating, 0) AS months_to_profitability,
               COALESCE(lperf.lifetime_revenue_cents, 0) / 100.0 AS lifetime_revenue_brl,
               COALESCE(lperf.lifetime_costs_cents, 0) / 100.0 AS lifetime_costs_brl,
               COALESCE(lperf.lifetime_profit_cents, 0) / 100.0 AS lifetime_profit_brl,
               ROUND(COALESCE(lperf.avg_margin_pct, 0), 2) AS avg_margin_pct,
               CASE WHEN COALESCE(lp.avg_monthly_profit_cents, 0) > 0
                    THEN ROUND(li.total_capex_cents / lp.avg_monthly_profit_cents, 1)
                    ELSE NULL END AS payback_months,
               CASE WHEN li.total_capex_cents > 0
                    THEN ROUND((100.0 * COALESCE(lp.avg_monthly_profit_cents, 0) * 12) / li.total_capex_cents, 2)
                    ELSE NULL END AS annual_roi_pct,
               CASE WHEN COALESCE(lp.avg_monthly_profit_cents, 0) <= 0 THEN 'INVIABLE'
                    WHEN li.total_capex_cents / lp.avg_monthly_profit_cents <= 12 THEN 'HIGH_PERFORMANCE'
                    WHEN li.total_capex_cents / lp.avg_monthly_profit_cents <= 24 THEN 'MODERATE'
                    WHEN li.total_capex_cents / lp.avg_monthly_profit_cents <= 36 THEN 'LOW_PERFORMANCE'
                    ELSE 'UNDERPERFORMING' END AS viability_classification,
               CASE WHEN COALESCE(lp.avg_monthly_profit_cents, 0) <= 0 THEN 'CONSIDER_RELOCATION_OR_RETIREMENT'
                    WHEN li.total_capex_cents / lp.avg_monthly_profit_cents <= 12 THEN 'EXPAND_NETWORK'
                    WHEN li.total_capex_cents / lp.avg_monthly_profit_cents <= 24 THEN 'OPTIMIZE_OPERATIONS'
                    ELSE 'REVIEW_PRICING_AND_COSTS' END AS recommendation,
               CASE WHEN lperf.last_profitable_month < (CURRENT_DATE - INTERVAL '3 months')::date THEN 'CONSECUTIVE_LOSSES'
                    WHEN COALESCE(lperf.avg_margin_pct, 0) < 15 THEN 'LOW_MARGIN'
                    ELSE 'OK' END AS alert_status,
               NOW() AS computed_at
        FROM locker_investment li
        LEFT JOIN locker_profitability lp ON lp.locker_id = li.locker_id
        LEFT JOIN locker_performance lperf ON lperf.locker_id = li.locker_id
        ORDER BY CASE WHEN COALESCE(lp.avg_monthly_profit_cents, 0) <= 0 THEN 3
                      WHEN li.total_capex_cents / lp.avg_monthly_profit_cents <= 12 THEN 1
                      WHEN li.total_capex_cents / lp.avg_monthly_profit_cents <= 24 THEN 2
                      ELSE 4 END, COALESCE(lp.avg_monthly_profit_cents, 0) DESC
    """))

    # v_financial_dashboard
    conn.execute(text("DROP VIEW IF EXISTS v_financial_dashboard CASCADE"))
    conn.execute(text("""
        CREATE VIEW v_financial_dashboard AS
        WITH current_month_metrics AS (
            SELECT date_trunc('month', CURRENT_DATE)::date AS current_month,
                   SUM(sales_revenue_cents) AS mtd_revenue_cents,
                   SUM(total_costs_cents) AS mtd_costs_cents,
                   SUM(net_profit_cents) AS mtd_profit_cents,
                   AVG(net_margin_pct) AS avg_margin_pct,
                   COUNT(DISTINCT locker_id) AS active_lockers
            FROM mv_locker_monthly_profitability
            WHERE month = date_trunc('month', CURRENT_DATE)::date
        ),
        rolling_12m AS (
            SELECT SUM(sales_revenue_cents) AS last_12m_revenue_cents,
                   SUM(net_profit_cents) AS last_12m_profit_cents,
                   SUM(total_pickups) AS last_12m_pickups
            FROM mv_locker_monthly_profitability
            WHERE month >= date_trunc('month', CURRENT_DATE - INTERVAL '1 year')::date
        ),
        underperforming_lockers AS (
            SELECT COUNT(*) AS underperforming_count
            FROM v_locker_roi_analysis
            WHERE viability_classification IN ('UNDERPERFORMING', 'INVIABLE')
        )
        SELECT COALESCE((SELECT mtd_revenue_cents FROM current_month_metrics) / 100.0, 0) AS revenue_mtd_brl,
               COALESCE((SELECT mtd_costs_cents FROM current_month_metrics) / 100.0, 0) AS costs_mtd_brl,
               COALESCE((SELECT mtd_profit_cents FROM current_month_metrics) / 100.0, 0) AS profit_mtd_brl,
               COALESCE(ROUND((SELECT avg_margin_pct FROM current_month_metrics), 2), 0) AS margin_mtd_pct,
               COALESCE((SELECT last_12m_revenue_cents FROM rolling_12m) / 100.0, 0) AS revenue_ltm_brl,
               COALESCE((SELECT last_12m_profit_cents FROM rolling_12m) / 100.0, 0) AS profit_ltm_brl,
               COALESCE((SELECT last_12m_pickups FROM rolling_12m), 0) AS total_pickups_ltm,
               COALESCE(ROUND((SELECT last_12m_profit_cents FROM rolling_12m) / NULLIF((SELECT last_12m_revenue_cents FROM rolling_12m), 0) * 100, 2), 0) AS ltm_margin_pct,
               COALESCE((SELECT COUNT(*) FROM lockers WHERE active = true), 0) AS total_active_lockers,
               COALESCE((SELECT underperforming_count FROM underperforming_lockers), 0) AS underperforming_lockers,
               COALESCE(ROUND(100.0 * (SELECT underperforming_count FROM underperforming_lockers) / NULLIF((SELECT COUNT(*) FROM lockers WHERE active = true), 0), 2), 0) AS pct_underperforming,
               40.0 AS target_ebitda_margin_pct,
               12.0 AS target_payback_months,
               24.0 AS max_acceptable_payback,
               NOW() AS computed_at
    """))

    # vw_ceo_occupancy
    conn.execute(text("DROP VIEW IF EXISTS vw_ceo_occupancy CASCADE"))
    conn.execute(text("""
        CREATE VIEW vw_ceo_occupancy AS
        WITH current_occupancy AS (
            SELECT l.id AS locker_id, l.external_id, l.region, l.city, l.address_line,
                   COUNT(ls.id) AS total_slots,
                   COUNT(CASE WHEN ls.status = 'OCCUPIED' THEN 1 END) AS occupied_slots,
                   COUNT(CASE WHEN ls.status = 'MAINTENANCE' THEN 1 END) AS maintenance_slots,
                   MAX(CASE WHEN o.status = 'PAID_PENDING_PICKUP' AND o.picked_up_at IS NULL THEN 1 ELSE 0 END) AS has_pending_pickup
            FROM lockers l
            LEFT JOIN locker_slots ls ON ls.locker_id = l.id
            LEFT JOIN allocations a ON a.locker_id = l.id AND a.state IN ('RESERVED_PAID_PENDING_PICKUP', 'OPENED_FOR_PICKUP')
            LEFT JOIN orders o ON o.id = a.order_id AND o.picked_up_at IS NULL
            WHERE l.active = true AND l.deleted_at IS NULL
            GROUP BY l.id, l.external_id, l.region, l.city, l.address_line
        )
        SELECT locker_id, external_id, region, city, address_line,
               total_slots, occupied_slots, maintenance_slots,
               ROUND((occupied_slots::numeric / NULLIF(total_slots, 0)) * 100, 2) AS occupancy_pct,
               has_pending_pickup = 1 AS has_urgent_pickup,
               CASE WHEN occupied_slots::numeric / NULLIF(total_slots, 0) >= 0.8 THEN 'HIGH'
                    WHEN occupied_slots::numeric / NULLIF(total_slots, 0) >= 0.5 THEN 'MEDIUM'
                    ELSE 'LOW' END AS occupancy_level
        FROM current_occupancy
    """))

    # vw_ceo_revenue
    conn.execute(text("DROP VIEW IF EXISTS vw_ceo_revenue CASCADE"))
    conn.execute(text("""
        CREATE VIEW vw_ceo_revenue AS
        SELECT date_trunc('month', o.picked_up_at) AS month_ref, o.region, o.channel,
               COUNT(DISTINCT o.id) AS total_orders,
               SUM(o.amount_cents) / 100 AS gross_revenue,
               SUM(CASE WHEN o.status = 'REFUNDED' THEN o.amount_cents ELSE 0 END) / 100 AS refunded_amount,
               (SUM(o.amount_cents) - SUM(CASE WHEN o.status = 'REFUNDED' THEN o.amount_cents ELSE 0 END)) / 100 AS net_revenue,
               COUNT(DISTINCT o.user_id) AS unique_customers,
               ROUND(((SUM(o.amount_cents) - SUM(CASE WHEN o.status = 'REFUNDED' THEN o.amount_cents ELSE 0 END))::numeric / NULLIF(COUNT(DISTINCT o.id), 0)) / 100, 2) AS avg_ticket
        FROM orders o
        WHERE o.picked_up_at IS NOT NULL AND o.deleted_at IS NULL
          AND o.status IN ('PICKED_UP', 'REFUNDED')
        GROUP BY date_trunc('month', o.picked_up_at), o.region, o.channel
        ORDER BY month_ref DESC, region, channel
    """))

    # vw_cfo_financial
    conn.execute(text("DROP VIEW IF EXISTS vw_cfo_financial CASCADE"))
    conn.execute(text("""
        CREATE VIEW vw_cfo_financial AS
        WITH wallet_balance AS (
            SELECT SUM(balance_cents) AS total_wallet_balance_cents,
                   COUNT(DISTINCT user_id) AS users_with_balance
            FROM user_wallets
            WHERE status = 'ACTIVE'
        ),
        disputes AS (
            SELECT COUNT(*) AS open_disputes,
                   SUM(hold_amount_cents) AS total_hold_cents
            FROM partner_payment_holds
            WHERE status = 'HELD'
        ),
        pending_credits AS (
            SELECT COUNT(*) AS pending_credit_notes,
                   SUM(amount_cents) AS total_credit_cents
            FROM partner_credit_notes
            WHERE status = 'PENDING'
        )
        SELECT COALESCE(SUM(o.amount_cents), 0) / 100 AS gross_revenue_mtd,
               COALESCE(SUM(CASE WHEN o.status = 'REFUNDED' THEN o.amount_cents ELSE 0 END), 0) / 100 AS refunds_mtd,
               (COALESCE(SUM(o.amount_cents), 0) - COALESCE(SUM(CASE WHEN o.status = 'REFUNDED' THEN o.amount_cents ELSE 0 END), 0)) / 100 AS net_revenue_mtd,
               wb.total_wallet_balance_cents / 100.0 AS total_wallet_balance,
               wb.users_with_balance,
               d.open_disputes,
               d.total_hold_cents / 100.0 AS total_dispute_holds,
               pc.pending_credit_notes,
               pc.total_credit_cents / 100.0 AS pending_credits_total
        FROM orders o
        CROSS JOIN wallet_balance wb
        CROSS JOIN disputes d
        CROSS JOIN pending_credits pc
        WHERE o.picked_up_at >= date_trunc('month', CURRENT_DATE)
          AND o.picked_up_at IS NOT NULL
          AND o.deleted_at IS NULL
        GROUP BY wb.total_wallet_balance_cents, wb.users_with_balance,
                 d.open_disputes, d.total_hold_cents,
                 pc.pending_credit_notes, pc.total_credit_cents
    """))

    # vw_coo_operations
    conn.execute(text("DROP VIEW IF EXISTS vw_coo_operations CASCADE"))
    conn.execute(text("""
        CREATE VIEW vw_coo_operations AS
        SELECT CURRENT_DATE AS snapshot_date,
               COUNT(DISTINCT o.id) FILTER (WHERE o.created_at >= CURRENT_DATE) AS orders_created_today,
               COUNT(DISTINCT o.id) FILTER (WHERE o.paid_at >= CURRENT_DATE) AS orders_paid_today,
               COUNT(DISTINCT o.id) FILTER (WHERE o.picked_up_at >= CURRENT_DATE) AS orders_picked_up_today,
               COUNT(DISTINCT p.id) FILTER (WHERE p.redeemed_at >= CURRENT_DATE) AS pickups_completed_today,
               COUNT(DISTINCT sbe.id) FILTER (WHERE sbe.detected_at >= CURRENT_DATE AND sbe.severity = 'CRITICAL') AS critical_sla_breaches_today,
               (AVG(EXTRACT(epoch FROM (p.redeemed_at - p.activated_at)) / 60))::integer AS avg_pickup_minutes_last_24h,
               COUNT(DISTINCT l.id) FILTER (WHERE l.active = false) AS offline_lockers
        FROM orders o
        LEFT JOIN pickups p ON p.order_id = o.id
        LEFT JOIN sla_breach_events sbe ON sbe.delivery_id = p.id::text
        CROSS JOIN lockers l
        WHERE o.deleted_at IS NULL
    """))

    # vw_maintenance_alerts
    conn.execute(text("DROP VIEW IF EXISTS vw_maintenance_alerts CASCADE"))
    conn.execute(text("""
        CREATE VIEW vw_maintenance_alerts AS
        WITH telemetry_issues AS (
            SELECT DISTINCT ON (locker_id) locker_id, event_type, occurred_at, battery_pct,
                   CASE WHEN event_type = 'DOOR_FAILURE' THEN 'CRITICO'
                        WHEN event_type = 'BATTERY_LOW' AND COALESCE(battery_pct, 100) < 10 THEN 'CRITICO'
                        WHEN event_type = 'BATTERY_LOW' AND COALESCE(battery_pct, 100) < 20 THEN 'ALTA'
                        WHEN event_type = 'SIGNAL_LOST' THEN 'CRITICO'
                        WHEN event_type = 'TEMPERATURE_ALERT' THEN 'ALTA'
                        ELSE 'NORMAL' END AS severity,
                   CASE WHEN event_type = 'DOOR_FAILURE' THEN 'Falha na porta do locker'
                        WHEN event_type = 'BATTERY_LOW' THEN ('Bateria fraca (' || COALESCE(battery_pct, 0)::integer || '%)')::varchar
                        WHEN event_type = 'SIGNAL_LOST' THEN 'Conexão perdida'
                        WHEN event_type = 'TEMPERATURE_ALERT' THEN 'Temperatura fora da faixa ideal'
                        ELSE event_type END AS description
            FROM locker_telemetry
            WHERE occurred_at >= CURRENT_DATE - INTERVAL '2 days'
              AND event_type IN ('DOOR_FAILURE', 'BATTERY_LOW', 'SIGNAL_LOST', 'TEMPERATURE_ALERT')
            ORDER BY locker_id, occurred_at DESC
        )
        SELECT ti.locker_id, l.display_name AS locker_name, l.address_line, l.city,
               ti.event_type, ti.severity, ti.description, ti.occurred_at,
               EXTRACT(epoch FROM (CURRENT_TIMESTAMP - ti.occurred_at)) / 3600 AS hours_ago,
               'Pendente' AS sla_status
        FROM telemetry_issues ti
        LEFT JOIN lockers l ON l.id = ti.locker_id
        WHERE ti.severity IN ('CRITICO', 'ALTA')
        ORDER BY CASE ti.severity WHEN 'CRITICO' THEN 1 WHEN 'ALTA' THEN 2 ELSE 3 END, ti.occurred_at
    """))

    # vw_support_active_tickets
    conn.execute(text("DROP VIEW IF EXISTS vw_support_active_tickets CASCADE"))
    conn.execute(text("""
        CREATE VIEW vw_support_active_tickets AS
        WITH open_tickets AS (
            SELECT o.id AS ticket_id, ('ORDER_' || o.id) AS ticket_number, o.user_id,
                   o.status::text AS status, o.created_at, NULL AS escalated_at,
                   'OPEN' AS ticket_status,
                   CASE WHEN o.status = 'PAYMENT_PENDING' AND o.created_at < CURRENT_DATE - INTERVAL '1 day' THEN 'PAYMENT_OVERDUE'
                        WHEN o.status = 'PAID_PENDING_PICKUP' AND o.pickup_deadline_at < CURRENT_DATE THEN 'PICKUP_EXPIRED'
                        ELSE 'ORDER_ISSUE' END AS reason,
                   2 AS priority
            FROM orders o
            WHERE o.deleted_at IS NULL
              AND o.status NOT IN ('PICKED_UP', 'CANCELLED', 'REFUNDED')
              AND ((o.status = 'PAYMENT_PENDING' AND o.created_at < CURRENT_DATE - INTERVAL '1 day')
                OR (o.status = 'PAID_PENDING_PICKUP' AND o.pickup_deadline_at < CURRENT_DATE))
            UNION ALL
            SELECT sbe.id::text AS ticket_id, ('SLA_' || sbe.id) AS ticket_number, NULL AS user_id,
                   sbe.breach_type AS status, sbe.detected_at AS created_at,
                   CASE WHEN sbe.severity = 'CRITICAL' THEN sbe.detected_at + INTERVAL '30 minutes' ELSE NULL END AS escalated_at,
                   CASE WHEN sbe.resolved_at IS NULL THEN 'OPEN' ELSE 'RESOLVED' END AS ticket_status,
                   sbe.breach_type AS reason,
                   CASE sbe.severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END AS priority
            FROM sla_breach_events sbe
            WHERE sbe.resolved_at IS NULL
        )
        SELECT ticket_id, ticket_number, user_id, status, created_at, escalated_at,
               ticket_status, reason, priority,
               CASE WHEN priority = 1 THEN 'CRITICO' WHEN priority = 2 THEN 'ALTA' ELSE 'NORMAL' END AS priority_label,
               EXTRACT(epoch FROM (CURRENT_DATE::timestamptz - created_at)) / 3600 AS hours_open
        FROM open_tickets
        ORDER BY priority, created_at
    """))

    # vw_noc_alerts
    conn.execute(text("DROP VIEW IF EXISTS vw_noc_alerts CASCADE"))
    conn.execute(text("""
        CREATE VIEW vw_noc_alerts AS
        SELECT 'SLA_BREACH' AS alert_type, sbe.id AS alert_id, sbe.severity,
               sbe.breach_type, sbe.detected_at, sbe.expected_at, sbe.resolved_at,
               COALESCE(ld.display_name, sbe.delivery_id) AS locker_display_name,
               COALESCE(ld.external_id, sbe.delivery_id) AS reference_id,
               CASE WHEN sbe.severity IN ('CRITICAL', 'HIGH') AND sbe.resolved_at IS NULL THEN 1 ELSE 2 END AS priority
        FROM sla_breach_events sbe
        LEFT JOIN inbound_deliveries ind ON ind.id = sbe.delivery_id
        LEFT JOIN lockers ld ON ld.id = ind.locker_id
        WHERE sbe.resolved_at IS NULL AND sbe.detected_at >= CURRENT_DATE - INTERVAL '7 days'
        UNION ALL
        SELECT 'LOCKER_OFFLINE', l.id, 'CRITICAL', 'NETWORK_DOWN',
               l.updated_at, l.updated_at + INTERVAL '1 hour', NULL,
               l.display_name, l.external_id, 1
        FROM lockers l
        WHERE l.active = false AND l.deleted_at IS NULL
        UNION ALL
        SELECT 'RISK_EVENT', pgre.id, CASE WHEN pgre.decision = 'BLOCK' THEN 'CRITICAL' WHEN pgre.decision = 'CHALLENGE' THEN 'HIGH' ELSE 'MEDIUM' END,
               pgre.event_type, pgre.created_at, NULL, NULL,
               COALESCE(l.display_name, pgre.locker_id), pgre.locker_id,
               CASE WHEN pgre.decision = 'BLOCK' THEN 1 ELSE 2 END
        FROM payment_gateway_risk_events pgre
        LEFT JOIN lockers l ON l.id = pgre.locker_id
        WHERE pgre.created_at >= CURRENT_DATE - INTERVAL '1 day'
          AND pgre.decision IN ('BLOCK', 'CHALLENGE')
        ORDER BY priority, detected_at DESC
    """))

    # vw_ml_dashboard
    conn.execute(text("DROP VIEW IF EXISTS vw_ml_dashboard CASCADE"))
    conn.execute(text("""
        CREATE VIEW vw_ml_dashboard AS
        SELECT mmm.model_version, mmm.trained_at, mmm.status, mmm.metrics_json,
               COUNT(DISTINCT mpl.locker_id) AS active_lockers,
               AVG(mpl.failure_probability) AS avg_failure_probability,
               AVG(mpl.health_score) AS avg_health_score
        FROM ml_model_metadata mmm
        LEFT JOIN ml_predictions_log mpl ON mpl.model_version = mmm.model_version
        WHERE mmm.status = 'ACTIVE' AND mpl.predicted_at >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY mmm.model_version, mmm.trained_at, mmm.status, mmm.metrics_json
    """))

    # invoice_order_view
    conn.execute(text("DROP VIEW IF EXISTS invoice_order_view CASCADE"))
    conn.execute(text("""
        CREATE VIEW invoice_order_view AS
        SELECT i.id AS invoice_id, i.order_id, i.tenant_id, i.region, i.country,
               i.status::text AS invoice_status, i.locker_id, i.totem_id, i.slot_label,
               i.amount_cents, i.currency, i.created_at, i.issued_at,
               i.items_json, i.order_snapshot, i.order_snapshot -> 'order' AS order_json,
               i.order_snapshot -> 'order_items' AS order_items_snapshot,
               COALESCE(i.items_json -> 'lines', '[]'::jsonb) AS items_lines
        FROM invoices i
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_geodata_tables(conn, applied: list[str]) -> None:
    """Cria tabelas geoespaciais no schema geodata."""
    name = "geodata_tables.create_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS geodata.test_points (
            id         SERIAL PRIMARY KEY,
            name       VARCHAR(100),
            geom       GEOMETRY(Point, 4326),
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_analytics_schema_tables(conn, applied: list[str]) -> None:
    """Cria tabelas analíticas no schema analytics_analytics."""
    name = "analytics_schema_tables.create_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    # company_mrr_trend
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS analytics_analytics.company_mrr_trend (
            month_ref            DATE,
            currency             VARCHAR(8),
            mrr_cents            NUMERIC,
            company_deferred_cents NUMERIC,
            active_partner_count BIGINT,
            active_locker_count  BIGINT,
            updated_at           TIMESTAMPTZ
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_company_mrr_trend_month ON analytics_analytics.company_mrr_trend (month_ref DESC)"))

    # locker_pnl
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS analytics_analytics.locker_pnl (
            month_ref          DATE,
            partner_id         VARCHAR(36),
            locker_id          VARCHAR(36),
            currency           VARCHAR(8),
            country_code       VARCHAR(2),
            jurisdiction_code  VARCHAR(32),
            revenue_cents      BIGINT,
            opex_cents         BIGINT,
            depreciation_cents BIGINT,
            gross_profit_cents BIGINT,
            gross_margin_pct   NUMERIC(10,4),
            ebitda_cents       BIGINT,
            net_income_cents   BIGINT,
            ar_open_cents      BIGINT,
            dso_days           NUMERIC(10,2),
            computed_at        TIMESTAMPTZ
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_locker_pnl_month ON analytics_analytics.locker_pnl (month_ref DESC, partner_id)"))

    # partner_revenue_monthly
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS analytics_analytics.partner_revenue_monthly (
            month_ref            DATE,
            partner_id           VARCHAR(36),
            locker_id            VARCHAR(36),
            currency             VARCHAR(8),
            country_code         VARCHAR(2),
            jurisdiction_code    VARCHAR(32),
            revenue_recognized_cents NUMERIC,
            deferred_amount_cents NUMERIC,
            updated_at           TIMESTAMPTZ
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_ellanlab_tables(conn, applied: list[str]) -> None:
    """Cria tabelas do módulo financeiro EllanLab."""
    name = "ellanlab_tables.create_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    # ellanlab_revenue_recognition (TimescaleDB hypertable)
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ellanlab_revenue_recognition (
            id                   BIGSERIAL NOT NULL,
            recognition_date     DATE NOT NULL,
            partner_id           VARCHAR(36) NOT NULL,
            locker_id            VARCHAR(36),
            source_type          VARCHAR(40) NOT NULL,
            source_id            VARCHAR(64) NOT NULL,
            recognition_rule     VARCHAR(40) NOT NULL DEFAULT 'ACCRUAL_DAILY',
            recognized_amount_cents BIGINT NOT NULL,
            deferred_amount_cents BIGINT NOT NULL DEFAULT 0,
            currency             VARCHAR(8) NOT NULL DEFAULT 'BRL',
            country_code         VARCHAR(2),
            jurisdiction_code    VARCHAR(32),
            dedupe_key           VARCHAR(180),
            metadata_json        JSONB NOT NULL DEFAULT '{}',
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (recognition_date, id)
        )
    """))
    conn.execute(text("SELECT create_hypertable('ellanlab_revenue_recognition', 'recognition_date', if_not_exists => TRUE)"))

    # ellanlab_opex_entries
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ellanlab_opex_entries (
            id                   VARCHAR(36) PRIMARY KEY,
            expense_date         DATE NOT NULL,
            expense_month        DATE NOT NULL,
            partner_id           VARCHAR(36),
            locker_id            VARCHAR(36),
            cost_center_code     VARCHAR(32),
            category             VARCHAR(40) NOT NULL,
            description          VARCHAR(255) NOT NULL,
            amount_cents         BIGINT NOT NULL,
            currency             VARCHAR(8) NOT NULL DEFAULT 'BRL',
            country_code         VARCHAR(2),
            jurisdiction_code    VARCHAR(32),
            vendor_ref           VARCHAR(120),
            reference_source     VARCHAR(50) NOT NULL DEFAULT 'manual',
            dedupe_key           VARCHAR(180),
            metadata_json        JSONB NOT NULL DEFAULT '{}',
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    # ellanlab_hardware_assets
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ellanlab_hardware_assets (
            id                   VARCHAR(36) PRIMARY KEY,
            asset_code           VARCHAR(64) NOT NULL UNIQUE,
            locker_id            VARCHAR(36),
            partner_id           VARCHAR(36),
            asset_category       VARCHAR(40) NOT NULL,
            description          VARCHAR(255) NOT NULL,
            acquisition_date     DATE NOT NULL,
            in_service_date      DATE,
            acquisition_cost_cents BIGINT NOT NULL,
            residual_value_cents BIGINT NOT NULL DEFAULT 0,
            useful_life_months   INTEGER NOT NULL,
            depreciation_method  VARCHAR(20) NOT NULL DEFAULT 'STRAIGHT_LINE',
            currency             VARCHAR(8) NOT NULL DEFAULT 'BRL',
            country_code         VARCHAR(2),
            jurisdiction_code    VARCHAR(32),
            status               VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
            metadata_json        JSONB NOT NULL DEFAULT '{}',
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            installation_cost_cents BIGINT NOT NULL DEFAULT 0,
            supplier_name        VARCHAR(140),
            warranty_ends_at     DATE,
            notes                TEXT
        )
    """))

    # ellanlab_depreciation_schedule
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ellanlab_depreciation_schedule (
            id                   BIGSERIAL PRIMARY KEY,
            asset_id             VARCHAR(36) NOT NULL REFERENCES ellanlab_hardware_assets(id) ON DELETE CASCADE,
            depreciation_month   DATE NOT NULL,
            partner_id           VARCHAR(36),
            locker_id            VARCHAR(36),
            depreciation_amount_cents BIGINT NOT NULL,
            accumulated_depreciation_cents BIGINT NOT NULL,
            nbv_cents            BIGINT NOT NULL,
            currency             VARCHAR(8) NOT NULL DEFAULT 'BRL',
            status               VARCHAR(20) NOT NULL DEFAULT 'POSTED',
            dedupe_key           VARCHAR(180),
            metadata_json        JSONB NOT NULL DEFAULT '{}',
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(asset_id, depreciation_month)
        )
    """))

    # ellanlab_monthly_pnl
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ellanlab_monthly_pnl (
            id                   BIGSERIAL NOT NULL,
            pnl_month            DATE NOT NULL,
            partner_id           VARCHAR(36) NOT NULL,
            locker_id            VARCHAR(36),
            currency             VARCHAR(8) NOT NULL DEFAULT 'BRL',
            country_code         VARCHAR(2),
            jurisdiction_code    VARCHAR(32),
            revenue_cents        BIGINT NOT NULL DEFAULT 0,
            cogs_cents           BIGINT NOT NULL DEFAULT 0,
            opex_cents           BIGINT NOT NULL DEFAULT 0,
            depreciation_cents   BIGINT NOT NULL DEFAULT 0,
            gross_profit_cents   BIGINT NOT NULL DEFAULT 0,
            gross_margin_pct     NUMERIC(10,4),
            ebitda_cents         BIGINT NOT NULL DEFAULT 0,
            net_income_cents     BIGINT NOT NULL DEFAULT 0,
            ar_open_cents        BIGINT NOT NULL DEFAULT 0,
            dso_days             NUMERIC(10,2),
            metadata_json        JSONB NOT NULL DEFAULT '{}',
            computed_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (pnl_month, id),
            UNIQUE(partner_id, locker_id, pnl_month)
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_financial_kpi_daily(conn, applied: list[str]) -> None:
    """Cria tabela de KPIs financeiros diários (TimescaleDB hypertable)."""
    name = "financial_kpi_daily.create_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS financial_kpi_daily (
            id                     BIGSERIAL NOT NULL,
            snapshot_date          DATE NOT NULL,
            partner_id             VARCHAR(36) NOT NULL,
            locker_id              VARCHAR(36),
            currency               VARCHAR(8) NOT NULL DEFAULT 'BRL',
            country_code           VARCHAR(2),
            jurisdiction_code      VARCHAR(32),
            revenue_recognized_cents BIGINT NOT NULL DEFAULT 0,
            ar_open_cents          BIGINT NOT NULL DEFAULT 0,
            arpl_cents             BIGINT NOT NULL DEFAULT 0,
            gross_margin_pct       NUMERIC(10,4) NOT NULL DEFAULT 0,
            dso_days               NUMERIC(10,2) NOT NULL DEFAULT 0,
            active_invoice_count   INTEGER NOT NULL DEFAULT 0,
            metadata_json          JSONB NOT NULL DEFAULT '{}',
            dedupe_key             VARCHAR(180),
            computed_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (snapshot_date, id),
            UNIQUE(partner_id, locker_id, snapshot_date)
        )
    """))
    conn.execute(text("SELECT create_hypertable('financial_kpi_daily', 'snapshot_date', if_not_exists => TRUE)"))


def _create_chart_of_accounts(conn, applied: list[str]) -> None:
    """Cria plano de contas contábil."""
    name = "chart_of_accounts.create_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS chart_of_accounts (
            id                   VARCHAR(36) PRIMARY KEY,
            account_code         VARCHAR(32) NOT NULL UNIQUE,
            account_name         VARCHAR(140) NOT NULL,
            account_type         VARCHAR(20) NOT NULL,
            normal_balance       VARCHAR(10) NOT NULL,
            parent_account_id    VARCHAR(36) REFERENCES chart_of_accounts(id),
            currency             VARCHAR(8) NOT NULL DEFAULT 'BRL',
            country_code         VARCHAR(2),
            jurisdiction_code    VARCHAR(32),
            is_active            BOOLEAN NOT NULL DEFAULT TRUE,
            metadata_json        JSONB NOT NULL DEFAULT '{}',
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_coa_type_active ON chart_of_accounts (account_type, is_active)"))


def _create_journal_entries(conn, applied: list[str]) -> None:
    """Cria tabelas do livro diário contábil."""
    name = "journal_entries.create_v1"
    if _migration_applied(conn, name):
        return

    # journal_entries
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS journal_entries (
            id                   VARCHAR(36) PRIMARY KEY,
            entry_date           DATE NOT NULL,
            description          VARCHAR(255) NOT NULL,
            reference_type       VARCHAR(50),
            reference_id         VARCHAR(36),
            reference_source     VARCHAR(50) NOT NULL DEFAULT 'manual',
            dedupe_key           VARCHAR(128) UNIQUE,
            currency             VARCHAR(8) NOT NULL DEFAULT 'BRL',
            is_posted            BOOLEAN NOT NULL DEFAULT FALSE,
            posted_at            TIMESTAMPTZ,
            posted_by            VARCHAR(36),
            created_by           VARCHAR(36),
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    # journal_entry_lines
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS journal_entry_lines (
            id                   BIGSERIAL PRIMARY KEY,
            journal_entry_id     VARCHAR(36) NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
            line_number          INTEGER NOT NULL,
            account_id           VARCHAR(36) NOT NULL REFERENCES chart_of_accounts(id),
            partner_id           VARCHAR(36),
            locker_id            VARCHAR(36),
            description          VARCHAR(255),
            debit_amount         NUMERIC(16,2) NOT NULL DEFAULT 0,
            credit_amount        NUMERIC(16,2) NOT NULL DEFAULT 0,
            currency             VARCHAR(8) NOT NULL DEFAULT 'BRL',
            country_code         VARCHAR(2),
            jurisdiction_code    VARCHAR(32),
            reference_source     VARCHAR(50) NOT NULL DEFAULT 'manual',
            reference_id         VARCHAR(36),
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(journal_entry_id, line_number)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_jel_journal_entry ON journal_entry_lines (journal_entry_id)"))


def _create_fiscal_provider_tables(conn, applied: list[str]) -> None:
    """Cria tabelas de integração fiscal."""
    name = "fiscal_provider_tables.create_v1"
    if _migration_applied(conn, name):
        return

    # fiscal_provider_health_status
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fiscal_provider_health_status (
            country              VARCHAR(5) PRIMARY KEY,
            provider_name        VARCHAR(80) NOT NULL,
            mode                 VARCHAR(20) NOT NULL,
            enabled              BOOLEAN NOT NULL,
            base_url             VARCHAR(300),
            last_status          VARCHAR(20) NOT NULL,
            last_http_status     INTEGER,
            last_latency_ms      INTEGER,
            last_error           VARCHAR(1000),
            checked_at           TIMESTAMPTZ NOT NULL
        )
    """))

    # fiscal_authority_callbacks
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fiscal_authority_callbacks (
            id                   VARCHAR(60) PRIMARY KEY,
            invoice_id           VARCHAR(50) NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
            authority            VARCHAR(30) NOT NULL,
            event_type           VARCHAR(80),
            status               VARCHAR(40),
            protocol_number      VARCHAR(120),
            raw_payload          JSONB,
            received_at          TIMESTAMPTZ NOT NULL
        )
    """))

    # fiscal_reconciliation_gaps
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fiscal_reconciliation_gaps (
            id                   VARCHAR(60) PRIMARY KEY,
            dedupe_key           VARCHAR(180) NOT NULL UNIQUE,
            gap_type             VARCHAR(80) NOT NULL,
            severity             VARCHAR(20) NOT NULL,
            status               VARCHAR(20) NOT NULL,
            order_id             VARCHAR(100),
            invoice_id           VARCHAR(50),
            details_json         JSONB,
            first_detected_at    TIMESTAMPTZ NOT NULL,
            last_detected_at     TIMESTAMPTZ NOT NULL,
            resolved_at          TIMESTAMPTZ
        )
    """))

    # fiscal_accounting_approvals
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fiscal_accounting_approvals (
            id                   VARCHAR(80) PRIMARY KEY,
            owner                VARCHAR(160) NOT NULL,
            eta                  TIMESTAMPTZ,
            status               VARCHAR(80) NOT NULL,
            payload_json         JSONB NOT NULL,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    # invoice_delivery_log
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS invoice_delivery_log (
            id                   VARCHAR(50) PRIMARY KEY,
            invoice_id           VARCHAR(50) NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
            channel              VARCHAR(32) NOT NULL,
            status               VARCHAR(32) NOT NULL,
            detail               JSONB,
            created_at           TIMESTAMPTZ NOT NULL
        )
    """))

    # invoice_email_outbox
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS invoice_email_outbox (
            id                   VARCHAR(50) PRIMARY KEY,
            invoice_id           VARCHAR(50) NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
            template             VARCHAR(32) NOT NULL,
            to_email             VARCHAR(255) NOT NULL,
            subject              VARCHAR(500) NOT NULL,
            body_text            TEXT NOT NULL,
            detail_json          JSONB,
            status               VARCHAR(24) NOT NULL,
            retry_count          INTEGER NOT NULL,
            next_retry_at        TIMESTAMPTZ,
            last_error           VARCHAR(2000),
            locked_by            VARCHAR(120),
            locked_at            TIMESTAMPTZ,
            created_at           TIMESTAMPTZ NOT NULL,
            sent_at              TIMESTAMPTZ
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_product_fiscal_config(conn, applied: list[str]) -> None:
    """Cria tabela de configuração fiscal por produto."""
    name = "product_fiscal_config.create_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_fiscal_config (
            sku_id               VARCHAR(255) PRIMARY KEY,
            ncm_code             VARCHAR(10),
            cest                 VARCHAR(9),
            icms_cst             VARCHAR(3),
            pis_cst              VARCHAR(2),
            cofins_cst           VARCHAR(2),
            iva_category         VARCHAR(20),
            is_active            BOOLEAN NOT NULL DEFAULT TRUE,
            unit_of_measure      VARCHAR(6) NOT NULL DEFAULT 'UN',
            origin_type          CHAR(1) NOT NULL DEFAULT '0',
            cfop                 VARCHAR(5),
            tax_rate_pct         NUMERIC(7,4),
            is_service           BOOLEAN NOT NULL DEFAULT FALSE,
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pfc_is_active ON product_fiscal_config (is_active)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pfc_origin_cfop_active ON product_fiscal_config (origin_type, cfop, is_active)"))


def _create_fiscal_auto_classification_log(conn, applied: list[str]) -> None:
    """Cria tabela de log de classificação fiscal automática."""
    name = "fiscal_auto_classification_log.create_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fiscal_auto_classification_log (
            id                   BIGSERIAL PRIMARY KEY,
            order_id             VARCHAR(36) NOT NULL,
            invoice_id           VARCHAR(50),
            sku_id               VARCHAR(255) NOT NULL,
            ncm_applied          VARCHAR(10),
            icms_cst_applied     VARCHAR(3),
            pis_cst_applied      VARCHAR(2),
            cofins_cst_applied   VARCHAR(2),
            cfop_applied         VARCHAR(5),
            source               VARCHAR(20) NOT NULL,
            classified_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_facl_order ON fiscal_auto_classification_log (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_facl_source_classified ON fiscal_auto_classification_log (source, classified_at DESC)"))


# ============================================================================
# BLOCO 18 — Row Level Security (RLS)
# ============================================================================

def _create_rls_policies(conn, applied: list[str]) -> None:
    """Cria políticas de Row Level Security para isolamento multi-tenant."""
    name = "rls_policies.create_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    # Funções auxiliares para RLS
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION get_current_tenant_id()
        RETURNS VARCHAR AS $$
            SELECT NULLIF(current_setting('app.current_tenant_id', TRUE), '')::VARCHAR;
        $$ LANGUAGE sql STABLE
    """))

    conn.execute(text("""
        CREATE OR REPLACE FUNCTION get_current_partner_id()
        RETURNS VARCHAR AS $$
            SELECT NULLIF(current_setting('app.current_partner_id', TRUE), '')::VARCHAR;
        $$ LANGUAGE sql STABLE
    """))

    conn.execute(text("""
        CREATE OR REPLACE FUNCTION get_current_user_role()
        RETURNS VARCHAR AS $$
            SELECT NULLIF(current_setting('app.user_role', TRUE), '')::VARCHAR;
        $$ LANGUAGE sql STABLE
    """))

    # RLS para orders
    conn.execute(text("ALTER TABLE orders ENABLE ROW LEVEL SECURITY"))
    conn.execute(text("DROP POLICY IF EXISTS orders_partner_isolation ON orders"))
    conn.execute(text("""
        CREATE POLICY orders_partner_isolation ON orders
            USING (ecommerce_partner_id = get_current_partner_id()
                   OR get_current_user_role() IN ('admin', 'ops'))
    """))
    conn.execute(text("DROP POLICY IF EXISTS orders_tenant_isolation ON orders"))
    conn.execute(text("""
        CREATE POLICY orders_tenant_isolation ON orders
            USING (tenant_id = get_current_tenant_id()
                   OR get_current_user_role() = 'admin')
    """))

    # RLS para order_items
    conn.execute(text("ALTER TABLE order_items ENABLE ROW LEVEL SECURITY"))
    conn.execute(text("DROP POLICY IF EXISTS order_items_partner_isolation ON order_items"))
    conn.execute(text("""
        CREATE POLICY order_items_partner_isolation ON order_items
            USING (EXISTS (
                SELECT 1 FROM orders o
                WHERE o.id = order_items.order_id
                  AND (o.ecommerce_partner_id = get_current_partner_id()
                       OR get_current_user_role() = 'admin')
            ))
    """))

    # RLS para invoices
    conn.execute(text("ALTER TABLE invoices ENABLE ROW LEVEL SECURITY"))
    conn.execute(text("DROP POLICY IF EXISTS invoices_partner_isolation ON invoices"))
    conn.execute(text("""
        CREATE POLICY invoices_partner_isolation ON invoices
            USING (tenant_id = get_current_tenant_id()
                   OR ecommerce_partner_id = get_current_partner_id()
                   OR get_current_user_role() = 'admin')
    """))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 19 — SQLite (KIOSK Offline)
# ============================================================================

def _kiosk_sqlite_ensure_core_tables(conn, applied: list[str]) -> None:
    """Garante as tabelas mínimas para operação KIOSK offline em SQLite."""
    name = "kiosk_sqlite.core_tables_v1"
    if _migration_applied(conn, name):
        return

    # orders
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS orders (
            id              TEXT PRIMARY KEY,
            channel         TEXT NOT NULL DEFAULT 'KIOSK',
            region          TEXT NOT NULL,
            totem_id        TEXT NOT NULL,
            sku_id          TEXT NOT NULL,
            amount_cents    INTEGER NOT NULL,
            currency        TEXT NOT NULL DEFAULT 'BRL',
            status          TEXT NOT NULL DEFAULT 'CREATED',
            payment_status  TEXT NOT NULL DEFAULT 'CREATED',
            payment_method  TEXT,
            guest_name      TEXT,
            guest_email     TEXT,
            guest_phone     TEXT,
            consent_marketing INTEGER NOT NULL DEFAULT 0,
            synced_at       TIMESTAMP,
            created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # payment_transactions
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payment_transactions (
            id                      TEXT PRIMARY KEY,
            order_id                TEXT NOT NULL,
            gateway                 TEXT NOT NULL,
            gateway_transaction_id  TEXT,
            amount_cents            INTEGER NOT NULL,
            currency                TEXT NOT NULL DEFAULT 'BRL',
            payment_method          TEXT NOT NULL,
            status                  TEXT NOT NULL DEFAULT 'INITIATED',
            raw_response_json       TEXT,
            initiated_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            approved_at             TIMESTAMP,
            synced_at               TIMESTAMP,
            created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # pickups
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS pickups (
            id              TEXT PRIMARY KEY,
            order_id        TEXT NOT NULL UNIQUE,
            slot            TEXT,
            status          TEXT NOT NULL DEFAULT 'ACTIVE',
            lifecycle_stage TEXT NOT NULL DEFAULT 'READY_FOR_PICKUP',
            activated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at      TIMESTAMP,
            redeemed_at     TIMESTAMP,
            redeemed_via    TEXT,
            synced_at       TIMESTAMP,
            created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # pickup_tokens
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS pickup_tokens (
            id            TEXT PRIMARY KEY,
            pickup_id     TEXT NOT NULL,
            token_type    TEXT NOT NULL DEFAULT 'QR_CODE',
            token_hash    TEXT NOT NULL UNIQUE,
            is_active     INTEGER NOT NULL DEFAULT 1,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            max_attempts  INTEGER NOT NULL DEFAULT 5,
            issued_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at    TIMESTAMP,
            used_at       TIMESTAMP,
            synced_at     TIMESTAMP,
            created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # products_cache
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS products_cache (
            sku_id               TEXT PRIMARY KEY,
            partner_id           TEXT,
            partner_sku          TEXT,
            name                 TEXT NOT NULL,
            description          TEXT,
            category_id          TEXT NOT NULL,
            amount_cents         INTEGER NOT NULL,
            currency             TEXT NOT NULL DEFAULT 'BRL',
            width_mm             INTEGER,
            height_mm            INTEGER,
            depth_mm             INTEGER,
            weight_g             INTEGER,
            is_active            INTEGER NOT NULL DEFAULT 1,
            requires_signature   INTEGER NOT NULL DEFAULT 0,
            is_hazardous         INTEGER NOT NULL DEFAULT 0,
            temperature_zone     TEXT NOT NULL DEFAULT 'AMBIENT',
            payload_json         TEXT,
            created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            synced_at            TIMESTAMP
        )
    """))

    # sync_outbox
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sync_outbox (
            id              TEXT PRIMARY KEY,
            table_name      TEXT NOT NULL,
            record_id       TEXT NOT NULL,
            operation       TEXT NOT NULL,
            payload_json    TEXT,
            synced_at       TIMESTAMP,
            created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # reconciliation_pending
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS reconciliation_pending (
            id                      TEXT PRIMARY KEY,
            dedupe_key              TEXT NOT NULL,
            order_id                TEXT NOT NULL,
            reason                  TEXT NOT NULL,
            status                  TEXT NOT NULL DEFAULT 'PENDING',
            payload_json            TEXT,
            attempt_count           INTEGER NOT NULL DEFAULT 0,
            max_attempts            INTEGER NOT NULL DEFAULT 5,
            next_retry_at           TIMESTAMP,
            processing_started_at   TIMESTAMP,
            last_error              TEXT,
            completed_at            TIMESTAMP,
            created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # ops_action_audit
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ops_action_audit (
            id              TEXT PRIMARY KEY,
            action          TEXT NOT NULL,
            result          TEXT NOT NULL,
            correlation_id  TEXT NOT NULL,
            user_id         TEXT,
            role            TEXT,
            order_id        TEXT,
            error_message   TEXT,
            details_json    TEXT,
            created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # Índices
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_kiosk_orders_status ON orders (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_kiosk_pickups_status ON pickups (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_kiosk_sync_pending ON sync_outbox (synced_at) WHERE synced_at IS NULL"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_recon_pending_dedupe ON reconciliation_pending (dedupe_key)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_recon_pending_status_next ON reconciliation_pending (status, next_retry_at)"))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 20 — Funções de Refresh e Manutenção
# ============================================================================

def _create_refresh_functions(conn, applied: list[str]) -> None:
    """Cria funções para atualização de views materializadas."""
    name = "refresh_functions.create_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    # fn_refresh_realtime_kpis
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION fn_refresh_realtime_kpis()
        RETURNS VOID AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_realtime_kpis;
            RAISE NOTICE '✅ mv_realtime_kpis atualizado em %', now();
        END;
        $$ LANGUAGE plpgsql
    """))

    # sp_refresh_financial_materialized_views
    conn.execute(text("""
        CREATE OR REPLACE FUNCTION sp_refresh_financial_materialized_views()
        RETURNS TEXT AS $$
        DECLARE
            v_start_time TIMESTAMPTZ;
            v_end_time TIMESTAMPTZ;
            v_duration TEXT;
        BEGIN
            v_start_time := NOW();
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_locker_monthly_profitability;
            RAISE NOTICE '✅ mv_locker_monthly_profitability atualizada';
            REFRESH MATERIALIZED VIEW CONCURRENTLY mv_realtime_kpis;
            RAISE NOTICE '✅ mv_realtime_kpis atualizada';
            IF EXISTS (SELECT 1 FROM pg_matviews WHERE matviewname = 'mv_locker_monthly_pnl') THEN
                REFRESH MATERIALIZED VIEW CONCURRENTLY mv_locker_monthly_pnl;
                RAISE NOTICE '✅ mv_locker_monthly_pnl atualizada';
            END IF;
            v_end_time := NOW();
            v_duration := EXTRACT(EPOCH FROM (v_end_time - v_start_time))::TEXT || ' segundos';
            RAISE NOTICE '✅ Todas as materialized views financeiras atualizadas em %', v_duration;
            RETURN 'Atualização concluída em ' || v_duration;
        END;
        $$ LANGUAGE plpgsql
    """))

    # sp_sync_locker_monthly_costs
    conn.execute(text("""
        CREATE OR REPLACE PROCEDURE sp_sync_locker_monthly_costs(IN p_target_month DATE)
        LANGUAGE plpgsql AS $$
        BEGIN
            WITH opex_agg AS (
                SELECT locker_id,
                       COALESCE(SUM(CASE WHEN category IN ('RENT', 'LOGISTICS', 'OTHER') THEN amount_cents ELSE 0 END), 0) AS operational_cents,
                       COALESCE(SUM(CASE WHEN category IN ('MAINTENANCE', 'REPAIR', 'SUPPORT') THEN amount_cents ELSE 0 END), 0) AS maint_cents,
                       COALESCE(SUM(CASE WHEN category IN ('ENERGY', 'CONNECTIVITY') THEN amount_cents ELSE 0 END), 0) AS utilities_cents
                FROM ellanlab_opex_entries
                WHERE expense_month = p_target_month AND locker_id IS NOT NULL
                GROUP BY locker_id
            ),
            depr_agg AS (
                SELECT ha.locker_id,
                       COALESCE(SUM(ds.depreciation_amount_cents), 0) AS depr_cents
                FROM ellanlab_depreciation_schedule ds
                JOIN ellanlab_hardware_assets ha ON ds.asset_id = ha.id
                WHERE ds.depreciation_month = p_target_month AND ha.locker_id IS NOT NULL
                GROUP BY ha.locker_id
            )
            UPDATE cost_centers cc
            SET operational_cost_monthly_cents = COALESCE(op.operational_cents, 0),
                maintenance_cost_annual_cents = COALESCE(op.maint_cents, 0) * 12,
                utilities_cost_monthly_cents = COALESCE(op.utilities_cents, 0),
                depreciation_cost_annual_cents = COALESCE(d.depr_cents, 0) * 12,
                updated_at = now()
            FROM opex_agg op
            LEFT JOIN depr_agg d ON cc.locker_id = d.locker_id
            WHERE cc.locker_id = op.locker_id;
            
            RAISE NOTICE 'Custos atualizados para o mês: %', p_target_month;
        END;
        $$;
    """))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 21 — Tabelas de Gateway/Device (PCI Compliance)
# ============================================================================

def _create_gateway_tables(conn, applied: list[str]) -> None:
    """Cria tabelas para gateway de pagamento e device registry."""
    name = "gateway_tables.create_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    # gateway_events
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS gateway_events (
            id               TEXT PRIMARY KEY,
            gateway_id       TEXT NOT NULL,
            region           TEXT NOT NULL,
            locker_id        TEXT NOT NULL,
            porta            INTEGER,
            event_type       TEXT NOT NULL,
            created_at       BIGINT NOT NULL,
            request_id       TEXT,
            order_id         TEXT,
            payload_json     JSONB NOT NULL
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_gateway_events_region_locker_porta_created ON gateway_events (region, locker_id, porta, created_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_gateway_events_order_created ON gateway_events (order_id, created_at)"))

    # risk_events
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS risk_events (
            id               TEXT PRIMARY KEY,
            request_id       TEXT NOT NULL,
            event_type       TEXT NOT NULL,
            decision         TEXT NOT NULL,
            score            INTEGER NOT NULL,
            policy_id        TEXT NOT NULL,
            region           TEXT NOT NULL,
            locker_id        TEXT NOT NULL,
            porta            INTEGER NOT NULL,
            created_at       BIGINT NOT NULL,
            reasons_json     JSONB NOT NULL DEFAULT '[]',
            signals_json     JSONB NOT NULL DEFAULT '{}',
            audit_event_id   TEXT NOT NULL
        )
    """))

    # payment_gateway_device_registry
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payment_gateway_device_registry (
            device_hash          TEXT PRIMARY KEY,
            version              TEXT NOT NULL,
            first_seen_at_epoch  BIGINT NOT NULL,
            last_seen_at_epoch   BIGINT NOT NULL,
            seen_count           INTEGER NOT NULL DEFAULT 1,
            region_code          VARCHAR(20),
            locker_id            VARCHAR(120),
            flags_json           JSONB NOT NULL DEFAULT '{}',
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    # payment_gateway_idempotency_keys
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payment_gateway_idempotency_keys (
            id                   TEXT PRIMARY KEY,
            endpoint             TEXT NOT NULL,
            idem_key             TEXT NOT NULL,
            payload_hash         TEXT NOT NULL,
            response_blob        JSONB NOT NULL DEFAULT '{}',
            status               TEXT NOT NULL,
            region_code          VARCHAR(20),
            sales_channel        VARCHAR(50),
            request_fingerprint  TEXT,
            created_at_epoch     BIGINT NOT NULL,
            expires_at_epoch     BIGINT NOT NULL,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(endpoint, idem_key)
        )
    """))

    # payment_gateway_risk_events
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payment_gateway_risk_events (
            id               TEXT PRIMARY KEY,
            request_id       TEXT NOT NULL,
            event_type       TEXT NOT NULL,
            decision         TEXT NOT NULL,
            score            INTEGER NOT NULL,
            policy_id        TEXT NOT NULL,
            region_code      VARCHAR(20) NOT NULL,
            locker_id        VARCHAR(120) NOT NULL,
            slot             INTEGER NOT NULL,
            audit_event_id   TEXT NOT NULL,
            reasons_json     JSONB NOT NULL DEFAULT '[]',
            signals_json     JSONB NOT NULL DEFAULT '{}',
            metadata_json    JSONB NOT NULL DEFAULT '{}',
            created_at_epoch BIGINT NOT NULL,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 22 — Templates
# ============================================================================

def _create_templates(conn, applied: list[str]) -> None:
    """Cria tabela de templates."""
    name = "templates.create_v1"
    if _migration_applied(conn, name):
        return

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS templates (
            id           VARCHAR(36) PRIMARY KEY,
            name         VARCHAR(128) NOT NULL UNIQUE,
            body         TEXT NOT NULL,
            created_at   TIMESTAMPTZ NOT NULL
        )
    """))

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# BLOCO 23 — Migration Helper Functions
# ============================================================================

def _migrate_partner_lifecycle_columns_v1(conn, applied: list[str]) -> None:
    """Migração para adicionar colunas de ciclo de vida a parceiros."""
    name = "partners.lifecycle_columns_v1"
    if _migration_applied(conn, name):
        return

    inspector = inspect(conn)
    if _has_table(inspector, "ecommerce_partners"):
        _ensure_column(conn, "ecommerce_partners", "status", "VARCHAR(30) NOT NULL DEFAULT 'DRAFT'")
        _ensure_column(conn, "ecommerce_partners", "legal_name", "VARCHAR(140)")
        _ensure_column(conn, "ecommerce_partners", "tax_id", "VARCHAR(32)")
        _ensure_column(conn, "ecommerce_partners", "tier", "VARCHAR(20) DEFAULT 'STANDARD'")

    if _has_table(inspector, "locker_operators"):
        _ensure_column(conn, "locker_operators", "status", "VARCHAR(30) NOT NULL DEFAULT 'DRAFT'")
        _ensure_column(conn, "locker_operators", "legal_name", "VARCHAR(140)")
        _ensure_column(conn, "locker_operators", "tier", "VARCHAR(20) DEFAULT 'STANDARD'")

    _mark_migration(conn, name)
    applied.append(name)


def _migrate_users_fiscal_pii_encryption_schema(conn, applied: list[str]) -> None:
    """Migração para colunas de PII fiscal criptografada."""
    name = "users.fiscal_pii_encryption_schema_v2026_01"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    inspector = inspect(conn)
    if not _has_table(inspector, "users"):
        _mark_migration(conn, name)
        applied.append(name)
        return

    try:
        conn.execute(text("DROP INDEX IF EXISTS ix_users_tax_document_value"))
    except Exception as exc:
        logger.warning("users_fiscal_pii_drop_index_failed err=%s", exc)

    widen_columns = [
        "tax_document_value", "fiscal_email", "fiscal_phone",
        "fiscal_address_line1", "fiscal_address_line2",
        "fiscal_address_city", "fiscal_address_state", "fiscal_address_postal_code"
    ]
    for col in widen_columns:
        if _has_column(inspector, "users", col):
            try:
                conn.execute(text(f"ALTER TABLE users ALTER COLUMN {col} TYPE VARCHAR(1024)"))
            except Exception as exc:
                logger.warning("users_fiscal_pii_widen_column_failed col=%s err=%s", col, exc)

    _mark_migration(conn, name)
    applied.append(name)


def _migrate_runtime_sync_queue_next_retry_at_v1(conn, applied: list[str]) -> None:
    """Migração para adicionar next_retry_at na runtime_sync_queue."""
    name = "runtime_sync_queue.next_retry_at_v1"
    if _migration_applied(conn, name):
        return

    if _dialect(conn) != "postgresql":
        _mark_migration(conn, name)
        applied.append(name)
        return

    inspector = inspect(conn)
    if not _has_table(inspector, "runtime_sync_queue"):
        _mark_migration(conn, name)
        applied.append(name)
        return

    if not _has_column(inspector, "runtime_sync_queue", "next_retry_at"):
        conn.execute(text("ALTER TABLE runtime_sync_queue ADD COLUMN next_retry_at TIMESTAMPTZ"))

    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_runtime_sync_queue_next_retry ON runtime_sync_queue (next_retry_at) WHERE status = 'PENDING'"))

    _mark_migration(conn, name)
    applied.append(name)


def _backfill_locker_slot_configs_mm_from_legacy_cm(conn, applied: list[str]) -> None:
    """Backfill de dimensões de cm para mm."""
    name = "locker_slot_configs.backfill_mm_from_cm_v1"
    if _migration_applied(conn, name):
        return

    inspector = inspect(conn)
    if not _has_table(inspector, "locker_slot_configs"):
        _mark_migration(conn, name)
        applied.append(name)
        return

    cols = {c["name"] for c in inspector.get_columns("locker_slot_configs")}

    if "width_cm" in cols and "width_mm" in cols:
        conn.execute(text("""
            UPDATE locker_slot_configs
            SET width_mm = COALESCE(width_mm, (width_cm * 10)::integer)
            WHERE width_cm IS NOT NULL AND width_mm IS NULL
        """))

    if "height_cm" in cols and "height_mm" in cols:
        conn.execute(text("""
            UPDATE locker_slot_configs
            SET height_mm = COALESCE(height_mm, (height_cm * 10)::integer)
            WHERE height_cm IS NOT NULL AND height_mm IS NULL
        """))

    if "depth_cm" in cols and "depth_mm" in cols:
        conn.execute(text("""
            UPDATE locker_slot_configs
            SET depth_mm = COALESCE(depth_mm, (depth_cm * 10)::integer)
            WHERE depth_cm IS NOT NULL AND depth_mm IS NULL
        """))

    if "max_weight_kg" in cols and "max_weight_g" in cols:
        conn.execute(text("""
            UPDATE locker_slot_configs
            SET max_weight_g = COALESCE(max_weight_g, (max_weight_kg * 1000)::integer)
            WHERE max_weight_kg IS NOT NULL AND max_weight_g IS NULL
        """))

    _mark_migration(conn, name)
    applied.append(name)


def _auto_heal_legacy_schema(conn, applied: list[str]) -> None:
    """Auto-heal para schema legado."""
    name = "schema.auto_heal_legacy_v1"
    if _migration_applied(conn, name):
        return

    _ensure_column(conn, "users", "locale", "VARCHAR(10) NOT NULL DEFAULT 'pt-BR'")
    _ensure_column(conn, "users", "totp_secret_ref", "VARCHAR(255)")
    _ensure_column(conn, "users", "totp_enabled", "BOOLEAN NOT NULL DEFAULT FALSE")
    _ensure_column(conn, "users", "anonymized_at", "TIMESTAMPTZ")
    _ensure_column(conn, "users", "tax_country", "VARCHAR(2)")
    _ensure_column(conn, "users", "tax_document_type", "VARCHAR(16)")

    _ensure_index(conn, "users", "ux_users_email", "CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON users (email) WHERE anonymized_at IS NULL")

    _ensure_column(conn, "locker_operators", "contract_start_at", "TIMESTAMPTZ")
    _ensure_column(conn, "locker_operators", "contract_end_at", "TIMESTAMPTZ")
    _ensure_column(conn, "locker_operators", "sla_pickup_hours", "INTEGER NOT NULL DEFAULT 72")
    _ensure_column(conn, "locker_operators", "player_code", "VARCHAR(40)")
    conn.execute(
        text("CREATE INDEX IF NOT EXISTS ix_locker_operators_player_code ON locker_operators (player_code)")
    )

    _ensure_column(conn, "lockers", "tenant_id", "VARCHAR(100)")
    _ensure_column(conn, "lockers", "slots_available", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column(conn, "lockers", "has_kiosk", "BOOLEAN NOT NULL DEFAULT FALSE")
    _ensure_column(conn, "lockers", "pickup_code_length", "INTEGER NOT NULL DEFAULT 6")
    _ensure_column(conn, "lockers", "has_ble", "BOOLEAN NOT NULL DEFAULT FALSE")

    _ensure_column(conn, "orders", "ecommerce_partner_id", "VARCHAR(36)")
    _ensure_column(conn, "orders", "partner_order_ref", "VARCHAR(128)")
    _ensure_column(conn, "orders", "cancelled_at", "TIMESTAMPTZ")
    _ensure_column(conn, "orders", "refunded_at", "TIMESTAMPTZ")
    _ensure_column(conn, "orders", "order_metadata", _jsonb_or_text(conn))

    _ensure_column(conn, "pickups", "pickup_phase", "VARCHAR(32)")
    _ensure_column(conn, "pickups", "evidence_score", "INTEGER DEFAULT 0")
    _ensure_column(conn, "pickups", "dispute_state", "VARCHAR(20) DEFAULT 'NONE'")
    _ensure_column(conn, "pickups", "fraud_flag", "BOOLEAN NOT NULL DEFAULT FALSE")

    _ensure_index(conn, "pickups", "ix_pickups_pickup_phase", "CREATE INDEX IF NOT EXISTS ix_pickups_pickup_phase ON pickups (pickup_phase)")
    _ensure_index(conn, "pickups", "ix_pickups_ble_redeemed", "CREATE INDEX IF NOT EXISTS ix_pickups_ble_redeemed ON pickups (locker_id, redeemed_at DESC) WHERE redeemed_via = 'BLE'")
    _ensure_index(conn, "lockers", "idx_lockers_has_ble", "CREATE INDEX IF NOT EXISTS idx_lockers_has_ble ON lockers (has_ble) WHERE has_ble = true")
    _ensure_index(conn, "lockers", "idx_lockers_active_ble", "CREATE INDEX IF NOT EXISTS idx_lockers_active_ble ON lockers (active, has_ble) WHERE active = true")

    _mark_migration(conn, name)
    applied.append(name)


# ============================================================================
# ENTRY POINT PRINCIPAL
# ============================================================================

# Sequência canônica de criação para PostgreSQL.
_POSTGRES_MIGRATION_STEPS = [
    # Extensões e schemas
    _create_extensions,
    _create_schemas,

    # Enums
    _create_enums,

    # Identidade e usuários
    _create_users,
    _create_auth_sessions,
    _create_core_user,
    _create_core_session,
    _create_login_history,
    _create_login_otps,
    _create_user_roles,
    _create_privacy_consents,
    _create_data_deletion_requests,

    # Lockers e operadores
    _create_locker_operators,
    _create_lockers,
    _create_capability_locker_location,
    _create_capability_country,
    _create_capability_province,
    _create_locker_slots,
    _create_locker_slot_configs,
    _backfill_locker_slot_configs_mm_from_legacy_cm,
    _create_runtime_lockers,
    _create_runtime_locker_slots,
    _create_runtime_locker_features,
    _create_runtime_sync_queue,
    _migrate_runtime_sync_queue_next_retry_at_v1,
    _create_locker_telemetry,
    _create_locker_telemetry_partitioned,
    _create_door_state,
    _create_ble_handshake_logs,
    _create_tenant_fiscal_config,
    _create_custom_domains,
    _create_cost_centers,
    _create_cost_center_monthly,
    _create_locker_capex,
    _create_locker_capex_details,
    _create_locker_opex,

    # Produtos
    _create_product_categories,
    _create_products,
    _create_product_status_history,
    _create_product_media,
    _create_product_barcodes,
    _create_product_inventory,
    _create_inventory_movements,
    _create_inventory_reservations,
    _create_product_bundles,
    _create_product_bundle_items,
    _create_promotions,
    _create_promotion_product_exclusions,
    _create_promotion_campaigns,
    _create_promotion_scopes,
    _create_promotion_product_inclusions,
    _create_promotion_redemptions,
    _create_promotion_audit_events,
    _promotions_add_campaign_id,
    _create_products_cache,
    _create_product_locker_configs,
    _create_dynamic_pricing_rules,
    _create_price_history,
    _create_product_recommendations,
    _create_catalog_professional_tables,
    _create_global_players_registry,
    _create_global_player_aliases_relations,

    # Parceiros
    _create_ecommerce_partners,
    _create_logistics_partners,
    _migrate_partner_lifecycle_columns_v1,
    _create_partner_status_history,
    _create_partner_contacts,
    _create_partner_sla_agreements,
    _create_partner_api_keys,
    _create_partner_webhook_endpoints,
    _create_partner_webhook_deliveries,
    _create_partner_integration_health,
    _create_partner_settlement_batches,
    _create_partner_settlement_items,
    _create_partner_service_areas,
    _create_partner_performance_metrics,
    _create_partner_order_events_outbox,
    _create_partner_billing_plans,
    _create_partner_billing_cycles,
    _create_partner_billing_line_items,
    _create_partner_b2b_invoices,
    _create_partner_credit_notes,
    _create_partner_payment_holds,

    # Logística
    _create_inbound_deliveries,
    _create_logistics_tracking_events,
    _create_logistics_delivery_attempts,
    _create_logistics_shipment_labels,
    _create_logistics_carrier_auth_config,
    _create_logistics_carrier_status_map,
    _create_logistics_returns,
    _create_logistics_return_events,
    _create_return_reasons_catalog,
    _create_return_requests,
    _create_return_legs,
    _create_return_tracking_events,
    _create_sla_breach_events,
    _create_logistics_manifests,
    _create_logistics_manifest_items,
    _create_logistics_capacity_allocations,
    _create_logistics_carrier_rates,

    # Fulfillment
    _create_fulfillment_centers,
    _create_fulfillment_inventory,
    _create_fulfillment_orders,
    _create_omnichannel_orders,
    _create_partner_stores,
    _create_store_inventory,

    # Pedidos e pagamentos
    _create_orders,
    _create_orders_partitioned,
    _create_order_items,
    _create_payment_transactions,
    _create_payment_instructions,
    _create_payment_splits,
    _create_saved_payment_methods,
    _create_credits,
    _create_financial_ledger,
    _create_user_wallets,
    _create_wallet_transactions,

    # Alocações e pickups
    _create_allocations,
    _create_pickups,
    _create_pickup_tokens,
    _create_pickup_events,
    _create_pickup_attempts,
    _create_slot_occupancy_history,

    # Documentos fiscais
    _create_fiscal_documents,
    _create_invoices,

    # Notificações e eventos
    _create_notification_logs,
    _create_notifications,
    _create_domain_event_outbox,
    _create_domain_events,
    _create_billing_processed_events,
    _create_lifecycle_deadlines,
    _create_analytics_facts,
    _create_reconciliation_pending,
    _create_ops_action_audit,
    _create_ops_outbox_replay_priority_runs,
    _create_order_fulfillment_tracking,
    _create_webhook_endpoints,
    _create_webhook_deliveries,

    # Assinaturas e marketplace
    _create_subscription_plans,
    _create_customer_subscriptions,
    _create_subscription_benefits_usage,
    _create_marketplace_sellers,
    _create_seller_products,
    _create_marketplace_commissions,
    _create_seller_reviews,

    # Rental
    _create_rental_plans,
    _create_rental_contracts,

    # Métricas e ML
    _create_demand_forecast,
    _create_ml_features_daily,
    _create_ml_predictions_log,
    _create_ml_model_metadata,
    _create_ml_prediction_feedback,
    _create_locker_slot_hourly_occupancy,
    _create_locker_utilization_snapshots,

    # BI e Analytics (Metabase)
    _create_metabase_tables,
    _create_metabase_support_tables,
    _create_metabase_audit_tables,
    _create_metabase_permission_tables,
    _create_metabase_scheduler_tables,
    _create_metabase_embedding_tables,
    _create_metabase_version_tables,

    # Geodata e Analytics schema
    _create_geodata_tables,
    _create_analytics_schema_tables,

    # EllanLab financeiro
    _create_ellanlab_tables,
    _create_financial_kpi_daily,
    _create_chart_of_accounts,
    _create_journal_entries,
    _create_fiscal_provider_tables,
    _create_product_fiscal_config,
    _create_fiscal_auto_classification_log,

    # Gateway/Device (PCI)
    _create_gateway_tables,

    # Templates
    _create_templates,

    # Funções, triggers e views
    _create_functions,
    _create_triggers,
    _create_materialized_views,
    _create_analytical_views,
    _create_refresh_functions,

    # RLS Policies
    _create_rls_policies,

    # Auto-heal (deve vir por último)
    _auto_heal_legacy_schema,
    _migrate_users_fiscal_pii_encryption_schema,
]


def run_migrations(conn) -> list[str]:
    """Executa todas as migrations no ambiente correto."""
    applied: list[str] = []
    dialect = conn.dialect.name

    if dialect == "postgresql":
        _ensure_schema_migrations(conn)

        for step in _POSTGRES_MIGRATION_STEPS:
            try:
                step(conn, applied)
                conn.commit()
            except Exception as exc:
                logger.error("Migration falhou em %s: %s", step.__name__, exc)
                conn.rollback()
                raise

    elif dialect == "sqlite":
        _kiosk_sqlite_ensure_core_tables(conn, applied)
    else:
        raise RuntimeError(f"Dialect não suportado: {dialect}")

    return applied


def migrate_order_pickup_schema() -> dict:
    """
    Executa as migrations completas usando o engine configurado.
    Chamada durante o startup do serviço.
    """
    try:
        with engine.begin() as conn:
            applied = run_migrations(conn)

        logger.info(
            "Migrations concluídas. %d aplicadas: %s",
            len(applied),
            applied or "nenhuma (schema já atualizado)",
        )
        return {"ok": True, "applied": applied}

    except Exception as exc:
        logger.exception("Erro fatal durante migrations: %s", exc)
        return {"ok": False, "error_type": exc.__class__.__name__, "applied": []}


def _run_startup_migrations_if_enabled() -> dict:
    """Wrapper de startup — compatível com `app.core.db`."""
    return migrate_order_pickup_schema()


# Ponto de entrada para execução direta (debug/testing)
if __name__ == "__main__":
    import json
    import sys
    import logging

    # Configurar logging básico para execução standalone
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    result = migrate_order_pickup_schema()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Exit com código de erro se falhou
    sys.exit(0 if result.get("ok") else 1)