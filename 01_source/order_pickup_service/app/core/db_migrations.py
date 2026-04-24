# 01_source/order_pickup_service/app/core/db_migrations.py
#
# Estratégia de banco de dados:
#   PRIMARY  → PostgreSQL (produção, cloud, back-office)
#   FALLBACK → SQLite    (KIOSK local — resiliência offline, replicação assíncrona separada)
#
# Convenções:
#   - IDs: VARCHAR(36) compatível com UUID v4
#   - Timestamps: TIMESTAMPTZ (PostgreSQL) / TIMESTAMP WITH TIME ZONE (SQLite)
#   - Monetário: INTEGER (centavos) + VARCHAR(8) currency — nunca FLOAT
#   - JSON: JSONB (PostgreSQL) / TEXT (SQLite)
#   - Booleanos: BOOLEAN
#   - Migrações rastreadas em `schema_migrations`
#
# Ordem de criação de tabelas (respeita FK):
#   1. schema_migrations
#   2. users
#   3. auth_sessions
#   4. locker_operators
#   5. lockers
#   6. locker_slot_configs
#   7. locker_slots
#   8. locker_telemetry
#   9. product_categories
#  10. product_locker_configs
#  11. rental_plans
#  12. rental_contracts
#  13. logistics_partners
#  14. ecommerce_partners
#  15. webhook_endpoints
#  16. webhook_deliveries
#  17. orders
#  18. payment_transactions
#  19. allocations
#  20. pickups
#  21. pickup_tokens
#  22. inbound_deliveries
#  23. fiscal_documents
#  24. notification_logs
#  25. domain_event_outbox
#  26. privacy_consents
#  27. data_deletion_requests

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import inspect, text

from app.core.db import engine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers de inspeção (dialect-agnóstico)
# ---------------------------------------------------------------------------

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


def _jsonb_or_text(conn) -> str:
    """Retorna JSONB em PostgreSQL, TEXT em SQLite."""
    return "JSONB" if _dialect(conn) == "postgresql" else "TEXT"


def _ts(conn) -> str:
    """Tipo de timestamp com fuso horário."""
    return "TIMESTAMPTZ" if _dialect(conn) == "postgresql" else "TIMESTAMP WITH TIME ZONE"


# ---------------------------------------------------------------------------
# Auto-heal helpers (produção)
# ---------------------------------------------------------------------------

def _quote_ident(name: str) -> str:
    """
    Quote mínimo e seguro para identificadores SQL simples.
    """
    return '"' + name.replace('"', '""') + '"'


def _ensure_column(conn, table_name: str, column_name: str, ddl: str) -> None:
    """
    Garante que uma coluna exista. Idempotente e seguro para startup.
    ddl exemplo: "TIMESTAMPTZ", "VARCHAR(255)", "BOOLEAN NOT NULL DEFAULT FALSE"
    """
    inspector = inspect(conn)
    if not _has_table(inspector, table_name):
        return
    if _has_column(inspector, table_name, column_name):
        return

    logger.warning(
        "[AUTO-HEAL] adicionando coluna %s.%s %s",
        table_name,
        column_name,
        ddl,
    )
    conn.execute(
        text(
            f"ALTER TABLE {_quote_ident(table_name)} "
            f"ADD COLUMN {_quote_ident(column_name)} {ddl}"
        )
    )


def _ensure_index(conn, table_name: str, index_name: str, create_sql: str) -> None:
    """
    Garante que um índice exista.
    create_sql deve ser um CREATE INDEX IF NOT EXISTS ... completo.
    """
    inspector = inspect(conn)
    if not _has_table(inspector, table_name):
        return
    if _has_index(inspector, table_name, index_name):
        return

    logger.warning("[AUTO-HEAL] criando índice %s em %s", index_name, table_name)
    conn.execute(text(create_sql))


def _ensure_columns(conn, table_name: str, columns: dict[str, str]) -> None:
    """
    Garante várias colunas numa mesma tabela.
    columns = {"coluna": "DDL"}
    """
    for column_name, ddl in columns.items():
        _ensure_column(conn, table_name, column_name, ddl)


# ---------------------------------------------------------------------------
# Versionamento de migrações
# ---------------------------------------------------------------------------

MIGRATIONS: dict[str, str] = {}
"""Registro de todas as migrations em ordem. Chave = nome único, Valor = SQL ou sentinela."""


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
    """Cria a tabela de controle de versão de migrations (idempotente)."""
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            name       VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))


# ---------------------------------------------------------------------------
# Auto-heal de compatibilidade de schema
# ---------------------------------------------------------------------------

def _ensure_users_columns(conn) -> None:
    _ensure_columns(conn, "users", {
        "locale": "VARCHAR(10) NOT NULL DEFAULT 'pt-BR'",
        "totp_secret_ref": "VARCHAR(255)",
        "totp_enabled": "BOOLEAN NOT NULL DEFAULT FALSE",
        "anonymized_at": "TIMESTAMPTZ",
    })
    _ensure_index(
        conn,
        "users",
        "ux_users_email",
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email "
        "ON users (email) WHERE anonymized_at IS NULL",
    )


def _ensure_locker_operators_columns(conn) -> None:
    _ensure_columns(conn, "locker_operators", {
        "contract_start_at": "TIMESTAMPTZ",
        "contract_end_at": "TIMESTAMPTZ",
        "contract_ref": "VARCHAR(255)",
        "sla_pickup_hours": "INTEGER NOT NULL DEFAULT 72",
        "sla_return_hours": "INTEGER NOT NULL DEFAULT 24",
    })


def _ensure_lockers_columns(conn) -> None:
    _ensure_columns(conn, "lockers", {
        "site_id": "VARCHAR(100)",
        "tenant_id": "VARCHAR(100)",
        "geolocation_wkt": "VARCHAR(100)",
        "slots_available": "INTEGER NOT NULL DEFAULT 0",
        "has_kiosk": "BOOLEAN NOT NULL DEFAULT FALSE",
        "has_printer": "BOOLEAN NOT NULL DEFAULT FALSE",
        "has_card_reader": "BOOLEAN NOT NULL DEFAULT FALSE",
        "has_nfc": "BOOLEAN NOT NULL DEFAULT FALSE",
        "finding_instructions": "TEXT",
        "pickup_code_length": "INTEGER NOT NULL DEFAULT 6",
        "pickup_reuse_policy": "VARCHAR(32) NOT NULL DEFAULT 'NO_REUSE'",
        "pickup_reuse_window_sec": "INTEGER",
        "pickup_max_reopens": "INTEGER NOT NULL DEFAULT 0",
    })


def _ensure_locker_slot_configs_columns(conn) -> None:
    _ensure_columns(conn, "locker_slot_configs", {
        "width_mm": "INTEGER",
        "height_mm": "INTEGER",
        "depth_mm": "INTEGER",
        "max_weight_g": "INTEGER",
    })


def _ensure_orders_columns(conn) -> None:
    json_type = _jsonb_or_text(conn)
    _ensure_columns(conn, "orders", {
        "site_id": "VARCHAR(100)",
        "tenant_id": "VARCHAR(100)",
        "ecommerce_partner_id": "VARCHAR(36)",
        "partner_order_ref": "VARCHAR(128)",
        "sku_description": "VARCHAR(255)",
        "slot_size": "VARCHAR(8)",
        "card_brand": "VARCHAR(20)",
        "card_last4": "VARCHAR(4)",
        "installments": "INTEGER NOT NULL DEFAULT 1",
        "guest_name": "VARCHAR(255)",
        "consent_analytics": "BOOLEAN NOT NULL DEFAULT FALSE",
        "cancelled_at": "TIMESTAMPTZ",
        "cancel_reason": "VARCHAR(255)",
        "refunded_at": "TIMESTAMPTZ",
        "refund_reason": "VARCHAR(255)",
        "payment_interface": "VARCHAR(32)",
        "wallet_provider": "VARCHAR(64)",
        "device_id": "VARCHAR(128)",
        "ip_address": "VARCHAR(64)",
        "user_agent": "VARCHAR(500)",
        "idempotency_key": "VARCHAR(255)",
        "order_metadata": json_type,
    })
    _ensure_index(
        conn,
        "orders",
        "ix_orders_pickup_deadline",
        "CREATE INDEX IF NOT EXISTS ix_orders_pickup_deadline "
        "ON orders (pickup_deadline_at) "
        "WHERE status NOT IN ('PICKED_UP','CANCELLED','REFUNDED','EXPIRED')",
    )
    # PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened


def _ensure_order_items_columns(conn) -> None:
    inspector = inspect(conn)
    if not _has_table(inspector, "order_items"):
        return
    _ensure_columns(conn, "order_items", {
        "ncm": "VARCHAR(10)",
    })


def _ensure_allocations_columns(conn) -> None:
    _ensure_columns(conn, "allocations", {
        "slot_size": "VARCHAR(8)",
        "allocated_at": "TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "released_at": "TIMESTAMPTZ",
        "release_reason": "VARCHAR(255)",
    })


def _ensure_pickup_tokens_columns(conn) -> None:
    _ensure_columns(conn, "pickup_tokens", {
        "is_active": "BOOLEAN NOT NULL DEFAULT TRUE",
    })
    _ensure_index(
        conn,
        "pickup_tokens",
        "ix_pickup_tokens_active",
        "CREATE INDEX IF NOT EXISTS ix_pickup_tokens_active "
        "ON pickup_tokens (pickup_id, is_active) WHERE is_active = TRUE",
    )


def _ensure_notification_logs_columns(conn) -> None:
    _ensure_columns(conn, "notification_logs", {
        "pickup_id": "VARCHAR(36)",
        "delivery_id": "VARCHAR(36)",
        "rental_id": "VARCHAR(36)",
        "provider_status": "VARCHAR(100)",
        "error_detail": "TEXT",
        "locale": "VARCHAR(10)",
    })
    _ensure_index(
        conn,
        "notification_logs",
        "ix_notif_pickup",
        "CREATE INDEX IF NOT EXISTS ix_notif_pickup ON notification_logs (pickup_id)",
    )


def _ensure_fiscal_documents_columns(conn) -> None:
    json_type = _jsonb_or_text(conn)
    xml_type = "TEXT"
    _ensure_columns(conn, "fiscal_documents", {
        "tenant_id": "VARCHAR(100)",
        "tax_amount_cents": "INTEGER",
        "tax_breakdown_json": json_type,
        "sent_at": "TIMESTAMPTZ",
        "printed_at": "TIMESTAMPTZ",
        "xml_signed": xml_type,
        "chave_acesso": "VARCHAR(64)",
        "cancelled_at": "TIMESTAMPTZ",
        "cancel_reason": "VARCHAR(255)",
    })


def _ensure_payment_method_catalog_columns(conn) -> None:
    _ensure_columns(conn, "payment_method_catalog", {
        "is_instant": "BOOLEAN NOT NULL DEFAULT FALSE",
    })


def _ensure_payment_interface_catalog_columns(conn) -> None:
    _ensure_columns(conn, "payment_interface_catalog", {
        "requires_hw": "BOOLEAN NOT NULL DEFAULT FALSE",
    })


def _ensure_capability_profile_columns(conn) -> None:
    _ensure_columns(conn, "capability_profile", {
        "valid_from": "TIMESTAMPTZ",
        "valid_until": "TIMESTAMPTZ",
    })
    _ensure_index(
        conn,
        "capability_profile",
        "ix_cap_profile_active",
        "CREATE INDEX IF NOT EXISTS ix_cap_profile_active "
        "ON capability_profile (is_active, valid_from, valid_until)",
    )


def _ensure_capability_profile_target_columns(conn) -> None:
    _ensure_columns(conn, "capability_profile_target", {
        "locker_id": "VARCHAR(64)",
    })
    _ensure_index(
        conn,
        "capability_profile_target",
        "ix_cpt_locker_id",
        "CREATE INDEX IF NOT EXISTS ix_cpt_locker_id "
        "ON capability_profile_target (locker_id)",
    )


def _backfill_locker_slot_configs_mm_from_legacy_cm(conn, applied: list[str]) -> None:
    """
    Bancos legados: colunas width_cm / max_weight_kg etc. preenchiam dimensões;
    o modelo canônico usa width_mm / max_weight_g. Copia valores faltantes uma vez.
    """
    name = "locker_slot_configs.backfill_mm_from_cm_v1"
    if _migration_applied(conn, name):
        return
    inspector = inspect(conn)
    if not _has_table(inspector, "locker_slot_configs"):
        _mark_migration(conn, name)
        applied.append(name)
        return
    cols = {c["name"] for c in inspector.get_columns("locker_slot_configs")}
    has_any_legacy = bool(
        {"width_cm", "height_cm", "depth_cm", "max_weight_kg"} & cols
    )
    if not has_any_legacy:
        _mark_migration(conn, name)
        applied.append(name)
        return

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
    logger.info("locker_slot_configs_legacy_cm_backfilled", extra={"migration": name})


def _auto_heal_legacy_schema(conn, applied: list[str]) -> None:
    """
    Corrige drift de schema antes do assert rígido.
    Idempotente e seguro para execução em todo startup.
    """
    name = "schema.auto_heal_legacy_v1"
    if _migration_applied(conn, name):
        # mesmo se já marcado, continua rodando porque pode haver drift novo
        pass

    _ensure_users_columns(conn)
    _ensure_locker_operators_columns(conn)
    _ensure_lockers_columns(conn)
    _ensure_locker_slot_configs_columns(conn)
    _backfill_locker_slot_configs_mm_from_legacy_cm(conn, applied)
    _ensure_orders_columns(conn)
    _ensure_order_items_columns(conn)
    _ensure_allocations_columns(conn)
    _ensure_pickup_tokens_columns(conn)
    _ensure_notification_logs_columns(conn)
    _ensure_fiscal_documents_columns(conn)
    _ensure_payment_method_catalog_columns(conn)
    _ensure_payment_interface_catalog_columns(conn)
    _ensure_capability_profile_columns(conn)
    _ensure_capability_profile_target_columns(conn)

    _mark_migration(conn, name)
    applied.append(name)


# ---------------------------------------------------------------------------
# ══════════════════════════════════════════════════════════════════════════
# BLOCO 1 — Tabelas de identidade e sessão
# ══════════════════════════════════════════════════════════════════════════
# ---------------------------------------------------------------------------

def _create_users(conn, applied: list[str]) -> None:
    name = "users.create_table_v2"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id                  VARCHAR(36)  NOT NULL PRIMARY KEY,
            full_name           VARCHAR(255) NOT NULL,
            email               VARCHAR(255) NOT NULL,
            phone               VARCHAR(32),
            password_hash       VARCHAR(255) NOT NULL,
            is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
            email_verified      BOOLEAN      NOT NULL DEFAULT FALSE,
            phone_verified      BOOLEAN      NOT NULL DEFAULT FALSE,
            -- LGPD: preferência de idioma para comunicações
            locale              VARCHAR(10)  NOT NULL DEFAULT 'pt-BR',
            -- 2FA
            totp_secret_ref     VARCHAR(255),          -- referência ao vault
            totp_enabled        BOOLEAN      NOT NULL DEFAULT FALSE,
            -- Soft-delete LGPD (anonimização)
            anonymized_at       TIMESTAMPTZ,
            created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_users_email ON users (email) "
        "WHERE anonymized_at IS NULL"
    ))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_phone ON users (phone)"))
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
    conn.execute(text(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_auth_sessions_token_hash "
        "ON auth_sessions (session_token_hash)"
    ))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_auth_sessions_user_id "
        "ON auth_sessions (user_id)"
    ))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_auth_sessions_expires_at "
        "ON auth_sessions (expires_at) WHERE revoked_at IS NULL"
    ))
    _mark_migration(conn, name)
    applied.append(name)


# ---------------------------------------------------------------------------
# ══════════════════════════════════════════════════════════════════════════
# BLOCO 2 — Operadores, Lockers e Slots
# ══════════════════════════════════════════════════════════════════════════
# ---------------------------------------------------------------------------

def _create_locker_operators(conn, applied: list[str]) -> None:
    name = "locker_operators.create_table_v2"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS locker_operators (
            id                  VARCHAR(64)  PRIMARY KEY,
            name                VARCHAR(128) NOT NULL,
            document            VARCHAR(32),           -- CNPJ/CPF
            email               VARCHAR(128),
            phone               VARCHAR(32),
            -- LOGISTICS = transportadora, ECOMMERCE = loja, OWN = próprio
            operator_type       VARCHAR(32)  NOT NULL DEFAULT 'LOGISTICS',
            country             VARCHAR(2)   NOT NULL DEFAULT 'BR',
            active              BOOLEAN      NOT NULL DEFAULT TRUE,
            -- Comissionamento
            commission_rate     NUMERIC(6,4),          -- ex: 0.0350 = 3,5%
            currency            VARCHAR(8)   NOT NULL DEFAULT 'BRL',
            -- Contrato
            contract_start_at   TIMESTAMPTZ,
            contract_end_at     TIMESTAMPTZ,
            contract_ref        VARCHAR(255),
            -- Configuração de SLA
            sla_pickup_hours    INTEGER      NOT NULL DEFAULT 72,
            sla_return_hours    INTEGER      NOT NULL DEFAULT 24,
            created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_locker_operators_document "
        "ON locker_operators (document)"
    ))
    _mark_migration(conn, name)
    applied.append(name)


def _create_lockers(conn, applied: list[str]) -> None:
    name = "lockers.create_table_v2"
    if _migration_applied(conn, name):
        return
    jsonb = _jsonb_or_text(conn)
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS lockers (
            id                      VARCHAR(36)   PRIMARY KEY,

            -- Identificação
            display_name            VARCHAR(255),
            external_id             VARCHAR(100),         -- ID no sistema do operador
            machine_id              VARCHAR(100),         -- ID físico do hardware

            -- Relacionamentos
            operator_id             VARCHAR(64)   REFERENCES locker_operators(id),
            tenant_id               VARCHAR(100),         -- Para SaaS multi-tenant
            site_id                 VARCHAR(100),

            -- Geografia
            region                  VARCHAR(10)   NOT NULL,
            timezone                VARCHAR(50)   NOT NULL DEFAULT 'America/Sao_Paulo',
            country                 VARCHAR(2)    NOT NULL DEFAULT 'BR',
            address_line            VARCHAR(255),
            address_number          VARCHAR(50),
            address_extra           VARCHAR(255),
            district                VARCHAR(100),
            city                    VARCHAR(100),
            state                   VARCHAR(100),
            postal_code             VARCHAR(20),
            latitude                DOUBLE PRECISION,
            longitude               DOUBLE PRECISION,
            -- PostGIS-ready (ativar quando disponível): GEOMETRY(Point, 4326)
            geolocation_wkt         VARCHAR(100),         -- WKT fallback: 'POINT(lng lat)'

            -- Capacidade e dimensões
            slots_count             INTEGER       NOT NULL DEFAULT 0,
            slots_available         INTEGER       NOT NULL DEFAULT 0,

            -- Operação
            active                  BOOLEAN       NOT NULL DEFAULT TRUE,
            allowed_channels        VARCHAR(100),         -- 'ONLINE,KIOSK'
            allowed_payment_methods VARCHAR(255),
            access_hours            TEXT,                 -- JSON com horários por dia

            -- Recursos físicos
            has_alarm               BOOLEAN       NOT NULL DEFAULT FALSE,
            has_camera              BOOLEAN       NOT NULL DEFAULT FALSE,
            has_kiosk               BOOLEAN       NOT NULL DEFAULT FALSE,
            has_printer             BOOLEAN       NOT NULL DEFAULT FALSE,
            has_card_reader         BOOLEAN       NOT NULL DEFAULT FALSE,
            has_nfc                 BOOLEAN       NOT NULL DEFAULT FALSE,
            is_rented               BOOLEAN       NOT NULL DEFAULT FALSE,

            -- Classificação
            security_level          VARCHAR(50),          -- STANDARD, HIGH, VAULT
            temperature_zone        VARCHAR(50),          -- AMBIENT, REFRIGERATED, FROZEN

            -- Metadados livres
            description             TEXT,
            metadata_json           {jsonb},

            created_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_lockers_active      ON lockers (active)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_lockers_operator    ON lockers (operator_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_lockers_region      ON lockers (region)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_lockers_site_id     ON lockers (site_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_lockers_tenant_id   ON lockers (tenant_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_lockers_machine_id  ON lockers (machine_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_lockers_lat_lng     ON lockers (latitude, longitude)"))
    _mark_migration(conn, name)
    applied.append(name)


def _create_tenant_fiscal_config(conn, applied: list[str]) -> None:
    """Dados fiscais do emitente por tenant (O-1 — NFC-e / faturação)."""
    name = "tenant_fiscal_config.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS tenant_fiscal_config (
            tenant_id       VARCHAR(100) PRIMARY KEY,
            cnpj            VARCHAR(18)  NOT NULL,
            razao_social    VARCHAR(140) NOT NULL,
            ie              VARCHAR(20),
            regime          VARCHAR(20)  NOT NULL,
            crt             CHAR(1)      NOT NULL,
            cert_a1_ref     VARCHAR(255),
            is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_tenant_fiscal_active ON tenant_fiscal_config (is_active)"
    ))
    _mark_migration(conn, name)
    applied.append(name)


def _create_locker_slot_configs(conn, applied: list[str]) -> None:
    """Configuração estática de tamanhos disponíveis por locker."""
    name = "locker_slot_configs.create_table_v2"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS locker_slot_configs (
            id              BIGSERIAL    PRIMARY KEY,
            locker_id       VARCHAR(36)  NOT NULL REFERENCES lockers(id) ON DELETE CASCADE,
            -- XS, S, M, L, XL, XXL — padronizado com InPost/DHL
            slot_size       VARCHAR(8)   NOT NULL,
            slot_count      INTEGER      NOT NULL DEFAULT 0,
            available_count INTEGER      NOT NULL DEFAULT 0,
            -- Dimensões internas da gaveta
            width_mm        INTEGER,
            height_mm        INTEGER,
            depth_mm        INTEGER,
            max_weight_g    INTEGER,
            created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            UNIQUE (locker_id, slot_size)
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_slot_configs_locker "
        "ON locker_slot_configs (locker_id)"
    ))
    _mark_migration(conn, name)
    applied.append(name)


def _create_locker_slots(conn, applied: list[str]) -> None:
    """Estado real-time de cada gaveta física."""
    name = "locker_slots.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS locker_slots (
            id                    VARCHAR(36)  PRIMARY KEY,
            locker_id             VARCHAR(36)  NOT NULL REFERENCES lockers(id),
            -- Label físico na porta: '01A', 'B-03', etc.
            slot_label            VARCHAR(20)  NOT NULL,
            slot_size             VARCHAR(8)   NOT NULL,
            -- AVAILABLE | OCCUPIED | BLOCKED | MAINTENANCE | RESERVED
            status                VARCHAR(20)  NOT NULL DEFAULT 'AVAILABLE',
            occupied_since        TIMESTAMPTZ,
            -- FKs preenchidas quando ocupada
            current_allocation_id VARCHAR(36),
            current_delivery_id   VARCHAR(36),
            current_rental_id     VARCHAR(36),
            -- Auditoria de hardware
            last_opened_at        TIMESTAMPTZ,
            last_closed_at        TIMESTAMPTZ,
            -- Código de falha do firmware
            fault_code            VARCHAR(50),
            fault_detail          TEXT,
            created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            UNIQUE (locker_id, slot_label)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_locker_slots_locker_status ON locker_slots (locker_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_locker_slots_status        ON locker_slots (status)"))
    _mark_migration(conn, name)
    applied.append(name)


def _create_locker_telemetry(conn, applied: list[str]) -> None:
    """Eventos de sensor/IoT por locker — série temporal, append-only."""
    name = "locker_telemetry.create_table_v1"
    if _migration_applied(conn, name):
        return
    jsonb = _jsonb_or_text(conn)
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS locker_telemetry (
            id                  BIGSERIAL    PRIMARY KEY,
            locker_id           VARCHAR(36)  NOT NULL,
            -- DOOR_OPEN | DOOR_CLOSE | TEMP_ALERT | HUMIDITY_ALERT |
            -- POWER_FAIL | POWER_RESTORED | TAMPER | LOCK_FAIL | CONNECTIVITY
            event_type          VARCHAR(50)  NOT NULL,
            slot_label          VARCHAR(20),
            temperature_celsius NUMERIC(5,2),
            humidity_pct        NUMERIC(5,2),
            battery_pct         NUMERIC(5,2),
            voltage_mv          INTEGER,
            signal_rssi         INTEGER,
            -- Firmware
            firmware_version    VARCHAR(50),
            raw_payload_json    {jsonb},
            occurred_at         TIMESTAMPTZ  NOT NULL,
            received_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    # Série temporal: sempre consultas por locker + janela de tempo
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_locker_telemetry_locker_time "
        "ON locker_telemetry (locker_id, occurred_at DESC)"
    ))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_locker_telemetry_event_time "
        "ON locker_telemetry (event_type, occurred_at DESC)"
    ))
    # Dica: usar TimescaleDB ou particionamento por mês em produção
    _mark_migration(conn, name)
    applied.append(name)


# ---------------------------------------------------------------------------
# ══════════════════════════════════════════════════════════════════════════
# BLOCO 3 — Produtos e Regras de Compatibilidade
# ══════════════════════════════════════════════════════════════════════════
# ---------------------------------------------------------------------------

def _create_product_categories(conn, applied: list[str]) -> None:
    name = "product_categories.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_categories (
            id                       VARCHAR(64)  PRIMARY KEY,
            name                     VARCHAR(128) NOT NULL,
            description              TEXT,
            parent_category          VARCHAR(64)  REFERENCES product_categories(id),
            -- Temperatura padrão: AMBIENT | REFRIGERATED | FROZEN
            default_temperature_zone VARCHAR(32)  NOT NULL DEFAULT 'AMBIENT',
            -- Segurança: STANDARD | HIGH | VAULT
            default_security_level   VARCHAR(32)  NOT NULL DEFAULT 'STANDARD',
            -- Restrições
            is_hazardous             BOOLEAN      NOT NULL DEFAULT FALSE,
            requires_age_verification BOOLEAN     NOT NULL DEFAULT FALSE,
            max_weight_g             INTEGER,
            created_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_product_categories_parent "
        "ON product_categories (parent_category)"
    ))
    _mark_migration(conn, name)
    applied.append(name)


def _create_product_locker_configs(conn, applied: list[str]) -> None:
    """Regras de compatibilidade produto × locker. Criada APÓS product_categories."""
    name = "product_locker_configs.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS product_locker_configs (
            id                  BIGSERIAL    PRIMARY KEY,
            locker_id           VARCHAR(36)  NOT NULL REFERENCES lockers(id) ON DELETE CASCADE,
            category            VARCHAR(64)  NOT NULL REFERENCES product_categories(id),
            subcategory         VARCHAR(64),
            allowed             BOOLEAN      NOT NULL DEFAULT TRUE,
            temperature_zone    VARCHAR(32)  NOT NULL DEFAULT 'ANY',
            min_value_cents     BIGINT,
            max_value_cents     BIGINT,
            max_weight_g        INTEGER,
            max_width_mm        INTEGER,
            max_height_mm       INTEGER,
            max_depth_mm        INTEGER,
            requires_signature  BOOLEAN      NOT NULL DEFAULT FALSE,
            requires_id_check   BOOLEAN      NOT NULL DEFAULT FALSE,
            is_fragile          BOOLEAN      NOT NULL DEFAULT FALSE,
            is_hazardous        BOOLEAN      NOT NULL DEFAULT FALSE,
            priority            INTEGER      NOT NULL DEFAULT 100,
            notes               TEXT,
            created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            UNIQUE (locker_id, category)
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_product_cfg_locker   ON product_locker_configs (locker_id)"
    ))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_product_cfg_category ON product_locker_configs (category)"
    ))
    _mark_migration(conn, name)
    applied.append(name)


# ---------------------------------------------------------------------------
# ══════════════════════════════════════════════════════════════════════════
# BLOCO 4 — Aluguel de Slots (Caso de Uso 3)
# ══════════════════════════════════════════════════════════════════════════
# ---------------------------------------------------------------------------

def _create_rental_plans(conn, applied: list[str]) -> None:
    name = "rental_plans.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS rental_plans (
            id                  VARCHAR(36)  PRIMARY KEY,
            -- NULL = plano global; preenchido = plano exclusivo do locker
            locker_id           VARCHAR(36)  REFERENCES lockers(id),
            -- NULL = qualquer tamanho
            slot_size           VARCHAR(8),
            name                VARCHAR(128) NOT NULL,
            description         TEXT,
            -- HOURLY | DAILY | WEEKLY | MONTHLY | YEARLY
            billing_cycle       VARCHAR(20)  NOT NULL,
            amount_cents        INTEGER      NOT NULL,
            currency            VARCHAR(8)   NOT NULL DEFAULT 'BRL',
            -- Duração máxima contratável (NULL = ilimitado)
            max_duration_days   INTEGER,
            -- Carência em horas para renovação automática
            grace_period_hours  INTEGER      NOT NULL DEFAULT 24,
            active              BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_rental_plans_locker ON rental_plans (locker_id)"
    ))
    _mark_migration(conn, name)
    applied.append(name)


def _create_rental_contracts(conn, applied: list[str]) -> None:
    name = "rental_contracts.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS rental_contracts (
            id                  VARCHAR(36)  PRIMARY KEY,
            locker_id           VARCHAR(36)  NOT NULL REFERENCES lockers(id),
            slot_label          VARCHAR(20)  NOT NULL,
            plan_id             VARCHAR(36)  REFERENCES rental_plans(id),
            tenant_id           VARCHAR(100),

            -- Locatário (pode ser user cadastrado ou guest)
            renter_user_id      VARCHAR(36)  REFERENCES users(id),
            renter_name         VARCHAR(255),
            renter_document     VARCHAR(32),   -- CPF/CNPJ
            renter_phone        VARCHAR(32),
            renter_email        VARCHAR(128),

            -- Financeiro
            amount_cents        INTEGER      NOT NULL,
            currency            VARCHAR(8)   NOT NULL DEFAULT 'BRL',
            billing_cycle       VARCHAR(20)  NOT NULL,
            next_billing_at     TIMESTAMPTZ,
            auto_renew          BOOLEAN      NOT NULL DEFAULT FALSE,

            -- Vigência
            -- PENDING | ACTIVE | SUSPENDED | OVERDUE | ENDED | CANCELLED
            status              VARCHAR(20)  NOT NULL DEFAULT 'PENDING',
            started_at          TIMESTAMPTZ,
            ends_at             TIMESTAMPTZ,
            cancelled_at        TIMESTAMPTZ,
            cancel_reason       VARCHAR(255),
            ended_at            TIMESTAMPTZ,

            -- Acesso
            access_pin_hash     VARCHAR(255),  -- PIN da gaveta durante o aluguel
            access_token_ref    VARCHAR(255),  -- referência a pickup_tokens se aplicável

            created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_rental_locker_slot   ON rental_contracts (locker_id, slot_label)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_rental_status        ON rental_contracts (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_rental_renter_user   ON rental_contracts (renter_user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_rental_next_billing  ON rental_contracts (next_billing_at) WHERE status = 'ACTIVE'"))
    _mark_migration(conn, name)
    applied.append(name)


# ---------------------------------------------------------------------------
# ══════════════════════════════════════════════════════════════════════════
# BLOCO 5 — Parceiros Logísticos (Caso de Uso 4)
# ══════════════════════════════════════════════════════════════════════════
# ---------------------------------------------------------------------------

def _create_logistics_partners(conn, applied: list[str]) -> None:
    name = "logistics_partners.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS logistics_partners (
            id                      VARCHAR(36)  PRIMARY KEY,
            name                    VARCHAR(128) NOT NULL,
            -- 'CORREIOS' | 'DHL' | 'JADLOG' | 'FEDEX' | 'SHOPEE_XPRESS' etc.
            code                    VARCHAR(32)  NOT NULL UNIQUE,
            -- WEBHOOK | POLLING | MANUAL | SFTP
            integration_type        VARCHAR(30)  NOT NULL,
            api_base_url            VARCHAR(500),
            tracking_url_template   VARCHAR(500), -- ex: 'https://rastreio.xyz/{code}'
            -- Auth: OAUTH2 | API_KEY | BASIC | MTLS
            auth_type               VARCHAR(20),
            -- Referência ao Vault (nunca armazenar credencial inline)
            credentials_secret_ref  VARCHAR(255),
            -- SLA padrão: horas máximas para o destinatário retirar
            default_sla_hours       INTEGER      NOT NULL DEFAULT 72,
            -- Horas antes do prazo para enviar 1º lembrete
            reminder_hours_before   INTEGER      NOT NULL DEFAULT 24,
            active                  BOOLEAN      NOT NULL DEFAULT TRUE,
            country                 VARCHAR(2)   NOT NULL DEFAULT 'BR',
            created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    _mark_migration(conn, name)
    applied.append(name)


def _create_inbound_deliveries(conn, applied: list[str]) -> None:
    """
    Encomendas depositadas por parceiros logísticos aguardando retirada pelo destinatário.
    Fluxo: parceiro deposita → destinatário notificado → destinatário retira (ou devolve).
    """
    name = "inbound_deliveries.create_table_v1"
    if _migration_applied(conn, name):
        return
    jsonb = _jsonb_or_text(conn)
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS inbound_deliveries (
            id                      VARCHAR(36)  PRIMARY KEY,
            logistics_partner_id    VARCHAR(36)  NOT NULL REFERENCES logistics_partners(id),
            locker_id               VARCHAR(36)  NOT NULL REFERENCES lockers(id),
            slot_label              VARCHAR(20),

            -- Rastreamento
            tracking_code           VARCHAR(128) NOT NULL,
            barcode                 VARCHAR(128),
            partner_order_ref       VARCHAR(128), -- ID do pedido no sistema do parceiro

            -- Destinatário
            recipient_name          VARCHAR(255),
            recipient_document      VARCHAR(32),
            recipient_phone         VARCHAR(32),
            recipient_email         VARCHAR(128),

            -- Pacote
            weight_g                INTEGER,
            width_mm                INTEGER,
            height_mm               INTEGER,
            depth_mm                INTEGER,
            declared_value_cents    INTEGER,
            currency                VARCHAR(8)   NOT NULL DEFAULT 'BRL',
            requires_signature      BOOLEAN      NOT NULL DEFAULT FALSE,
            requires_id_check       BOOLEAN      NOT NULL DEFAULT FALSE,

            -- Ciclo de vida
            -- PENDING | STORED | NOTIFIED | PICKED_UP | RETURNED | EXPIRED | LOST
            status                  VARCHAR(20)  NOT NULL DEFAULT 'PENDING',
            stored_at               TIMESTAMPTZ,
            first_notified_at       TIMESTAMPTZ,
            last_notified_at        TIMESTAMPTZ,
            notification_count      INTEGER      NOT NULL DEFAULT 0,
            pickup_deadline_at      TIMESTAMPTZ,
            picked_up_at            TIMESTAMPTZ,
            returned_at             TIMESTAMPTZ,
            return_reason           VARCHAR(255),

            -- Token de retirada (gerado ao armazenar)
            pickup_token_id         VARCHAR(36),

            -- Payload bruto do parceiro para disputas
            carrier_payload_json    {jsonb},

            created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_inbound_tracking ON inbound_deliveries (logistics_partner_id, tracking_code)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_inbound_locker_status ON inbound_deliveries (locker_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_inbound_status         ON inbound_deliveries (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_inbound_deadline       ON inbound_deliveries (pickup_deadline_at) WHERE status NOT IN ('PICKED_UP', 'RETURNED', 'EXPIRED')"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_inbound_recipient_phone ON inbound_deliveries (recipient_phone)"))
    _mark_migration(conn, name)
    applied.append(name)


# ---------------------------------------------------------------------------
# ══════════════════════════════════════════════════════════════════════════
# BLOCO 6 — Parceiros de E-commerce (Caso de Uso 5)
# ══════════════════════════════════════════════════════════════════════════
# ---------------------------------------------------------------------------

def _create_ecommerce_partners(conn, applied: list[str]) -> None:
    name = "ecommerce_partners.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ecommerce_partners (
            id                      VARCHAR(36)  PRIMARY KEY,
            name                    VARCHAR(128) NOT NULL,
            -- 'SHOPEE' | 'MERCADOLIVRE' | 'AMAZON' | 'MAGALU' etc.
            code                    VARCHAR(32)  NOT NULL UNIQUE,
            -- API_PUSH | WEBHOOK | SFTP | MANUAL
            integration_type        VARCHAR(30)  NOT NULL,
            api_base_url            VARCHAR(500),
            -- Referência ao Vault
            credentials_secret_ref  VARCHAR(255),
            webhook_secret_ref      VARCHAR(255),
            -- Financeiro
            revenue_share_pct       NUMERIC(6,4),  -- % da transação
            currency                VARCHAR(8)   NOT NULL DEFAULT 'BRL',
            -- SLA contratado para retirada (em horas)
            sla_pickup_hours        INTEGER      NOT NULL DEFAULT 72,
            active                  BOOLEAN      NOT NULL DEFAULT TRUE,
            country                 VARCHAR(2)   NOT NULL DEFAULT 'BR',
            created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    _mark_migration(conn, name)
    applied.append(name)


def _create_webhook_endpoints(conn, applied: list[str]) -> None:
    name = "webhook_endpoints.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS webhook_endpoints (
            id              VARCHAR(36)  PRIMARY KEY,
            -- ECOMMERCE | LOGISTICS | PAYMENT | RENTAL | INTERNAL
            partner_type    VARCHAR(20)  NOT NULL,
            partner_id      VARCHAR(36)  NOT NULL,
            url             VARCHAR(500) NOT NULL,
            -- CSV dos eventos inscritos: 'order.paid,pickup.redeemed'
            events          TEXT         NOT NULL,
            secret_ref      VARCHAR(255),
            -- Algoritmo de assinatura: HMAC_SHA256 | HMAC_SHA512
            signing_algo    VARCHAR(20)  NOT NULL DEFAULT 'HMAC_SHA256',
            active          BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_webhook_ep_partner ON webhook_endpoints (partner_type, partner_id)"
    ))
    _mark_migration(conn, name)
    applied.append(name)


def _create_webhook_deliveries(conn, applied: list[str]) -> None:
    name = "webhook_deliveries.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS webhook_deliveries (
            id                  VARCHAR(36)  PRIMARY KEY,
            endpoint_id         VARCHAR(36)  NOT NULL REFERENCES webhook_endpoints(id),
            event_name          VARCHAR(100) NOT NULL,
            aggregate_type      VARCHAR(50),
            aggregate_id        VARCHAR(36),
            payload_json        TEXT         NOT NULL,
            -- PENDING | DELIVERED | FAILED | SKIPPED
            status              VARCHAR(20)  NOT NULL DEFAULT 'PENDING',
            attempt_count       INTEGER      NOT NULL DEFAULT 0,
            max_attempts        INTEGER      NOT NULL DEFAULT 5,
            last_status_code    INTEGER,
            last_response_body  TEXT,
            last_attempt_at     TIMESTAMPTZ,
            next_attempt_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            delivered_at        TIMESTAMPTZ,
            created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_webhook_del_status_next  ON webhook_deliveries (status, next_attempt_at) WHERE status IN ('PENDING', 'FAILED')"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_webhook_del_endpoint      ON webhook_deliveries (endpoint_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_webhook_del_aggregate     ON webhook_deliveries (aggregate_type, aggregate_id)"))
    _mark_migration(conn, name)
    applied.append(name)


# ---------------------------------------------------------------------------
# ══════════════════════════════════════════════════════════════════════════
# BLOCO 7 — Pedidos e Pagamentos
# ══════════════════════════════════════════════════════════════════════════
# ---------------------------------------------------------------------------

def _create_orders(conn, applied: list[str]) -> None:
    name = "orders.create_table_v3"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS orders (
            id                          VARCHAR(36)  PRIMARY KEY,

            -- Usuário (NULL = guest)
            user_id                     VARCHAR(36)  REFERENCES users(id),

            -- Origem
            -- ONLINE | KIOSK | API | PARTNER
            channel                     VARCHAR(10)  NOT NULL,
            region                      VARCHAR(10)  NOT NULL,
            totem_id                    VARCHAR(36)  NOT NULL,   -- locker físico
            site_id                     VARCHAR(100),
            tenant_id                   VARCHAR(100),

            -- Parceiro de e-commerce (se aplicável)
            ecommerce_partner_id        VARCHAR(36)  REFERENCES ecommerce_partners(id),
            partner_order_ref           VARCHAR(128),

            -- Produto/SKU
            sku_id                      VARCHAR(128) NOT NULL,
            sku_description             VARCHAR(255),
            slot_size                   VARCHAR(8),

            -- Financeiro
            amount_cents                INTEGER      NOT NULL,
            currency                    VARCHAR(8)   NOT NULL DEFAULT 'BRL',

            -- Status geral do pedido
            -- CREATED | PAID | READY | PICKED_UP | CANCELLED | REFUNDED | EXPIRED
            status                      VARCHAR(20)  NOT NULL DEFAULT 'CREATED',

            -- Pagamento
            -- CREATED | PENDING | APPROVED | DECLINED | REFUNDED | CHARGEBACK | CANCELLED
            payment_status              VARCHAR(30)  NOT NULL DEFAULT 'CREATED',
            payment_method              VARCHAR(30),   -- CREDIT_CARD | DEBIT_CARD | PIX | CASH | WALLET
            card_type                   VARCHAR(10),   -- VISA | MASTER | ELO | AMEX
            card_last4                  VARCHAR(4),
            card_brand                  VARCHAR(20),
            installments                INTEGER      NOT NULL DEFAULT 1,
            gateway_transaction_id      VARCHAR(128),
            payment_updated_at          TIMESTAMPTZ,
            paid_at                     TIMESTAMPTZ,

            -- Prazos
            pickup_deadline_at          TIMESTAMPTZ,
            picked_up_at                TIMESTAMPTZ,

            -- Acesso público sem autenticação (e.g., link de status no e-mail)
            public_access_token_hash    VARCHAR(255),

            -- Dados de guest
            guest_session_id            VARCHAR(128),
            guest_name                  VARCHAR(255),
            guest_email                 VARCHAR(255),
            guest_phone                 VARCHAR(32),

            -- Recibo
            receipt_email               VARCHAR(255),
            receipt_phone               VARCHAR(32),

            -- LGPD
            consent_marketing           BOOLEAN      NOT NULL DEFAULT FALSE,
            consent_analytics           BOOLEAN      NOT NULL DEFAULT FALSE,

            -- Cancelamento/devolução
            cancelled_at                TIMESTAMPTZ,
            cancel_reason               VARCHAR(255),
            refunded_at                 TIMESTAMPTZ,
            refund_reason               VARCHAR(255),

            created_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_status                ON orders (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_channel_status        ON orders (channel, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_region_status         ON orders (region, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_region_totem_status   ON orders (region, totem_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_region_totem_created  ON orders (region, totem_id, created_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_paid_at               ON orders (paid_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_picked_up_at          ON orders (picked_up_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_status_picked_up      ON orders (status, picked_up_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_totem_picked_up       ON orders (totem_id, picked_up_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_user_id               ON orders (user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_ecommerce_partner     ON orders (ecommerce_partner_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_public_token_hash     ON orders (public_access_token_hash)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_orders_pickup_deadline       ON orders (pickup_deadline_at) WHERE status NOT IN ('PICKED_UP','CANCELLED','REFUNDED','EXPIRED')"))
    _mark_migration(conn, name)
    applied.append(name)


def _create_payment_transactions(conn, applied: list[str]) -> None:
    """
    Trilha de auditoria de cada tentativa de pagamento — necessário para
    PCI-DSS, chargebacks e reconciliação financeira.
    """
    name = "payment_transactions.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payment_transactions (
            id                      VARCHAR(36)  PRIMARY KEY,
            order_id                VARCHAR(36)  NOT NULL REFERENCES orders(id),

            -- Gateway: STRIPE | CIELO | STONE | ADYEN | PAGARME | MERCADOPAGO | REDE
            gateway                 VARCHAR(50)  NOT NULL,
            gateway_transaction_id  VARCHAR(128),
            gateway_idempotency_key VARCHAR(128),

            -- Valor
            amount_cents            INTEGER      NOT NULL,
            currency                VARCHAR(8)   NOT NULL DEFAULT 'BRL',

            -- Método: CREDIT_CARD | DEBIT_CARD | PIX | CASH | VOUCHER | WALLET
            payment_method          VARCHAR(30)  NOT NULL,
            card_brand              VARCHAR(20),
            card_last4              VARCHAR(4),
            card_type               VARCHAR(10),
            installments            INTEGER      NOT NULL DEFAULT 1,

            -- NSU/AUT para conciliação com a adquirente
            nsu                     VARCHAR(50),
            authorization_code      VARCHAR(50),

            -- Status: INITIATED | PENDING | APPROVED | DECLINED | REFUNDED |
            --         CHARGEBACK | CANCELLED | TIMEOUT | ERROR
            status                  VARCHAR(20)  NOT NULL DEFAULT 'INITIATED',
            error_code              VARCHAR(100),
            error_message           TEXT,

            -- Payload bruto para disputas — nunca remover
            raw_request_json        TEXT,
            raw_response_json       TEXT,

            -- Timestamps
            initiated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            approved_at             TIMESTAMPTZ,
            settled_at              TIMESTAMPTZ,
            refunded_at             TIMESTAMPTZ,
            refund_reason           VARCHAR(255),
            refund_amount_cents     INTEGER,
            chargeback_at           TIMESTAMPTZ,
            chargeback_reason       VARCHAR(255),

            created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_payment_tx_order      ON payment_transactions (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_payment_tx_status     ON payment_transactions (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_payment_tx_gateway_id ON payment_transactions (gateway, gateway_transaction_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_payment_tx_nsu        ON payment_transactions (nsu)"))
    _mark_migration(conn, name)
    applied.append(name)


# ---------------------------------------------------------------------------
# ══════════════════════════════════════════════════════════════════════════
# BLOCO 8 — Alocações e Pickups
# ══════════════════════════════════════════════════════════════════════════
# ---------------------------------------------------------------------------

def _create_allocations(conn, applied: list[str]) -> None:
    name = "allocations.create_table_v2"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS allocations (
            id          VARCHAR(36)  PRIMARY KEY,
            order_id    VARCHAR(36)  NOT NULL REFERENCES orders(id),
            locker_id   VARCHAR(36)  NOT NULL REFERENCES lockers(id),
            slot        VARCHAR(20)  NOT NULL,
            slot_size   VARCHAR(8),
            -- PENDING | CONFIRMED | RELEASED | FAILED
            state       VARCHAR(20)  NOT NULL DEFAULT 'PENDING',
            allocated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            released_at  TIMESTAMPTZ,
            release_reason VARCHAR(255),
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_alloc_order_id          ON allocations (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_alloc_state             ON allocations (state)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_alloc_locker_slot_state ON allocations (locker_id, slot, state)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_alloc_created_at        ON allocations (created_at)"))
    _mark_migration(conn, name)
    applied.append(name)


def _create_pickups(conn, applied: list[str]) -> None:
    name = "pickups.create_table_v3"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS pickups (
            id                  VARCHAR(36)  PRIMARY KEY,
            order_id            VARCHAR(36)  NOT NULL UNIQUE REFERENCES orders(id),

            -- Contexto de canal e localização
            -- ONLINE | KIOSK | API | PARTNER
            channel             VARCHAR(10)  NOT NULL,
            region              VARCHAR(10)  NOT NULL,
            locker_id           VARCHAR(36)  REFERENCES lockers(id),
            machine_id          VARCHAR(100),
            slot                VARCHAR(20),
            operator_id         VARCHAR(64)  REFERENCES locker_operators(id),
            tenant_id           VARCHAR(100),
            site_id             VARCHAR(100),

            -- Estado
            -- ACTIVE | REDEEMED | EXPIRED | CANCELLED
            status              VARCHAR(16)  NOT NULL DEFAULT 'ACTIVE',
            -- AWAITING_PAYMENT | READY_FOR_PICKUP | IN_PROGRESS |
            -- COMPLETED | EXPIRED | CANCELLED
            lifecycle_stage     VARCHAR(24)  NOT NULL DEFAULT 'AWAITING_PAYMENT',

            -- Token de acesso atual
            current_token_id    VARCHAR(36),

            -- Timestamps de ciclo de vida granular (auditoria e KPI)
            activated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            ready_at            TIMESTAMPTZ,     -- quando a gaveta ficou pronta
            expires_at          TIMESTAMPTZ,
            door_opened_at      TIMESTAMPTZ,     -- sensor: porta aberta
            item_removed_at     TIMESTAMPTZ,     -- sensor: item retirado
            door_closed_at      TIMESTAMPTZ,     -- sensor: porta fechada
            redeemed_at         TIMESTAMPTZ,     -- confirmação do pickup
            -- KIOSK | QR_CODE | PIN | NFC | APP | STAFF
            redeemed_via        VARCHAR(16),
            expired_at          TIMESTAMPTZ,
            cancelled_at        TIMESTAMPTZ,
            cancel_reason       VARCHAR(255),

            -- Rastreabilidade de eventos
            correlation_id      VARCHAR(36),
            source_event_id     VARCHAR(36),
            sensor_event_id     VARCHAR(36),
            notes               TEXT,

            created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_order_id       ON pickups (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_status         ON pickups (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_channel_status ON pickups (channel, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_region_status  ON pickups (region, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_locker_status  ON pickups (locker_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_machine_status ON pickups (machine_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_slot_status    ON pickups (slot, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_operator       ON pickups (operator_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_tenant         ON pickups (tenant_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_site           ON pickups (site_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_expires_at     ON pickups (expires_at) WHERE status = 'ACTIVE'"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_redeemed_at   ON pickups (redeemed_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_created_at    ON pickups (created_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_lifecycle      ON pickups (lifecycle_stage)"))
    _mark_migration(conn, name)
    applied.append(name)


def _create_pickup_tokens(conn, applied: list[str]) -> None:
    """
    Tokens de acesso à gaveta — histórico completo por pickup.
    Suporta QR Code, PIN numérico, NFC e link profundo para app.
    """
    name = "pickup_tokens.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS pickup_tokens (
            id              VARCHAR(36)  PRIMARY KEY,
            pickup_id       VARCHAR(36)  NOT NULL REFERENCES pickups(id) ON DELETE CASCADE,

            -- QR_CODE | PIN | NFC | BARCODE | DEEP_LINK | STAFF_OVERRIDE
            token_type      VARCHAR(20)  NOT NULL DEFAULT 'QR_CODE',

            -- Hash do segredo — nunca armazenar o token em claro
            token_hash      VARCHAR(255) NOT NULL UNIQUE,

            -- Controle de uso
            is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
            attempt_count   INTEGER      NOT NULL DEFAULT 0,
            max_attempts    INTEGER      NOT NULL DEFAULT 5,

            -- Tempos
            issued_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            expires_at      TIMESTAMPTZ,
            first_used_at   TIMESTAMPTZ,
            last_used_at    TIMESTAMPTZ,
            revoked_at      TIMESTAMPTZ,
            revoke_reason   VARCHAR(100),

            -- Quem gerou (sistema, operador, staff)
            issued_by       VARCHAR(100),

            created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickup_tokens_pickup   ON pickup_tokens (pickup_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickup_tokens_active   ON pickup_tokens (pickup_id, is_active) WHERE is_active = TRUE"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickup_tokens_expires  ON pickup_tokens (expires_at) WHERE is_active = TRUE"))
    _mark_migration(conn, name)
    applied.append(name)


# ---------------------------------------------------------------------------
# ══════════════════════════════════════════════════════════════════════════
# BLOCO 9 — Documentos Fiscais e Notificações
# ══════════════════════════════════════════════════════════════════════════
# ---------------------------------------------------------------------------

def _create_fiscal_documents(conn, applied: list[str]) -> None:
    name = "fiscal_documents.create_table_v2"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS fiscal_documents (
            id                  VARCHAR(36)  PRIMARY KEY,
            order_id            VARCHAR(36)  NOT NULL UNIQUE REFERENCES orders(id),

            -- CUPOM_FISCAL | NF-E | NFC-E | SAT | BOLETO | RECEIPT_INTL
            document_type       VARCHAR(50)  NOT NULL,
            receipt_code        VARCHAR(64)  NOT NULL UNIQUE,

            -- Contexto
            channel             VARCHAR(20),
            region              VARCHAR(10),
            tenant_id           VARCHAR(100),

            -- Financeiro
            amount_cents        INTEGER      NOT NULL,
            currency            VARCHAR(10)  NOT NULL DEFAULT 'BRL',
            tax_amount_cents    INTEGER,
            tax_breakdown_json  TEXT,

            -- Entrega
            -- EMAIL | SMS | PRINT | WHATSAPP | NONE
            delivery_mode       VARCHAR(20),
            send_status         VARCHAR(50),
            send_target         VARCHAR(255),
            sent_at             TIMESTAMPTZ,

            -- Impressão física (KIOSK/totem)
            print_status        VARCHAR(50),
            print_site_path     VARCHAR(255),
            printed_at          TIMESTAMPTZ,

            -- Payload completo do documento (XML NF-e, JSON SAT, etc.)
            payload_json        TEXT         NOT NULL,
            xml_signed          TEXT,         -- XML assinado da NF-e/NFC-e
            chave_acesso        VARCHAR(64),  -- chave de acesso SEFAZ

            issued_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            cancelled_at        TIMESTAMPTZ,
            cancel_reason       VARCHAR(255),

            created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_fiscal_docs_receipt  ON fiscal_documents (receipt_code)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_fiscal_docs_issued   ON fiscal_documents (issued_at)"))
    _mark_migration(conn, name)
    applied.append(name)


def _create_notification_logs(conn, applied: list[str]) -> None:
    name = "notification_logs.create_table_v2"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS notification_logs (
            id                      VARCHAR(36)  PRIMARY KEY,

            -- Referências
            order_id                VARCHAR(36)  REFERENCES orders(id),
            pickup_id               VARCHAR(36)  REFERENCES pickups(id),
            delivery_id             VARCHAR(36)  REFERENCES inbound_deliveries(id),
            rental_id               VARCHAR(36)  REFERENCES rental_contracts(id),

            -- EMAIL | SMS | WHATSAPP | PUSH | WEBHOOK
            channel                 VARCHAR(20)  NOT NULL,
            template_key            VARCHAR(100) NOT NULL,
            destination_value       VARCHAR(255),
            locale                  VARCHAR(10)  NOT NULL DEFAULT 'pt-BR',

            -- Deduplicação: hash do (channel + template + destino + conteúdo chave)
            dedupe_key              VARCHAR(255) NOT NULL UNIQUE,

            -- Payload enviado
            payload_json            TEXT,

            -- QUEUED | PROCESSING | SENT | FAILED | SKIPPED | BOUNCED
            status                  VARCHAR(20)  NOT NULL DEFAULT 'QUEUED',

            attempt_count           INTEGER      NOT NULL DEFAULT 0,
            max_attempts            INTEGER      NOT NULL DEFAULT 3,
            processing_started_at   TIMESTAMPTZ,
            last_attempt_at         TIMESTAMPTZ,
            next_attempt_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            sent_at                 TIMESTAMPTZ,

            -- Resposta do provider
            provider_message_id     VARCHAR(255),
            provider_status         VARCHAR(50),
            error_detail            TEXT,

            created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notif_status_next    ON notification_logs (status, next_attempt_at) WHERE status IN ('QUEUED', 'FAILED')"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notif_order          ON notification_logs (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notif_pickup         ON notification_logs (pickup_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notif_delivery       ON notification_logs (delivery_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_notif_next_attempt   ON notification_logs (next_attempt_at)"))
    _mark_migration(conn, name)
    applied.append(name)


# ---------------------------------------------------------------------------
# ══════════════════════════════════════════════════════════════════════════
# BLOCO 10 — Outbox (Event-Driven / Saga)
# ══════════════════════════════════════════════════════════════════════════
# ---------------------------------------------------------------------------

def _create_domain_event_outbox(conn, applied: list[str]) -> None:
    name = "domain_event_outbox.create_table_v2"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS domain_event_outbox (
            id              VARCHAR(36)  PRIMARY KEY,
            event_key       VARCHAR(255) NOT NULL,
            aggregate_type  VARCHAR(100),
            aggregate_id    VARCHAR(100),
            event_name      VARCHAR(100),
            event_version   INTEGER      NOT NULL DEFAULT 1,
            -- PENDING | PUBLISHED | FAILED | DEAD
            status          VARCHAR(20)  NOT NULL DEFAULT 'PENDING',
            payload_json    TEXT,
            occurred_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            published_at    TIMESTAMPTZ,
            attempt_count   INTEGER      NOT NULL DEFAULT 0,
            last_error      TEXT,
            created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_outbox_status_occurred ON domain_event_outbox (status, occurred_at) WHERE status = 'PENDING'"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_outbox_aggregate        ON domain_event_outbox (aggregate_type, aggregate_id)"))
    _mark_migration(conn, name)
    applied.append(name)


def _create_reconciliation_pending(conn, applied: list[str]) -> None:
    name = "reconciliation_pending.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS reconciliation_pending (
            id                      VARCHAR(40) PRIMARY KEY,
            dedupe_key              VARCHAR(180) NOT NULL,
            order_id                VARCHAR(36) NOT NULL REFERENCES orders(id),
            reason                  VARCHAR(80) NOT NULL,
            status                  VARCHAR(24) NOT NULL DEFAULT 'PENDING',
            payload_json            TEXT,
            attempt_count           INTEGER NOT NULL DEFAULT 0,
            max_attempts            INTEGER NOT NULL DEFAULT 5,
            next_retry_at           TIMESTAMPTZ,
            processing_started_at   TIMESTAMPTZ,
            last_error              TEXT,
            completed_at            TIMESTAMPTZ,
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
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
    conn.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_recon_pending_dedupe "
            "ON reconciliation_pending (dedupe_key)"
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_recon_pending_status_next "
            "ON reconciliation_pending (status, next_retry_at)"
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_recon_pending_order_id "
            "ON reconciliation_pending (order_id)"
        )
    )
    _mark_migration(conn, name)
    applied.append(name)


def _create_ops_action_audit(conn, applied: list[str]) -> None:
    name = "ops_action_audit.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ops_action_audit (
            id              VARCHAR(40) PRIMARY KEY,
            action          VARCHAR(120) NOT NULL,
            result          VARCHAR(20) NOT NULL,
            correlation_id  VARCHAR(80) NOT NULL,
            user_id         VARCHAR(36),
            role            VARCHAR(80),
            order_id        VARCHAR(36),
            error_message   TEXT,
            details_json    TEXT,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_ops_audit_created_at "
            "ON ops_action_audit (created_at)"
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_ops_audit_order_id "
            "ON ops_action_audit (order_id)"
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_ops_audit_action_result "
            "ON ops_action_audit (action, result)"
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_ops_audit_corr_id "
            "ON ops_action_audit (correlation_id)"
        )
    )
    _mark_migration(conn, name)
    applied.append(name)


# ---------------------------------------------------------------------------
# ══════════════════════════════════════════════════════════════════════════
# BLOCO 11 — LGPD / GDPR
# ══════════════════════════════════════════════════════════════════════════
# ---------------------------------------------------------------------------

def _create_privacy_consents(conn, applied: list[str]) -> None:
    name = "privacy_consents.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS privacy_consents (
            id                  VARCHAR(36)  PRIMARY KEY,
            -- Usuário identificado ou identificador de guest/sessão
            user_id             VARCHAR(36)  REFERENCES users(id),
            guest_identifier    VARCHAR(255),
            -- MARKETING | ANALYTICS | THIRD_PARTY | ESSENTIAL
            consent_type        VARCHAR(50)  NOT NULL,
            granted             BOOLEAN      NOT NULL,
            -- Onde foi coletado
            channel             VARCHAR(20),
            ip_address          VARCHAR(64),
            user_agent          VARCHAR(500),
            -- Versão da política aceita
            policy_version      VARCHAR(20),
            -- Linha do tempo
            granted_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            revoked_at          TIMESTAMPTZ,
            created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_consents_user       ON privacy_consents (user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_consents_guest      ON privacy_consents (guest_identifier)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_consents_type       ON privacy_consents (consent_type)"))
    _mark_migration(conn, name)
    applied.append(name)


def _create_data_deletion_requests(conn, applied: list[str]) -> None:
    name = "data_deletion_requests.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS data_deletion_requests (
            id              VARCHAR(36)  PRIMARY KEY,
            user_id         VARCHAR(36)  REFERENCES users(id),
            requested_by    VARCHAR(255),  -- email ou ID do solicitante
            -- PENDING | IN_PROGRESS | COMPLETED | REJECTED
            status          VARCHAR(20)  NOT NULL DEFAULT 'PENDING',
            -- Motivo da solicitação (por boa prática LGPD)
            reason          VARCHAR(255),
            -- Se rejeitado, motivo legal (ex: obrigação fiscal)
            rejection_reason TEXT,
            requested_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            completed_at    TIMESTAMPTZ,
            notes           TEXT,
            created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_deletion_req_user   ON data_deletion_requests (user_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_deletion_req_status ON data_deletion_requests (status)"))
    _mark_migration(conn, name)
    applied.append(name)


# ---------------------------------------------------------------------------
# ══════════════════════════════════════════════════════════════════════════
# BLOCO 12 — Capability Catalog (Payment / Channel / Context)
#
# Propósito: base canônica de configuração de capacidades por região,
# canal e contexto. Substitui enums gigantes, mapas hardcoded no router,
# paymentProfile.js, validação paralela no public_orders.py e
# lógica local no RegionPage.jsx.
#
# Princípio:
#   PostgreSQL  = verdade do catálogo operacional
#   backend     = interpreta e expõe
#   frontend    = consome
#   KIOSK       = recebe snapshot resolvida, não consulta essas tabelas
#
# Ordem de criação (respeita FKs):
#   1.  capability_region
#   2.  capability_channel
#   3.  capability_context
#   4.  payment_method_catalog
#   5.  payment_interface_catalog
#   6.  wallet_provider_catalog
#   7.  capability_profile
#   8.  capability_profile_method
#   9.  capability_profile_method_interface
#   10. capability_requirement_catalog
#   11. capability_profile_method_requirement
#   12. capability_profile_action
#   13. capability_profile_constraint
#   14. capability_profile_target
#   15. capability_profile_snapshot   ← novo: snapshot resolvida para KIOSK
# ══════════════════════════════════════════════════════════════════════════
# ---------------------------------------------------------------------------


def _create_capability_region(conn, applied: list[str]) -> None:
    """
    Regiões de negócio configuráveis.
    Evita ENUM de banco — regiões crescem sem migration estrutural.
    Exemplos de code: SP, RJ, PT, CN, JP, AE, UK, AR
    """
    name = "capability_region.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS capability_region (
            id               BIGSERIAL    PRIMARY KEY,
            code             VARCHAR(20)  NOT NULL UNIQUE,
            name             VARCHAR(120) NOT NULL,
            country_code     VARCHAR(10),           -- ISO 3166-1 alpha-2: BR, PT, CN...
            continent        VARCHAR(60),
            -- Moeda padrão desta região (ISO 4217)
            default_currency VARCHAR(10)  NOT NULL,
            -- Fuso horário padrão da região
            default_timezone VARCHAR(50)  NOT NULL DEFAULT 'America/Sao_Paulo',
            -- Locale padrão para comunicações
            default_locale   VARCHAR(10)  NOT NULL DEFAULT 'pt-BR',
            is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
            metadata_json    JSONB        NOT NULL DEFAULT '{}'::JSONB,
            created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cap_region_country ON capability_region (country_code)"))
    _mark_migration(conn, name)
    applied.append(name)


def _create_capability_channel(conn, applied: list[str]) -> None:
    """
    Canal macro de operação.
    Exemplos: online, kiosk, api, partner, staff
    """
    name = "capability_channel.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS capability_channel (
            id          BIGSERIAL    PRIMARY KEY,
            code        VARCHAR(50)  NOT NULL UNIQUE,
            name        VARCHAR(120) NOT NULL,
            description TEXT,
            is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    _mark_migration(conn, name)
    applied.append(name)

    # Seed dos canais base (idempotente)
    conn.execute(text("""
        INSERT INTO capability_channel (code, name) VALUES
            ('online',  'Online / Web / App'),
            ('kiosk',   'KIOSK / Totem físico'),
            ('api',     'API direta (parceiros B2B)'),
            ('partner', 'Parceiro integrado'),
            ('staff',   'Operação manual por staff')
        ON CONFLICT (code) DO NOTHING
    """))


def _create_capability_context(conn, applied: list[str]) -> None:
    """
    Contexto operacional dentro de um canal.

    NOTA DE DESIGN: contextos são channel-scoped intencionalmente.
    'pickup' no kiosk e 'pickup' no online têm fluxos distintos.
    O UNIQUE (channel_id, code) garante que o mesmo código semântico
    pode existir em canais diferentes sem colisão.

    Exemplos:
      kiosk  + purchase           → compra presencial com pagamento
      kiosk  + pickup             → retirada de pedido online
      kiosk  + operator_pickup    → retirada assistida por operador
      kiosk  + logistics_handover → entrega de parceiro logístico
      kiosk  + return_dropoff     → devolução de item
      online + checkout           → compra web/app com pagamento
      online + pickup_schedule    → agendamento de retirada
    """
    name = "capability_context.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS capability_context (
            id          BIGSERIAL    PRIMARY KEY,
            channel_id  BIGINT       NOT NULL REFERENCES capability_channel(id),
            code        VARCHAR(80)  NOT NULL,
            name        VARCHAR(120) NOT NULL,
            description TEXT,
            is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            UNIQUE (channel_id, code)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cap_context_channel ON capability_context (channel_id)"))
    _mark_migration(conn, name)
    applied.append(name)


def _create_payment_method_catalog(conn, applied: list[str]) -> None:
    """
    Catálogo global de métodos de pagamento.
    Exemplos: pix, creditCard, debitCard, mbway, alipay, wechat_pay,
              konbini, m_pesa, boleto, voucher, cash, bnpl_tabby
    """
    name = "payment_method_catalog.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payment_method_catalog (
            id                BIGSERIAL    PRIMARY KEY,
            code              VARCHAR(80)  NOT NULL UNIQUE,
            name              VARCHAR(120) NOT NULL,
            -- Família de agrupamento para UI: card | digital_wallet | bank_transfer |
            --   cash | bnpl | voucher | crypto | mobile_money
            family            VARCHAR(80),
            -- Flags de classificação (consultáveis sem parsear JSON)
            is_wallet         BOOLEAN      NOT NULL DEFAULT FALSE,
            is_card           BOOLEAN      NOT NULL DEFAULT FALSE,
            is_bnpl           BOOLEAN      NOT NULL DEFAULT FALSE,
            is_cash_like      BOOLEAN      NOT NULL DEFAULT FALSE,
            is_bank_transfer  BOOLEAN      NOT NULL DEFAULT FALSE,
            is_instant        BOOLEAN      NOT NULL DEFAULT FALSE,  -- PIX, MB Way
            requires_redirect BOOLEAN      NOT NULL DEFAULT FALSE,  -- 3DS, bank_link
            -- Campos extras livres
            metadata_json     JSONB        NOT NULL DEFAULT '{}'::JSONB,
            is_active         BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pmc_family ON payment_method_catalog (family)"))

    # Seed de métodos comuns (idempotente)
    conn.execute(text("""
        INSERT INTO payment_method_catalog
            (code, name, family, is_instant, is_bank_transfer, is_card, is_wallet, is_cash_like)
        VALUES
            ('pix',           'PIX',              'bank_transfer',  TRUE,  TRUE,  FALSE, FALSE, FALSE),
            ('creditCard',    'Cartão de Crédito', 'card',          FALSE, FALSE, TRUE,  FALSE, FALSE),
            ('debitCard',     'Cartão de Débito',  'card',          FALSE, FALSE, TRUE,  FALSE, FALSE),
            ('boleto',        'Boleto Bancário',   'bank_transfer',  FALSE, TRUE,  FALSE, FALSE, FALSE),
            ('cash',          'Dinheiro',           'cash',          FALSE, FALSE, FALSE, FALSE, TRUE),
            ('voucher',       'Voucher',            'voucher',       FALSE, FALSE, FALSE, FALSE, FALSE),
            ('mbway',         'MB Way',             'digital_wallet', TRUE, FALSE, FALSE, TRUE,  FALSE),
            ('alipay',        'Alipay',             'digital_wallet', FALSE,FALSE, FALSE, TRUE,  FALSE),
            ('wechat_pay',    'WeChat Pay',         'digital_wallet', FALSE,FALSE, FALSE, TRUE,  FALSE),
            ('apple_pay',     'Apple Pay',          'digital_wallet', FALSE,FALSE, TRUE,  TRUE,  FALSE),
            ('google_pay',    'Google Pay',         'digital_wallet', FALSE,FALSE, TRUE,  TRUE,  FALSE),
            ('mercado_pago',  'Mercado Pago',       'digital_wallet', FALSE,FALSE, FALSE, TRUE,  FALSE),
            ('konbini',       'Konbini',            'cash',           FALSE,FALSE, FALSE, FALSE, TRUE),
            ('m_pesa',        'M-Pesa',             'mobile_money',   FALSE,FALSE, FALSE, TRUE,  FALSE),
            ('tabby',         'Tabby (BNPL)',        'bnpl',           FALSE,FALSE, FALSE, FALSE, FALSE)
        ON CONFLICT (code) DO NOTHING
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_payment_interface_catalog(conn, applied: list[str]) -> None:
    """
    Catálogo global de interfaces de interação com o método de pagamento.
    Exemplos: qr_code, chip, nfc, deep_link, web_token, manual, ussd,
              barcode, bank_link, kiosk_pinpad
    """
    name = "payment_interface_catalog.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payment_interface_catalog (
            id              BIGSERIAL    PRIMARY KEY,
            code            VARCHAR(80)  NOT NULL UNIQUE,
            name            VARCHAR(120) NOT NULL,
            -- physical | digital | hybrid
            interface_type  VARCHAR(60),
            -- Requer hardware físico no terminal?
            requires_hw     BOOLEAN      NOT NULL DEFAULT FALSE,
            metadata_json   JSONB        NOT NULL DEFAULT '{}'::JSONB,
            is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))

    conn.execute(text("""
        INSERT INTO payment_interface_catalog (code, name, interface_type, requires_hw) VALUES
            ('qr_code',       'QR Code',            'digital',  FALSE),
            ('chip',          'Chip (EMV)',           'physical', TRUE),
            ('nfc',           'NFC / Contactless',   'physical', TRUE),
            ('magnetic',      'Trato magnético',     'physical', TRUE),
            ('deep_link',     'Deep Link (App)',      'digital',  FALSE),
            ('web_token',     'Token Web',           'digital',  FALSE),
            ('manual',        'Digitação manual',    'physical', FALSE),
            ('ussd',          'USSD',                'digital',  FALSE),
            ('barcode',       'Código de barras',    'physical', FALSE),
            ('bank_link',     'Internet Banking',    'digital',  FALSE),
            ('kiosk_pinpad',  'PinPad no KIOSK',    'physical', TRUE)
        ON CONFLICT (code) DO NOTHING
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_wallet_provider_catalog(conn, applied: list[str]) -> None:
    """
    Catálogo global de wallet providers.
    Separado de payment_method para suportar casos onde o método é
    'wallet' mas o provider varia (Apple Pay vs Google Pay no mesmo checkout).
    """
    name = "wallet_provider_catalog.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS wallet_provider_catalog (
            id            BIGSERIAL    PRIMARY KEY,
            code          VARCHAR(80)  NOT NULL UNIQUE,
            name          VARCHAR(120) NOT NULL,
            metadata_json JSONB        NOT NULL DEFAULT '{}'::JSONB,
            is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))

    conn.execute(text("""
        INSERT INTO wallet_provider_catalog (code, name) VALUES
            ('applePay',     'Apple Pay'),
            ('googlePay',    'Google Pay'),
            ('mercadoPago',  'Mercado Pago'),
            ('wechatPay',    'WeChat Pay'),
            ('alipay',       'Alipay'),
            ('mPesa',        'M-Pesa'),
            ('tabby',        'Tabby'),
            ('mbway',        'MB Way'),
            ('picpay',       'PicPay'),
            ('pagseguro',    'PagSeguro')
        ON CONFLICT (code) DO NOTHING
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_capability_requirement_catalog(conn, applied: list[str]) -> None:
    """
    Catálogo dos requisitos possíveis para um método de pagamento.
    Evita que requisitos fiquem apenas em JSON opaco.
    Exemplos: amount_cents, customer_phone, national_id, wallet_provider,
              qr_code_content, device_id, ip_address
    """
    name = "capability_requirement_catalog.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS capability_requirement_catalog (
            id          BIGSERIAL    PRIMARY KEY,
            code        VARCHAR(100) NOT NULL UNIQUE,
            name        VARCHAR(120) NOT NULL,
            -- string | integer | boolean | enum | phone | email | document_id | any_of
            data_type   VARCHAR(40)  NOT NULL,
            description TEXT,
            is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))

    conn.execute(text("""
        INSERT INTO capability_requirement_catalog (code, name, data_type) VALUES
            ('amount_cents',                  'Valor em centavos',          'integer'),
            ('customer_phone',                'Telefone do cliente',         'phone'),
            ('customer_email',                'E-mail do cliente',           'email'),
            ('customer_phone_or_email',       'Telefone OU e-mail',          'any_of'),
            ('wallet_provider',               'Provider da wallet',          'enum'),
            ('qr_code_content',               'Conteúdo do QR Code',         'string'),
            ('konbini_code',                  'Código Konbini',              'string'),
            ('ussd_session_id',               'ID de sessão USSD',           'string'),
            ('national_id',                   'Documento de identidade',     'document_id'),
            ('turkish_id',                    'TC Kimlik No (Turquia)',       'string'),
            ('device_id',                     'ID do dispositivo',           'string'),
            ('ip_address',                    'Endereço IP do cliente',      'string'),
            ('installments',                  'Número de parcelas',          'integer'),
            ('card_token',                    'Token do cartão',             'string'),
            ('billing_address',               'Endereço de cobrança',        'string'),
            ('age_confirmation',              'Confirmação de maioridade',   'boolean')
        ON CONFLICT (code) DO NOTHING
    """))

    _mark_migration(conn, name)
    applied.append(name)


def _create_capability_profile(conn, applied: list[str]) -> None:
    """
    Combinação canônica de (região, canal, contexto).
    É o ponto central de toda a árvore de capabilities.

    Exemplos de profile_code (gerado, não editável):
      SP:kiosk:purchase
      SP:kiosk:pickup
      SP:online:checkout
      PT:online:checkout
      CN:kiosk:purchase

    valid_from / valid_until permitem transições de perfil sem janela
    de manutenção — pedidos em andamento continuam no perfil antigo.
    """
    name = "capability_profile.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS capability_profile (
            id           BIGSERIAL    PRIMARY KEY,
            region_id    BIGINT       NOT NULL REFERENCES capability_region(id),
            channel_id   BIGINT       NOT NULL REFERENCES capability_channel(id),
            context_id   BIGINT       NOT NULL REFERENCES capability_context(id),

            -- Gerado pelo backend: '<region_code>:<channel_code>:<context_code>'
            -- Imutável após criação — usado como referência externa estável
            profile_code VARCHAR(160) NOT NULL UNIQUE,

            name         VARCHAR(180) NOT NULL,

            -- Prioridade de resolução quando múltiplos perfis se aplicam
            priority     INTEGER      NOT NULL DEFAULT 100,

            -- Moeda padrão deste perfil (pode divergir da região, ex: duty-free)
            currency     VARCHAR(10)  NOT NULL,

            -- Vigência — permite transições sem janela de manutenção
            valid_from   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            valid_until  TIMESTAMPTZ,             -- NULL = vigente indefinidamente

            is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
            metadata_json JSONB       NOT NULL DEFAULT '{}'::JSONB,

            created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

            UNIQUE (region_id, channel_id, context_id)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cap_profile_region  ON capability_profile (region_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cap_profile_channel ON capability_profile (channel_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cap_profile_active  ON capability_profile (is_active, valid_from, valid_until)"))
    _mark_migration(conn, name)
    applied.append(name)


def _create_capability_profile_method(conn, applied: list[str]) -> None:
    """
    Métodos de pagamento permitidos dentro de um perfil.
    Tabela central do catálogo de pagamentos.

    Campos financeiros críticos são colunas explícitas (não JSON)
    para permitir índices, validação e queries diretas.
    """
    name = "capability_profile_method.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS capability_profile_method (
            id                  BIGSERIAL    PRIMARY KEY,
            profile_id          BIGINT       NOT NULL REFERENCES capability_profile(id) ON DELETE CASCADE,
            payment_method_id   BIGINT       NOT NULL REFERENCES payment_method_catalog(id),

            label               VARCHAR(120),    -- label localizado para UI
            sort_order          INTEGER      NOT NULL DEFAULT 100,
            is_default          BOOLEAN      NOT NULL DEFAULT FALSE,
            is_active           BOOLEAN      NOT NULL DEFAULT TRUE,

            -- Wallet provider quando aplicável (Apple Pay, Google Pay, etc.)
            wallet_provider_id  BIGINT       REFERENCES wallet_provider_catalog(id),

            -- Limites financeiros — colunas explícitas (não enterrar em JSON)
            min_amount_cents    INTEGER,
            max_amount_cents    INTEGER,
            max_installments    INTEGER      NOT NULL DEFAULT 1,

            -- Exige pre-autorização antes de exibir?
            requires_preauth    BOOLEAN      NOT NULL DEFAULT FALSE,

            -- Configurações extras que não cabem como coluna
            rules_json          JSONB        NOT NULL DEFAULT '{}'::JSONB,

            created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

            UNIQUE (profile_id, payment_method_id)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cpm_profile  ON capability_profile_method (profile_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cpm_method   ON capability_profile_method (payment_method_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_cpm_active   ON capability_profile_method (profile_id, is_active)"))
    _mark_migration(conn, name)
    applied.append(name)


def _create_capability_profile_method_interface(conn, applied: list[str]) -> None:
    """
    Interfaces válidas para um método dentro de um perfil.

    Exemplos:
      pix        em SP:kiosk:purchase  → qr_code
      creditCard em SP:kiosk:purchase  → chip, nfc, manual, kiosk_pinpad
      mbway      em PT:online:checkout → qr_code, web_token, deep_link
    """
    name = "capability_profile_method_interface.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS capability_profile_method_interface (
            id                   BIGSERIAL    PRIMARY KEY,
            profile_method_id    BIGINT       NOT NULL REFERENCES capability_profile_method(id) ON DELETE CASCADE,
            payment_interface_id BIGINT       NOT NULL REFERENCES payment_interface_catalog(id),
            sort_order           INTEGER      NOT NULL DEFAULT 100,
            is_default           BOOLEAN      NOT NULL DEFAULT FALSE,
            is_active            BOOLEAN      NOT NULL DEFAULT TRUE,
            config_json          JSONB        NOT NULL DEFAULT '{}'::JSONB,
            created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            UNIQUE (profile_method_id, payment_interface_id)
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_cpmi_method ON capability_profile_method_interface (profile_method_id)"
    ))
    _mark_migration(conn, name)
    applied.append(name)


def _create_capability_profile_method_requirement(conn, applied: list[str]) -> None:
    """
    Requisitos de dados para um método dentro de um perfil.
    Evita transformar tudo em JSON opaco e permite validação server-side
    sem lógica hardcoded.

    requirement_scope:
      request   → enviado na requisição de pagamento
      session   → disponível na sessão (já coletado antes)
      hardware  → depende do hardware do terminal
    """
    name = "capability_profile_method_requirement.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS capability_profile_method_requirement (
            id                  BIGSERIAL    PRIMARY KEY,
            profile_method_id   BIGINT       NOT NULL REFERENCES capability_profile_method(id) ON DELETE CASCADE,
            requirement_id      BIGINT       NOT NULL REFERENCES capability_requirement_catalog(id),
            is_required         BOOLEAN      NOT NULL DEFAULT TRUE,
            -- request | session | hardware
            requirement_scope   VARCHAR(40)  NOT NULL DEFAULT 'request',
            -- Regras de validação (ex: min/max length, regex, allowed values)
            validation_json     JSONB        NOT NULL DEFAULT '{}'::JSONB,
            created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            UNIQUE (profile_method_id, requirement_id)
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_cpmr_method ON capability_profile_method_requirement (profile_method_id)"
    ))
    _mark_migration(conn, name)
    applied.append(name)


def _create_capability_profile_action(conn, applied: list[str]) -> None:
    """
    Ações operacionais que o KIOSK/frontend deve expor em cada perfil.
    Não todo contexto é 'pagar' — pickup, returns e staff têm fluxos próprios.

    Exemplos:
      create_order        → iniciar pedido
      start_payment       → iniciar cobrança
      identify_customer   → verificar identidade
      enter_pickup_code   → digitar código de retirada
      scan_pickup_qr      → escanear QR de retirada
      operator_release    → liberação manual por operador
      open_empty_slot     → abrir gaveta vazia (manutenção)
      return_item         → iniciar devolução

    action_type categoriza a ação para o engine de comportamento:
      PAYMENT | NAVIGATION | HARDWARE | IDENTIFICATION | OPERATION
    """
    name = "capability_profile_action.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS capability_profile_action (
            id           BIGSERIAL    PRIMARY KEY,
            profile_id   BIGINT       NOT NULL REFERENCES capability_profile(id) ON DELETE CASCADE,
            action_code  VARCHAR(80)  NOT NULL,
            label        VARCHAR(120) NOT NULL,
            -- PAYMENT | NAVIGATION | HARDWARE | IDENTIFICATION | OPERATION
            action_type  VARCHAR(40)  NOT NULL DEFAULT 'OPERATION',
            sort_order   INTEGER      NOT NULL DEFAULT 100,
            is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
            -- Pré-condição para exibir a ação (ex: {"requires_auth": true})
            precondition_json JSONB   NOT NULL DEFAULT '{}'::JSONB,
            -- Config de UX (ícone, cor, timeout de tela)
            config_json  JSONB        NOT NULL DEFAULT '{}'::JSONB,
            created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            UNIQUE (profile_id, action_code)
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_cpa_profile ON capability_profile_action (profile_id, is_active)"
    ))
    _mark_migration(conn, name)
    applied.append(name)


def _create_capability_profile_constraint(conn, applied: list[str]) -> None:
    """
    Constraints contextuais do perfil — regras de negócio que variam
    por região/canal/contexto e não pertencem ao método de pagamento.

    Exemplos de code:
      pickup_window_sec           → janela máxima de retirada em segundos
      prepayment_timeout_sec      → timeout de pagamento no KIOSK
      alloc_ttl_sec               → TTL da alocação de slot
      max_amount_cents            → limite de valor por transação
      min_amount_cents            → valor mínimo por transação
      requires_identity_validation → validação de CPF/ID obrigatória
      max_active_orders_per_user  → limite de pedidos simultâneos
      allow_guest_checkout        → permite checkout sem cadastro
    """
    name = "capability_profile_constraint.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS capability_profile_constraint (
            id          BIGSERIAL    PRIMARY KEY,
            profile_id  BIGINT       NOT NULL REFERENCES capability_profile(id) ON DELETE CASCADE,
            code        VARCHAR(100) NOT NULL,
            -- Valor como JSONB para suportar scalar, array e objeto
            value_json  JSONB        NOT NULL,
            description TEXT,
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            UNIQUE (profile_id, code)
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_cpconstraint_profile ON capability_profile_constraint (profile_id)"
    ))
    _mark_migration(conn, name)
    applied.append(name)


def _create_capability_profile_target(conn, applied: list[str]) -> None:
    """
    Override de perfil por entidade específica (tenant, operador, site,
    locker, modelo de hardware). Permite comportamento diferenciado sem
    criar um perfil inteiramente novo.

    target_type: TENANT | OPERATOR | SITE | LOCKER | LOCKER_MODEL | PARTNER

    locker_id é coluna explícita (FK) para o caso mais comum de override
    por locker físico. Os demais casos usam target_type + target_key.

    Estratégia de resolução (no backend):
      1. Busca perfil por (region, channel, context, locker_id)
      2. Fallback para (region, channel, context, operator_id)
      3. Fallback para (region, channel, context) — perfil base
    """
    name = "capability_profile_target.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS capability_profile_target (
            id            BIGSERIAL    PRIMARY KEY,
            profile_id    BIGINT       NOT NULL REFERENCES capability_profile(id) ON DELETE CASCADE,
            -- TENANT | OPERATOR | SITE | LOCKER | LOCKER_MODEL | PARTNER
            target_type   VARCHAR(40)  NOT NULL,
            -- Chave do alvo (ID do tenant, código do operador, etc.)
            target_key    VARCHAR(120) NOT NULL,
            -- FK explícita para locker (caso mais comum de override)
            locker_id     VARCHAR(36)  REFERENCES lockers(id),
            is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
            metadata_json JSONB        NOT NULL DEFAULT '{}'::JSONB,
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            UNIQUE (profile_id, target_type, target_key)
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_cpt_target     ON capability_profile_target (target_type, target_key)"
    ))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_cpt_locker_id  ON capability_profile_target (locker_id)"
    ))
    _mark_migration(conn, name)
    applied.append(name)


def _create_capability_profile_snapshot(conn, applied: list[str]) -> None:
    """
    Snapshot resolvida e desnormalizada do perfil — para o KIOSK.

    O KIOSK NÃO deve consultar as tabelas capability_* em runtime.
    O backend resolve o perfil completo e publica um snapshot JSON
    que o KIOSK consome offline. Isso garante operação mesmo sem
    conectividade com o PostgreSQL principal.

    Fluxo:
      1. Backoffice edita tabelas capability_*
      2. Evento dispara resolução do perfil
      3. Backend serializa perfil resolvido em resolved_json
      4. KIOSK faz pull periódico deste snapshot
      5. KIOSK usa snapshot localmente — sem queries ao Postgres

    snapshot_hash permite ao KIOSK detectar mudanças sem baixar o payload.
    """
    name = "capability_profile_snapshot.create_table_v1"
    if _migration_applied(conn, name):
        return
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS capability_profile_snapshot (
            id              BIGSERIAL    PRIMARY KEY,
            profile_id      BIGINT       NOT NULL REFERENCES capability_profile(id),
            profile_code    VARCHAR(160) NOT NULL,
            -- Locker-specific ou NULL (snapshot global do perfil)
            locker_id       VARCHAR(36)  REFERENCES lockers(id),
            -- JSON resolvido e desnormalizado — o que o KIOSK lê
            resolved_json   JSONB        NOT NULL,
            -- SHA-256 do resolved_json para detecção de mudança
            snapshot_hash   VARCHAR(64)  NOT NULL,
            -- Versão incremental para ordenação
            version         INTEGER      NOT NULL DEFAULT 1,
            -- DRAFT | PUBLISHED | SUPERSEDED
            status          VARCHAR(20)  NOT NULL DEFAULT 'DRAFT',
            published_at    TIMESTAMPTZ,
            superseded_at   TIMESTAMPTZ,
            generated_by    VARCHAR(100),  -- serviço/job que gerou
            created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_cap_snapshot_profile_status "
        "ON capability_profile_snapshot (profile_id, status)"
    ))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_cap_snapshot_locker "
        "ON capability_profile_snapshot (locker_id, status)"
    ))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_cap_snapshot_code_status "
        "ON capability_profile_snapshot (profile_code, status)"
    ))
    _mark_migration(conn, name)
    applied.append(name)


# ---------------------------------------------------------------------------
# Sequência do Bloco 12 — para incluir em _POSTGRES_MIGRATION_STEPS
# ---------------------------------------------------------------------------
#
# Adicione estas entradas ao final de _POSTGRES_MIGRATION_STEPS no arquivo
# principal, após _create_data_deletion_requests:
#
#     _create_capability_region,
#     _create_capability_channel,
#     _create_capability_context,
#     _create_payment_method_catalog,
#     _create_payment_interface_catalog,
#     _create_wallet_provider_catalog,
#     _create_capability_requirement_catalog,
#     _create_capability_profile,
#     _create_capability_profile_method,
#     _create_capability_profile_method_interface,
#     _create_capability_profile_method_requirement,
#     _create_capability_profile_action,
#     _create_capability_profile_constraint,
#     _create_capability_profile_target,
#     _create_capability_profile_snapshot,
#
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# ══════════════════════════════════════════════════════════════════════════
# BLOCO LEGACY — SQLite (apenas para ambiente KIOSK offline)
# NOTA: este bloco existe exclusivamente para manter o KIOSK operacional
# quando não houver conectividade com o PostgreSQL principal.
# Um serviço de replicação externo (a implementar) sincronizará os dados
# para o PostgreSQL ao restabelecer a conexão.
# Não adicionar novos schemas neste bloco — evoluir apenas o Postgres.
# ══════════════════════════════════════════════════════════════════════════
# ---------------------------------------------------------------------------

def _kiosk_sqlite_ensure_core_tables(conn, applied: list[str]) -> None:
    """
    Garante as tabelas mínimas para operação KIOSK offline em SQLite.
    Schema propositalmente simplificado — apenas o essencial para:
      - registrar pedidos
      - registrar pagamentos
      - emitir tokens de retirada
      - registrar pickups
    Tudo mais será sincronizado pelo serviço de replicação.
    """
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
            synced_at       TIMESTAMP,   -- preenchido pelo serviço de replicação
            created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))

    # payment_transactions (simplificado)
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

    # outbox para replicação assíncrona
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sync_outbox (
            id              TEXT PRIMARY KEY,
            table_name      TEXT NOT NULL,
            record_id       TEXT NOT NULL,
            operation       TEXT NOT NULL,  -- INSERT | UPDATE | DELETE
            payload_json    TEXT,
            synced_at       TIMESTAMP,
            created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """))

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

    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_kiosk_orders_status   ON orders (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_kiosk_pickups_status  ON pickups (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_kiosk_sync_pending    ON sync_outbox (synced_at) WHERE synced_at IS NULL"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_recon_pending_dedupe ON reconciliation_pending (dedupe_key)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_recon_pending_status_next ON reconciliation_pending (status, next_retry_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ops_audit_created_at ON ops_action_audit (created_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ops_audit_order_id ON ops_action_audit (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_ops_audit_action_result ON ops_action_audit (action, result)"))

    applied.append("kiosk_sqlite.core_tables")


# ---------------------------------------------------------------------------
# ══════════════════════════════════════════════════════════════════════════
# ENTRY POINTS PRINCIPAIS
# ══════════════════════════════════════════════════════════════════════════
# ---------------------------------------------------------------------------

# Sequência canônica de criação para PostgreSQL.
# A ordem respeita todas as FKs.
_POSTGRES_MIGRATION_STEPS = [
    _create_users,
    _create_auth_sessions,
    _create_locker_operators,
    _create_lockers,
    _create_tenant_fiscal_config,
    _create_locker_slot_configs,
    _create_locker_slots,
    _create_locker_telemetry,
    _create_product_categories,
    _create_product_locker_configs,
    _create_rental_plans,
    _create_rental_contracts,
    _create_logistics_partners,
    _create_ecommerce_partners,
    _create_webhook_endpoints,
    _create_webhook_deliveries,
    _create_orders,
    _create_payment_transactions,
    _create_allocations,
    _create_pickups,
    _create_pickup_tokens,
    _create_inbound_deliveries,
    _create_fiscal_documents,
    _create_notification_logs,
    _create_domain_event_outbox,
    _create_reconciliation_pending,
    _create_ops_action_audit,
    _create_privacy_consents,
    _create_data_deletion_requests,

    # BLOCO 12
    _create_capability_region,
    _create_capability_channel,
    _create_capability_context,
    _create_payment_method_catalog,
    _create_payment_interface_catalog,
    _create_wallet_provider_catalog,
    _create_capability_requirement_catalog,
    _create_capability_profile,
    _create_capability_profile_method,
    _create_capability_profile_method_interface,
    _create_capability_profile_method_requirement,
    _create_capability_profile_action,
    _create_capability_profile_constraint,
    _create_capability_profile_target,
    _create_capability_profile_snapshot,

]


def run_migrations(conn) -> list[str]:
    applied: list[str] = []
    dialect = conn.dialect.name

    if dialect == "postgresql":
        _ensure_schema_migrations(conn)
        _auto_heal_legacy_schema(conn, applied)

        for step in _POSTGRES_MIGRATION_STEPS:
            try:
                step(conn, applied)
            except Exception as exc:
                logger.error("Migration falhou em %s: %s", step.__name__, exc)
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
        return {"ok": False, "error": str(exc), "applied": []}


def _run_startup_migrations_if_enabled():
    """
    Wrapper de startup — mantido para compatibilidade com chamadas existentes.
    """
    return migrate_order_pickup_schema()



# ENGINE DE AUTO-CORREÇÃO
def _ensure_columns(conn, table: str, columns: dict[str, str]) -> None:
    """
    Garante que colunas existam na tabela.
    columns = { "coluna": "TIPO SQL" }
    """
    inspector = inspect(conn)

    existing = {col["name"] for col in inspector.get_columns(table)}

    for col, ddl in columns.items():
        if col not in existing:
            logger.warning(f"[AUTO-MIGRATE] adicionando coluna {table}.{col}")
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))


def _ensure_locker_operators_columns(conn):
    _ensure_columns(conn, "locker_operators", {
        "contract_start_at": "TIMESTAMPTZ",
        "contract_end_at": "TIMESTAMPTZ",
        "contract_ref": "VARCHAR(255)",
        "sla_pickup_hours": "INTEGER DEFAULT 72",
        "sla_return_hours": "INTEGER DEFAULT 24",
    })

def _ensure_lockers_columns(conn):
    _ensure_columns(conn, "lockers", {
        "geolocation_wkt": "VARCHAR(100)",
        "slots_available": "INTEGER DEFAULT 0",
        "has_kiosk": "BOOLEAN DEFAULT FALSE",
        "has_printer": "BOOLEAN DEFAULT FALSE",
        "has_card_reader": "BOOLEAN DEFAULT FALSE",
        "has_nfc": "BOOLEAN DEFAULT FALSE",
    })

def _ensure_slot_configs_columns(conn):
    _ensure_columns(conn, "locker_slot_configs", {
        "width_mm": "INTEGER",
        "height_mm": "INTEGER",
        "depth_mm": "INTEGER",
        "max_weight_g": "INTEGER",
    })    

def _ensure_capability_columns(conn):
    _ensure_columns(conn, "capability_profile_target", {
        "locker_id": "VARCHAR(64)",
    })

    

if __name__ == "__main__":
    import json
    result = _run_startup_migrations_if_enabled()
    print(json.dumps(result, indent=2, ensure_ascii=False))
