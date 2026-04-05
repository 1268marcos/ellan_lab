# 01_source/order_pickup_service/app/core/db_super_migrations.py
# 04/04/2026 - Migração completa para PostgreSQL com Capability Catalog
# Compatível com PostgreSQL 15+


# 1. Backup (sempre!)
# docker exec postgres_central pg_dump -U admin -d locker_central > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Rodar migração
# docker exec -it order_pickup_service python -m app.core.db_super_migrations

# 3. Validar
# docker exec -it postgres_central psql -U admin -d locker_central -c "\dt"


from __future__ import annotations
import logging
from typing import Any
from sqlalchemy import inspect, text
from app.core.db import engine

logger = logging.getLogger("order_pickup_service.migrations")


# =============================================================================
# FUNÇÕES AUXILIARES (PostgreSQL-compatible)
# =============================================================================

def _has_table(inspector: Any, table_name: str) -> bool:
    """Verifica se tabela existe."""
    return table_name in inspector.get_table_names()


def _has_column(inspector: Any, table_name: str, column_name: str) -> bool:
    """Verifica se coluna existe na tabela."""
    if not _has_table(inspector, table_name):
        return False
    cols = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in cols)


def _has_index(inspector: Any, table_name: str, index_name: str) -> bool:
    """Verifica se índice existe na tabela."""
    if not _has_table(inspector, table_name):
        return False
    indexes = inspector.get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def _add_column_if_not_exists(conn: Any, table: str, column: str, definition: str, default: str | None = None) -> bool:
    """
    Adiciona coluna se não existir (PostgreSQL: ALTER TABLE ADD COLUMN IF NOT EXISTS).
    Retorna True se a coluna foi adicionada.
    """
    inspector = inspect(conn)
    if _has_table(inspector, table) and not _has_column(inspector, table, column):
        ddl = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {definition}"
        conn.execute(text(ddl))
        if default:
            conn.execute(text(f"UPDATE {table} SET {column} = {default} WHERE {column} IS NULL"))
        logger.info(f"Coluna adicionada: {table}.{column}")
        return True
    return False


def _create_index_if_not_exists(conn: Any, index_name: str, ddl: str) -> bool:
    """
    Cria índice se não existir.
    Retorna True se o índice foi criado.
    """
    inspector = inspect(conn)
    # Verifica em todas as tabelas se o índice já existe
    for table in inspector.get_table_names():
        if _has_index(inspector, table, index_name):
            return False
    conn.execute(text(ddl))
    logger.info(f"Índice criado: {index_name}")
    return True


def _create_table_if_not_exists(conn: Any, table_name: str, ddl: str) -> bool:
    """
    Cria tabela se não existir.
    Retorna True se a tabela foi criada.
    """
    inspector = inspect(conn)
    if not _has_table(inspector, table_name):
        conn.execute(text(ddl))
        logger.info(f"Tabela criada: {table_name}")
        return True
    return False


def _register_migration(conn: Any, migration_name: str, success: bool = True, error_message: str | None = None) -> None:
    """Registra migração na tabela de histórico."""
    conn.execute(
        text("""
            INSERT INTO migration_history (migration_name, success, error_message)
            VALUES (:name, :success, :error)
        """),
        {"name": migration_name, "success": success, "error": error_message}
    )


# =============================================================================
# MIGRAÇÃO: TABELA DE HISTÓRICO DE MIGRAÇÕES
# =============================================================================

def _ensure_migration_history_table(conn: Any) -> None:
    """Garante que a tabela de histórico de migrações existe."""
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS migration_history (
            id SERIAL PRIMARY KEY,
            migration_name VARCHAR(255) NOT NULL,
            applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            success BOOLEAN NOT NULL DEFAULT TRUE,
            error_message TEXT,
            UNIQUE(migration_name)
        )
    """))
    logger.info("Tabela migration_history garantida")


def _migration_already_applied(conn: Any, migration_name: str) -> bool:
    """Verifica se migração já foi aplicada."""
    result = conn.execute(
        text("SELECT success FROM migration_history WHERE migration_name = :name"),
        {"name": migration_name}
    ).fetchone()
    return result is not None and result[0] is True


# =============================================================================
# MIGRAÇÃO: ORDERS - COLUNAS ADICIONAIS
# =============================================================================

def _migrate_orders_columns(conn: Any, applied: list[str]) -> None:
    """Adiciona colunas faltantes na tabela orders."""
    inspector = inspect(conn)
    
    if not _has_table(inspector, "orders"):
        logger.warning("Tabela orders não existe, pulando migração de colunas")
        return
    
    columns_to_add = [
        ("currency", "VARCHAR(8)", "'BRL'"),
        ("site_id", "VARCHAR(100)", "NULL"),
        ("tenant_id", "VARCHAR(100)", "NULL"),
        ("ecommerce_partner_id", "VARCHAR(100)", "NULL"),
        ("partner_order_ref", "VARCHAR(100)", "NULL"),
        ("sku_description", "TEXT", "NULL"),
        ("slot_size", "VARCHAR(8)", "NULL"),
        ("card_last4", "VARCHAR(4)", "NULL"),
        ("card_brand", "VARCHAR(50)", "NULL"),
        ("installments", "INTEGER", "NULL"),
        ("guest_name", "VARCHAR(255)", "NULL"),
        ("consent_analytics", "BOOLEAN", "FALSE"),
        ("cancelled_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("cancel_reason", "TEXT", "NULL"),
        ("refunded_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("refund_reason", "TEXT", "NULL"),
        ("public_access_token_hash", "VARCHAR", "NULL"),
    ]
    
    for col_name, col_def, default_val in columns_to_add:
        if not _has_column(inspector, "orders", col_name):
            ddl = f"ALTER TABLE orders ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
            conn.execute(text(ddl))
            if default_val != "NULL":
                conn.execute(text(f"UPDATE orders SET {col_name} = {default_val} WHERE {col_name} IS NULL"))
            applied.append(f"orders.{col_name}")
            logger.info(f"Coluna adicionada: orders.{col_name}")
    
    # Backfill específico para currency
    if _has_column(inspector, "orders", "currency"):
        conn.execute(text("UPDATE orders SET currency = 'BRL' WHERE currency IS NULL"))
        if "orders.currency" not in applied:
            applied.append("orders.currency_backfill")


# =============================================================================
# MIGRAÇÃO: ORDERS - ÍNDICES
# =============================================================================

def _migrate_orders_indexes(conn: Any, applied: list[str]) -> None:
    """Cria índices faltantes na tabela orders."""
    inspector = inspect(conn)
    
    if not _has_table(inspector, "orders"):
        return
    
    indexes = [
        ("ix_orders_user_id", "CREATE INDEX IF NOT EXISTS ix_orders_user_id ON orders (user_id)"),
        ("ix_orders_ecommerce_partner", "CREATE INDEX IF NOT EXISTS ix_orders_ecommerce_partner ON orders (ecommerce_partner_id)"),
        ("ix_orders_pickup_deadline", "CREATE INDEX IF NOT EXISTS ix_orders_pickup_deadline ON orders (pickup_deadline_at)"),
        ("idx_orders_public_access_token_hash", "CREATE INDEX IF NOT EXISTS idx_orders_public_access_token_hash ON orders (public_access_token_hash)"),
        ("idx_orders_status", "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status)"),
        ("idx_orders_channel_status", "CREATE INDEX IF NOT EXISTS idx_orders_channel_status ON orders (channel, status)"),
        ("idx_orders_region_status", "CREATE INDEX IF NOT EXISTS idx_orders_region_status ON orders (region, status)"),
        ("idx_orders_region_totem_status", "CREATE INDEX IF NOT EXISTS idx_orders_region_totem_status ON orders (region, totem_id, status)"),
        ("idx_orders_region_totem_created_at", "CREATE INDEX IF NOT EXISTS idx_orders_region_totem_created_at ON orders (region, totem_id, created_at)"),
        ("idx_orders_paid_at", "CREATE INDEX IF NOT EXISTS idx_orders_paid_at ON orders (paid_at)"),
        ("idx_orders_picked_up_at", "CREATE INDEX IF NOT EXISTS idx_orders_picked_up_at ON orders (picked_up_at)"),
        ("idx_orders_status_picked_up", "CREATE INDEX IF NOT EXISTS idx_orders_status_picked_up ON orders (status, picked_up_at)"),
        ("idx_orders_totem_picked_up", "CREATE INDEX IF NOT EXISTS idx_orders_totem_picked_up ON orders (totem_id, picked_up_at)"),
    ]
    
    for idx_name, ddl in indexes:
        if not _has_index(inspector, "orders", idx_name):
            conn.execute(text(ddl))
            applied.append(idx_name)
            logger.info(f"Índice criado: {idx_name}")


# =============================================================================
# MIGRAÇÃO: ALLOCATIONS
# =============================================================================

def _migrate_allocations(conn: Any, applied: list[str]) -> None:
    """Migra tabela allocations."""
    inspector = inspect(conn)
    
    if not _has_table(inspector, "allocations"):
        return
    
    columns_to_add = [
        ("slot_size", "VARCHAR(8)", "NULL"),
        ("allocated_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("released_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("release_reason", "TEXT", "NULL"),
    ]
    
    for col_name, col_def, default_val in columns_to_add:
        if not _has_column(inspector, "allocations", col_name):
            ddl = f"ALTER TABLE allocations ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
            conn.execute(text(ddl))
            applied.append(f"allocations.{col_name}")
            logger.info(f"Coluna adicionada: allocations.{col_name}")
    
    # Backfill allocations.locker_id a partir de orders
    if _has_column(inspector, "allocations", "locker_id") and _has_table(inspector, "orders"):
        conn.execute(text("""
            UPDATE allocations
            SET locker_id = (
                SELECT orders.totem_id
                FROM orders
                WHERE orders.id = allocations.order_id
            )
            WHERE locker_id IS NULL
        """))
        applied.append("allocations.locker_id_backfill")
    
    # Índices
    indexes = [
        ("idx_allocations_order_id", "CREATE INDEX IF NOT EXISTS idx_allocations_order_id ON allocations (order_id)"),
        ("idx_allocations_state", "CREATE INDEX IF NOT EXISTS idx_allocations_state ON allocations (state)"),
        ("idx_allocations_locker_slot_state", "CREATE INDEX IF NOT EXISTS idx_allocations_locker_slot_state ON allocations (locker_id, slot, state)"),
        ("idx_allocations_created_at", "CREATE INDEX IF NOT EXISTS idx_allocations_created_at ON allocations (created_at)"),
    ]
    
    for idx_name, ddl in indexes:
        if not _has_index(inspector, "allocations", idx_name):
            conn.execute(text(ddl))
            applied.append(idx_name)


# =============================================================================
# MIGRAÇÃO: PICKUPS
# =============================================================================

def _migrate_pickups(conn: Any, applied: list[str]) -> None:
    """Migra tabela pickups."""
    inspector = inspect(conn)
    
    if not _has_table(inspector, "pickups"):
        return
    
    columns_to_add = [
        ("channel", "VARCHAR(8)", "'ONLINE'"),
        ("locker_id", "VARCHAR", "NULL"),
        ("machine_id", "VARCHAR", "NULL"),
        ("slot", "VARCHAR", "NULL"),
        ("operator_id", "VARCHAR", "NULL"),
        ("tenant_id", "VARCHAR", "NULL"),
        ("site_id", "VARCHAR", "NULL"),
        ("lifecycle_stage", "VARCHAR(24)", "'READY_FOR_PICKUP'"),
        ("activated_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("ready_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("door_opened_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("item_removed_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("door_closed_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("expired_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("cancelled_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("cancel_reason", "VARCHAR", "NULL"),
        ("correlation_id", "VARCHAR", "NULL"),
        ("source_event_id", "VARCHAR", "NULL"),
        ("sensor_event_id", "VARCHAR", "NULL"),
        ("notes", "VARCHAR", "NULL"),
    ]
    
    for col_name, col_def, default_val in columns_to_add:
        if not _has_column(inspector, "pickups", col_name):
            ddl = f"ALTER TABLE pickups ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
            conn.execute(text(ddl))
            if default_val != "NULL":
                conn.execute(text(f"UPDATE pickups SET {col_name} = {default_val} WHERE {col_name} IS NULL"))
            applied.append(f"pickups.{col_name}")
    
    # Backfill de contexto a partir de orders
    if _has_table(inspector, "orders"):
        if _has_column(inspector, "pickups", "channel"):
            conn.execute(text("""
                UPDATE pickups
                SET channel = (
                    SELECT CASE
                        WHEN orders.channel = 'KIOSK' THEN 'KIOSK'
                        ELSE 'ONLINE'
                    END
                    FROM orders
                    WHERE orders.id = pickups.order_id
                )
                WHERE channel IS NULL
            """))
            applied.append("pickups.channel_backfill")
        
        if _has_column(inspector, "pickups", "machine_id"):
            conn.execute(text("""
                UPDATE pickups
                SET machine_id = (
                    SELECT orders.totem_id
                    FROM orders
                    WHERE orders.id = pickups.order_id
                )
                WHERE machine_id IS NULL
            """))
            applied.append("pickups.machine_id_backfill")
    
    # Índices
    indexes = [
        ("ix_pickups_order_id", "CREATE INDEX IF NOT EXISTS ix_pickups_order_id ON pickups (order_id)"),
        ("ix_pickups_status", "CREATE INDEX IF NOT EXISTS ix_pickups_status ON pickups (status)"),
        ("ix_pickups_channel_status", "CREATE INDEX IF NOT EXISTS ix_pickups_channel_status ON pickups (channel, status)"),
        ("ix_pickups_region_status", "CREATE INDEX IF NOT EXISTS ix_pickups_region_status ON pickups (region, status)"),
        ("ix_pickups_locker_status", "CREATE INDEX IF NOT EXISTS ix_pickups_locker_status ON pickups (locker_id, status)"),
        ("ix_pickups_machine_status", "CREATE INDEX IF NOT EXISTS ix_pickups_machine_status ON pickups (machine_id, status)"),
        ("ix_pickups_slot_status", "CREATE INDEX IF NOT EXISTS ix_pickups_slot_status ON pickups (slot, status)"),
        ("ix_pickups_operator_status", "CREATE INDEX IF NOT EXISTS ix_pickups_operator_status ON pickups (operator_id, status)"),
        ("ix_pickups_tenant_status", "CREATE INDEX IF NOT EXISTS ix_pickups_tenant_status ON pickups (tenant_id, status)"),
        ("ix_pickups_site_status", "CREATE INDEX IF NOT EXISTS ix_pickups_site_status ON pickups (site_id, status)"),
        ("ix_pickups_expires_at", "CREATE INDEX IF NOT EXISTS ix_pickups_expires_at ON pickups (expires_at)"),
        ("ix_pickups_redeemed_at", "CREATE INDEX IF NOT EXISTS ix_pickups_redeemed_at ON pickups (redeemed_at)"),
        ("ix_pickups_created_at", "CREATE INDEX IF NOT EXISTS ix_pickups_created_at ON pickups (created_at)"),
        ("ix_pickups_lifecycle_stage", "CREATE INDEX IF NOT EXISTS ix_pickups_lifecycle_stage ON pickups (lifecycle_stage)"),
    ]
    
    for idx_name, ddl in indexes:
        if _has_table(inspector, "pickups") and not _has_index(inspector, "pickups", idx_name):
            conn.execute(text(ddl))
            applied.append(idx_name)


# =============================================================================
# MIGRAÇÃO: USERS
# =============================================================================

def _migrate_users(conn: Any, applied: list[str]) -> None:
    """Migra tabela users."""
    inspector = inspect(conn)
    
    if not _has_table(inspector, "users"):
        return
    
    columns_to_add = [
        ("full_name", "VARCHAR(255)", "NULL"),
        ("phone", "VARCHAR(32)", "NULL"),
        ("password_hash", "VARCHAR(255)", "''"),
        ("is_active", "BOOLEAN", "TRUE"),
        ("email_verified", "BOOLEAN", "FALSE"),
        ("phone_verified", "BOOLEAN", "FALSE"),
        ("locale", "VARCHAR(16)", "'pt-BR'"),
        ("totp_secret_ref", "VARCHAR(255)", "NULL"),
        ("totp_enabled", "BOOLEAN", "FALSE"),
        ("anonymized_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
    ]
    
    for col_name, col_def, default_val in columns_to_add:
        if not _has_column(inspector, "users", col_name):
            ddl = f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
            conn.execute(text(ddl))
            if default_val != "NULL":
                conn.execute(text(f"UPDATE users SET {col_name} = {default_val} WHERE {col_name} IS NULL"))
            applied.append(f"users.{col_name}")
    
    # Índices
    indexes = [
        ("ix_users_email", "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"),
        ("ix_users_phone", "CREATE INDEX IF NOT EXISTS ix_users_phone ON users (phone)"),
    ]
    
    for idx_name, ddl in indexes:
        if not _has_index(inspector, "users", idx_name):
            conn.execute(text(ddl))
            applied.append(idx_name)


# =============================================================================
# MIGRAÇÃO: AUTH_SESSIONS
# =============================================================================

def _migrate_auth_sessions(conn: Any, applied: list[str]) -> None:
    """Migra tabela auth_sessions."""
    inspector = inspect(conn)
    
    if not _has_table(inspector, "auth_sessions"):
        return
    
    columns_to_add = [
        ("user_agent", "VARCHAR(500)", "NULL"),
        ("ip_address", "VARCHAR(64)", "NULL"),
        ("revoked_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
    ]
    
    for col_name, col_def, default_val in columns_to_add:
        if not _has_column(inspector, "auth_sessions", col_name):
            ddl = f"ALTER TABLE auth_sessions ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
            conn.execute(text(ddl))
            applied.append(f"auth_sessions.{col_name}")
    
    # Índices
    indexes = [
        ("ix_auth_sessions_session_token_hash", "CREATE UNIQUE INDEX IF NOT EXISTS ix_auth_sessions_session_token_hash ON auth_sessions (session_token_hash)"),
        ("ix_auth_sessions_user_id", "CREATE INDEX IF NOT EXISTS ix_auth_sessions_user_id ON auth_sessions (user_id)"),
    ]
    
    for idx_name, ddl in indexes:
        if not _has_index(inspector, "auth_sessions", idx_name):
            conn.execute(text(ddl))
            applied.append(idx_name)


# =============================================================================
# MIGRAÇÃO: NOTIFICATION_LOGS
# =============================================================================

def _migrate_notification_logs(conn: Any, applied: list[str]) -> None:
    """Migra tabela notification_logs."""
    inspector = inspect(conn)
    
    if not _has_table(inspector, "notification_logs"):
        return
    
    columns_to_add = [
        ("destination_value", "VARCHAR(255)", "NULL"),
        ("attempt_count", "INTEGER", "0"),
        ("payload_json", "TEXT", "NULL"),
        ("dedupe_key", "VARCHAR(255)", "NULL"),
        ("processing_started_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("last_attempt_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("next_attempt_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("pickup_id", "VARCHAR", "NULL"),
        ("delivery_id", "VARCHAR", "NULL"),
        ("rental_id", "VARCHAR", "NULL"),
        ("locale", "VARCHAR(16)", "'pt-BR'"),
        ("provider_status", "VARCHAR(100)", "NULL"),
        ("error_detail", "TEXT", "NULL"),
    ]
    
    for col_name, col_def, default_val in columns_to_add:
        if not _has_column(inspector, "notification_logs", col_name):
            ddl = f"ALTER TABLE notification_logs ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
            conn.execute(text(ddl))
            if default_val != "NULL":
                conn.execute(text(f"UPDATE notification_logs SET {col_name} = {default_val} WHERE {col_name} IS NULL"))
            applied.append(f"notification_logs.{col_name}")
    
    # Backfill dedupe_key
    if _has_column(inspector, "notification_logs", "dedupe_key"):
        conn.execute(text("""
            UPDATE notification_logs
            SET dedupe_key =
                COALESCE(channel, '') || '|' ||
                COALESCE(template_key, '') || '|' ||
                COALESCE(destination_value, '') || '|' ||
                COALESCE(payload_json->>'receipt_code', '')
            WHERE dedupe_key IS NULL OR dedupe_key = ''
        """))
        applied.append("notification_logs.dedupe_key_backfill")
    
    # Índices
    indexes = [
        ("ux_notification_logs_dedupe", "CREATE UNIQUE INDEX IF NOT EXISTS ux_notification_logs_dedupe ON notification_logs (dedupe_key)"),
        ("ix_notification_logs_next_attempt_at", "CREATE INDEX IF NOT EXISTS ix_notification_logs_next_attempt_at ON notification_logs (next_attempt_at)"),
        ("ix_notification_logs_status_next_attempt_at", "CREATE INDEX IF NOT EXISTS ix_notification_logs_status_next_attempt_at ON notification_logs (status, next_attempt_at)"),
        ("ix_notif_order", "CREATE INDEX IF NOT EXISTS ix_notif_order ON notification_logs (order_id)"),
        ("ix_notif_pickup", "CREATE INDEX IF NOT EXISTS ix_notif_pickup ON notification_logs (pickup_id)"),
        ("ix_notif_delivery", "CREATE INDEX IF NOT EXISTS ix_notif_delivery ON notification_logs (delivery_id)"),
        ("ix_notif_next_attempt", "CREATE INDEX IF NOT EXISTS ix_notif_next_attempt ON notification_logs (next_attempt_at)"),
    ]
    
    for idx_name, ddl in indexes:
        if not _has_index(inspector, "notification_logs", idx_name):
            conn.execute(text(ddl))
            applied.append(idx_name)


# =============================================================================
# MIGRAÇÃO: FISCAL_DOCUMENTS
# =============================================================================

def _migrate_fiscal_documents(conn: Any, applied: list[str]) -> None:
    """Migra tabela fiscal_documents."""
    inspector = inspect(conn)
    
    if not _has_table(inspector, "fiscal_documents"):
        ddl = """
            CREATE TABLE IF NOT EXISTS fiscal_documents (
                id VARCHAR PRIMARY KEY,
                order_id VARCHAR NOT NULL UNIQUE,
                receipt_code VARCHAR(64) NOT NULL UNIQUE,
                document_type VARCHAR(50) NOT NULL,
                channel VARCHAR(20),
                region VARCHAR(10),
                amount_cents INTEGER NOT NULL,
                currency VARCHAR(10) NOT NULL,
                delivery_mode VARCHAR(20),
                send_status VARCHAR(50),
                send_target VARCHAR(255),
                print_status VARCHAR(50),
                print_site_path VARCHAR(255),
                payload_json TEXT NOT NULL,
                issued_at TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                tenant_id VARCHAR(100),
                tax_amount_cents INTEGER,
                tax_breakdown_json JSONB,
                sent_at TIMESTAMP WITH TIME ZONE,
                printed_at TIMESTAMP WITH TIME ZONE,
                xml_signed BOOLEAN DEFAULT FALSE,
                chave_acesso VARCHAR(44),
                cancelled_at TIMESTAMP WITH TIME ZONE,
                cancel_reason TEXT
            )
        """
        conn.execute(text(ddl))
        applied.append("fiscal_documents.create_table")
        logger.info("Tabela fiscal_documents criada")
        return
    
    # Colunas adicionais se tabela já existir
    columns_to_add = [
        ("tenant_id", "VARCHAR(100)", "NULL"),
        ("tax_amount_cents", "INTEGER", "NULL"),
        ("tax_breakdown_json", "JSONB", "NULL"),
        ("sent_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("printed_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("xml_signed", "BOOLEAN", "FALSE"),
        ("chave_acesso", "VARCHAR(44)", "NULL"),
        ("cancelled_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
        ("cancel_reason", "TEXT", "NULL"),
    ]
    
    for col_name, col_def, default_val in columns_to_add:
        if not _has_column(inspector, "fiscal_documents", col_name):
            ddl = f"ALTER TABLE fiscal_documents ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
            conn.execute(text(ddl))
            applied.append(f"fiscal_documents.{col_name}")


# =============================================================================
# MIGRAÇÃO: LOCKERS E CONFIGURAÇÕES
# =============================================================================

def _migrate_lockers(conn: Any, applied: list[str]) -> None:
    """Migra tabelas de lockers."""
    inspector = inspect(conn)
    
    # Tabela lockers
    if not _has_table(inspector, "lockers"):
        ddl = """
            CREATE TABLE IF NOT EXISTS lockers (
                id VARCHAR PRIMARY KEY,
                region VARCHAR(10) NOT NULL,
                display_name VARCHAR(255),
                slots_count INTEGER NOT NULL,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                allowed_channels VARCHAR(100),
                allowed_payment_methods VARCHAR(255),
                timezone VARCHAR(50),
                site_id VARCHAR(100),
                access_hours TEXT,
                address_line VARCHAR(255),
                address_number VARCHAR(50),
                address_extra VARCHAR(255),
                district VARCHAR(100),
                city VARCHAR(100),
                state VARCHAR(100),
                country VARCHAR(100),
                postal_code VARCHAR(50),
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                description TEXT,
                external_id VARCHAR(100),
                has_alarm BOOLEAN DEFAULT FALSE,
                has_camera BOOLEAN DEFAULT FALSE,
                is_rented BOOLEAN DEFAULT FALSE,
                machine_id VARCHAR(100),
                tenant_id VARCHAR(100),
                metadata_json JSONB,
                security_level VARCHAR(50),
                temperature_zone VARCHAR(50),
                operator_id VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                slots_available INTEGER,
                geolocation_wkt TEXT,
                has_kiosk BOOLEAN DEFAULT FALSE,
                has_printer BOOLEAN DEFAULT FALSE,
                has_card_reader BOOLEAN DEFAULT FALSE,
                has_nfc BOOLEAN DEFAULT FALSE
            )
        """
        conn.execute(text(ddl))
        applied.append("lockers.create_table")
    else:
        # Colunas adicionais
        columns_to_add = [
            ("slots_available", "INTEGER", "NULL"),
            ("geolocation_wkt", "TEXT", "NULL"),
            ("has_kiosk", "BOOLEAN", "FALSE"),
            ("has_printer", "BOOLEAN", "FALSE"),
            ("has_card_reader", "BOOLEAN", "FALSE"),
            ("has_nfc", "BOOLEAN", "FALSE"),
        ]
        for col_name, col_def, default_val in columns_to_add:
            if not _has_column(inspector, "lockers", col_name):
                ddl = f"ALTER TABLE lockers ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
                conn.execute(text(ddl))
                applied.append(f"lockers.{col_name}")
    
    # Índices lockers
    indexes = [
        ("idx_lockers_active", "CREATE INDEX IF NOT EXISTS idx_lockers_active ON lockers (active)"),
        ("idx_lockers_operator", "CREATE INDEX IF NOT EXISTS idx_lockers_operator ON lockers (operator_id)"),
        ("idx_lockers_region", "CREATE INDEX IF NOT EXISTS idx_lockers_region ON lockers (region)"),
        ("idx_lockers_site_id", "CREATE INDEX IF NOT EXISTS idx_lockers_site_id ON lockers (site_id)"),
        ("ix_lockers_tenant_id", "CREATE INDEX IF NOT EXISTS ix_lockers_tenant_id ON lockers (tenant_id)"),
        ("ix_lockers_machine_id", "CREATE INDEX IF NOT EXISTS ix_lockers_machine_id ON lockers (machine_id)"),
        ("ix_lockers_lat_lng", "CREATE INDEX IF NOT EXISTS ix_lockers_lat_lng ON lockers (latitude, longitude)"),
    ]
    
    for idx_name, ddl in indexes:
        if _has_table(inspector, "lockers") and not _has_index(inspector, "lockers", idx_name):
            conn.execute(text(ddl))
            applied.append(idx_name)
    
    # Tabela locker_slot_configs
    if not _has_table(inspector, "locker_slot_configs"):
        ddl = """
            CREATE TABLE IF NOT EXISTS locker_slot_configs (
                id BIGSERIAL PRIMARY KEY,
                locker_id VARCHAR(64) NOT NULL REFERENCES lockers(id),
                slot_size VARCHAR(8) NOT NULL,
                slot_count INTEGER NOT NULL DEFAULT 0,
                available_count INTEGER,
                width_mm INTEGER,
                height_mm INTEGER,
                depth_mm INTEGER,
                max_weight_g INTEGER,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                width_mm INTEGER,
                height_mm INTEGER,
                depth_mm INTEGER,
                max_weight_g BIGINT
            )
        """
        conn.execute(text(ddl))
        applied.append("locker_slot_configs.create_table")
    else:
        columns_to_add = [
            ("width_mm", "INTEGER", "NULL"),
            ("height_mm", "INTEGER", "NULL"),
            ("depth_mm", "INTEGER", "NULL"),
            ("max_weight_g", "BIGINT", "NULL"),
        ]
        for col_name, col_def, default_val in columns_to_add:
            if not _has_column(inspector, "locker_slot_configs", col_name):
                ddl = f"ALTER TABLE locker_slot_configs ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
                conn.execute(text(ddl))
                applied.append(f"locker_slot_configs.{col_name}")
    
    # Índice locker_slot_configs
    if _has_table(inspector, "locker_slot_configs"):
        if not _has_index(inspector, "locker_slot_configs", "idx_locker_slot_locker"):
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_locker_slot_locker ON locker_slot_configs (locker_id)"))
            applied.append("idx_locker_slot_locker")
    
    # Tabela locker_operators
    if not _has_table(inspector, "locker_operators"):
        ddl = """
            CREATE TABLE IF NOT EXISTS locker_operators (
                id VARCHAR(64) PRIMARY KEY,
                name VARCHAR(128) NOT NULL,
                document VARCHAR(32),
                email VARCHAR(128),
                phone VARCHAR(32),
                operator_type VARCHAR(32) NOT NULL DEFAULT 'LOGISTICS',
                country VARCHAR(2) NOT NULL DEFAULT 'BR',
                active BOOLEAN NOT NULL DEFAULT TRUE,
                commission_rate FLOAT,
                currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                contract_start_at TIMESTAMP WITH TIME ZONE,
                contract_end_at TIMESTAMP WITH TIME ZONE,
                contract_ref VARCHAR(100),
                sla_pickup_hours INTEGER,
                sla_return_hours INTEGER
            )
        """
        conn.execute(text(ddl))
        applied.append("locker_operators.create_table")
    else:
        columns_to_add = [
            ("country", "VARCHAR(2)", "'BR'"),
            ("contract_start_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
            ("contract_end_at", "TIMESTAMP WITH TIME ZONE", "NULL"),
            ("contract_ref", "VARCHAR(100)", "NULL"),
            ("sla_pickup_hours", "INTEGER", "72"),
            ("sla_return_hours", "INTEGER", "24"),
        ]
        for col_name, col_def, default_val in columns_to_add:
            if not _has_column(inspector, "locker_operators", col_name):
                ddl = f"ALTER TABLE locker_operators ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
                conn.execute(text(ddl))
                applied.append(f"locker_operators.{col_name}")
    
    # Índice locker_operators
    if _has_table(inspector, "locker_operators"):
        if not _has_index(inspector, "locker_operators", "idx_operator_document"):
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_operator_document ON locker_operators (document)"))
            applied.append("idx_operator_document")
    
    # Tabela product_categories
    if not _has_table(inspector, "product_categories"):
        ddl = """
            CREATE TABLE IF NOT EXISTS product_categories (
                id VARCHAR(64) PRIMARY KEY,
                name VARCHAR(128) NOT NULL,
                description TEXT,
                parent_category VARCHAR(64),
                default_temperature_zone VARCHAR(32) NOT NULL DEFAULT 'AMBIENT',
                default_security_level VARCHAR(32) NOT NULL DEFAULT 'STANDARD',
                is_hazardous BOOLEAN NOT NULL DEFAULT FALSE,
                requires_age_verification BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                max_weight_g BIGINT
            )
        """
        conn.execute(text(ddl))
        applied.append("product_categories.create_table")
    else:
        if not _has_column(inspector, "product_categories", "max_weight_g"):
            conn.execute(text("ALTER TABLE product_categories ADD COLUMN IF NOT EXISTS max_weight_g BIGINT"))
            applied.append("product_categories.max_weight_g")
    
    # Índice product_categories
    if _has_table(inspector, "product_categories"):
        if not _has_index(inspector, "product_categories", "idx_product_categories_parent"):
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_product_categories_parent ON product_categories (parent_category)"))
            applied.append("idx_product_categories_parent")
    
    # Tabela product_locker_configs
    if not _has_table(inspector, "product_locker_configs"):
        ddl = """
            CREATE TABLE IF NOT EXISTS product_locker_configs (
                id BIGSERIAL PRIMARY KEY,
                locker_id VARCHAR(64) NOT NULL REFERENCES lockers(id),
                category VARCHAR(64) NOT NULL REFERENCES product_categories(id),
                subcategory VARCHAR(64),
                allowed BOOLEAN NOT NULL DEFAULT TRUE,
                temperature_zone VARCHAR(32) NOT NULL DEFAULT 'ANY',
                min_value BIGINT,
                max_value BIGINT,
                max_weight_g INTEGER,
                max_width_mm INTEGER,
                max_height_mm INTEGER,
                max_depth_mm INTEGER,
                requires_signature BOOLEAN NOT NULL DEFAULT FALSE,
                requires_id BOOLEAN NOT NULL DEFAULT FALSE,
                is_fragile BOOLEAN NOT NULL DEFAULT FALSE,
                is_hazardous BOOLEAN NOT NULL DEFAULT FALSE,
                priority INTEGER NOT NULL DEFAULT 100,
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                min_value_cents BIGINT,
                max_value_cents BIGINT,
                max_weight_g BIGINT,
                max_width_mm INTEGER,
                max_height_mm INTEGER,
                max_depth_mm INTEGER,
                requires_id_check BOOLEAN DEFAULT FALSE
            )
        """
        conn.execute(text(ddl))
        applied.append("product_locker_configs.create_table")
        
        # Índice único
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_locker_category ON product_locker_configs (locker_id, category)"))
        applied.append("uq_locker_category")
    else:
        columns_to_add = [
            ("min_value_cents", "BIGINT", "NULL"),
            ("max_value_cents", "BIGINT", "NULL"),
            ("max_weight_g", "BIGINT", "NULL"),
            ("max_width_mm", "INTEGER", "NULL"),
            ("max_height_mm", "INTEGER", "NULL"),
            ("max_depth_mm", "INTEGER", "NULL"),
            ("requires_id_check", "BOOLEAN", "FALSE"),
        ]
        for col_name, col_def, default_val in columns_to_add:
            if not _has_column(inspector, "product_locker_configs", col_name):
                ddl = f"ALTER TABLE product_locker_configs ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
                conn.execute(text(ddl))
                applied.append(f"product_locker_configs.{col_name}")
    
    # Índices product_locker_configs
    if _has_table(inspector, "product_locker_configs"):
        indexes = [
            ("idx_product_config_locker", "CREATE INDEX IF NOT EXISTS idx_product_config_locker ON product_locker_configs (locker_id)"),
            ("idx_product_config_category", "CREATE INDEX IF NOT EXISTS idx_product_config_category ON product_locker_configs (category)"),
        ]
        for idx_name, ddl in indexes:
            if not _has_index(inspector, "product_locker_configs", idx_name):
                conn.execute(text(ddl))
                applied.append(idx_name)


# =============================================================================
# MIGRAÇÃO: CAPABILITY CATALOG (14 TABELAS)
# =============================================================================

def _migrate_capability_catalog(conn: Any, applied: list[str]) -> None:
    """Cria tabelas do Capability Catalog se não existirem."""
    inspector = inspect(conn)
    
    tables = [
        ("capability_region", """
            CREATE TABLE IF NOT EXISTS capability_region (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                code VARCHAR(10) NOT NULL UNIQUE,
                name VARCHAR(128) NOT NULL,
                country_code VARCHAR(2) NOT NULL,
                continent VARCHAR(64),
                default_currency VARCHAR(8) NOT NULL,
                default_timezone VARCHAR(64) NOT NULL,
                default_locale VARCHAR(16) NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """),
        ("capability_channel", """
            CREATE TABLE IF NOT EXISTS capability_channel (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                code VARCHAR(32) NOT NULL UNIQUE,
                name VARCHAR(128) NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """),
        ("capability_context", """
            CREATE TABLE IF NOT EXISTS capability_context (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                channel_id UUID NOT NULL REFERENCES capability_channel(id),
                code VARCHAR(64) NOT NULL,
                name VARCHAR(128) NOT NULL,
                description TEXT,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                UNIQUE(channel_id, code)
            )
        """),
        ("payment_method_catalog", """
            CREATE TABLE IF NOT EXISTS payment_method_catalog (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                code VARCHAR(32) NOT NULL UNIQUE,
                name VARCHAR(128) NOT NULL,
                family VARCHAR(32) NOT NULL,
                is_wallet BOOLEAN NOT NULL DEFAULT FALSE,
                is_card BOOLEAN NOT NULL DEFAULT FALSE,
                is_bnpl BOOLEAN NOT NULL DEFAULT FALSE,
                is_cash_like BOOLEAN NOT NULL DEFAULT FALSE,
                is_bank_transfer BOOLEAN NOT NULL DEFAULT FALSE,
                is_instant BOOLEAN NOT NULL DEFAULT FALSE,
                requires_redirect BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """),
        ("payment_interface_catalog", """
            CREATE TABLE IF NOT EXISTS payment_interface_catalog (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                code VARCHAR(32) NOT NULL UNIQUE,
                name VARCHAR(128) NOT NULL,
                interface_type VARCHAR(32) NOT NULL,
                requires_hw BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """),
        ("wallet_provider_catalog", """
            CREATE TABLE IF NOT EXISTS wallet_provider_catalog (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                code VARCHAR(32) NOT NULL UNIQUE,
                name VARCHAR(128) NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """),
        ("capability_requirement_catalog", """
            CREATE TABLE IF NOT EXISTS capability_requirement_catalog (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                code VARCHAR(64) NOT NULL UNIQUE,
                name VARCHAR(128) NOT NULL,
                data_type VARCHAR(32) NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """),
        ("capability_profile", """
            CREATE TABLE IF NOT EXISTS capability_profile (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                region_id UUID NOT NULL REFERENCES capability_region(id),
                channel_id UUID NOT NULL REFERENCES capability_channel(id),
                context_id UUID REFERENCES capability_context(id),
                profile_code VARCHAR(128) NOT NULL UNIQUE,
                name VARCHAR(256) NOT NULL,
                priority INTEGER NOT NULL DEFAULT 100,
                currency VARCHAR(8) NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """),
        ("capability_profile_method", """
            CREATE TABLE IF NOT EXISTS capability_profile_method (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                profile_id UUID NOT NULL REFERENCES capability_profile(id),
                payment_method_id UUID NOT NULL REFERENCES payment_method_catalog(id),
                sort_order INTEGER NOT NULL DEFAULT 100,
                is_default BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                max_installments INTEGER,
                wallet_provider_id UUID REFERENCES wallet_provider_catalog(id),
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                UNIQUE(profile_id, payment_method_id)
            )
        """),
        ("capability_profile_method_interface", """
            CREATE TABLE IF NOT EXISTS capability_profile_method_interface (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                profile_method_id UUID NOT NULL REFERENCES capability_profile_method(id),
                payment_interface_id UUID NOT NULL REFERENCES payment_interface_catalog(id),
                sort_order INTEGER NOT NULL DEFAULT 100,
                is_default BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                UNIQUE(profile_method_id, payment_interface_id)
            )
        """),
        ("capability_profile_method_requirement", """
            CREATE TABLE IF NOT EXISTS capability_profile_method_requirement (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                profile_method_id UUID NOT NULL REFERENCES capability_profile_method(id),
                requirement_id UUID NOT NULL REFERENCES capability_requirement_catalog(id),
                is_required BOOLEAN NOT NULL DEFAULT TRUE,
                requirement_scope VARCHAR(32) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                UNIQUE(profile_method_id, requirement_id)
            )
        """),
        ("capability_profile_action", """
            CREATE TABLE IF NOT EXISTS capability_profile_action (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                profile_id UUID NOT NULL REFERENCES capability_profile(id),
                action_code VARCHAR(64) NOT NULL,
                label VARCHAR(128) NOT NULL,
                action_type VARCHAR(32) NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 100,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                UNIQUE(profile_id, action_code)
            )
        """),
        ("capability_profile_constraint", """
            CREATE TABLE IF NOT EXISTS capability_profile_constraint (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                profile_id UUID NOT NULL REFERENCES capability_profile(id),
                code VARCHAR(64) NOT NULL,
                value_json JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                UNIQUE(profile_id, code)
            )
        """),
        ("capability_profile_target", """
            CREATE TABLE IF NOT EXISTS capability_profile_target (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                profile_id UUID NOT NULL REFERENCES capability_profile(id),
                target_type VARCHAR(32) NOT NULL,
                target_key VARCHAR(256) NOT NULL,
                locker_id VARCHAR REFERENCES lockers(id),
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                metadata_json JSONB,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                UNIQUE(profile_id, target_type, target_key)
            )
        """),
        ("capability_profile_snapshot", """
            CREATE TABLE IF NOT EXISTS capability_profile_snapshot (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                profile_id UUID NOT NULL REFERENCES capability_profile(id),
                profile_code VARCHAR(128) NOT NULL,
                resolved_json JSONB NOT NULL,
                snapshot_hash VARCHAR(64) NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                status VARCHAR(32) NOT NULL DEFAULT 'DRAFT',
                published_at TIMESTAMP WITH TIME ZONE,
                generated_by VARCHAR(64),
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """),
    ]
    
    for table_name, ddl in tables:
        if _create_table_if_not_exists(conn, table_name, ddl):
            applied.append(f"{table_name}.create")


# =============================================================================
# MIGRAÇÃO: DOMAIN EVENT OUTBOX
# =============================================================================

def _migrate_domain_event_outbox(conn: Any, applied: list[str]) -> None:
    """Cria tabela domain_event_outbox se não existir."""
    inspector = inspect(conn)
    
    if not _has_table(inspector, "domain_event_outbox"):
        ddl = """
            CREATE TABLE IF NOT EXISTS domain_event_outbox (
                id VARCHAR PRIMARY KEY,
                event_key VARCHAR(255) NOT NULL,
                aggregate_type VARCHAR(100),
                aggregate_id VARCHAR(100),
                event_name VARCHAR(100),
                event_version INTEGER,
                status VARCHAR(50),
                payload_json TEXT,
                occurred_at TIMESTAMP WITH TIME ZONE,
                published_at TIMESTAMP WITH TIME ZONE,
                last_error TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """
        conn.execute(text(ddl))
        applied.append("domain_event_outbox.create")
        logger.info("Tabela domain_event_outbox criada")


# =============================================================================
# MIGRAÇÃO: PICKUP_TOKENS
# =============================================================================

def _migrate_pickup_tokens(conn: Any, applied: list[str]) -> None:
    """Cria tabela pickup_tokens se não existir."""
    inspector = inspect(conn)
    
    if not _has_table(inspector, "pickup_tokens"):
        ddl = """
            CREATE TABLE IF NOT EXISTS pickup_tokens (
                id VARCHAR PRIMARY KEY,
                pickup_id VARCHAR NOT NULL REFERENCES pickups(id),
                token_hash VARCHAR(255) NOT NULL UNIQUE,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                used_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """
        conn.execute(text(ddl))
        applied.append("pickup_tokens.create")
        logger.info("Tabela pickup_tokens criada")
    
    # Índices
    if _has_table(inspector, "pickup_tokens"):
        indexes = [
            ("ix_pickup_tokens_token_hash", "CREATE INDEX IF NOT EXISTS ix_pickup_tokens_token_hash ON pickup_tokens (token_hash)"),
            ("ix_pickup_tokens_pickup_id", "CREATE INDEX IF NOT EXISTS ix_pickup_tokens_pickup_id ON pickup_tokens (pickup_id)"),
        ]
        for idx_name, ddl in indexes:
            if not _has_index(inspector, "pickup_tokens", idx_name):
                conn.execute(text(ddl))
                applied.append(idx_name)


# =============================================================================
# MIGRAÇÃO: CREDIT
# =============================================================================

def _migrate_credit(conn: Any, applied: list[str]) -> None:
    """Cria tabela credit se não existir."""
    inspector = inspect(conn)
    
    if not _has_table(inspector, "credit"):
        ddl = """
            CREATE TABLE IF NOT EXISTS credit (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL REFERENCES users(id),
                amount_cents BIGINT NOT NULL,
                balance_cents BIGINT NOT NULL,
                currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
                status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
                expires_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """
        conn.execute(text(ddl))
        applied.append("credit.create")
        logger.info("Tabela credit criada")
    
    # Índices
    if _has_table(inspector, "credit"):
        if not _has_index(inspector, "credit", "ix_credit_user_id"):
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_credit_user_id ON credit (user_id)"))
            applied.append("ix_credit_user_id")


# =============================================================================
# MIGRAÇÃO: KIOSK_ANTIFRAUD_EVENT
# =============================================================================

def _migrate_kiosk_antifraud_event(conn: Any, applied: list[str]) -> None:
    """Cria tabela kiosk_antifraud_event se não existir."""
    inspector = inspect(conn)
    
    if not _has_table(inspector, "kiosk_antifraud_event"):
        ddl = """
            CREATE TABLE IF NOT EXISTS kiosk_antifraud_event (
                id VARCHAR PRIMARY KEY,
                kiosk_id VARCHAR NOT NULL,
                event_type VARCHAR(64) NOT NULL,
                risk_score INTEGER,
                risk_level VARCHAR(32),
                payload_json JSONB,
                action_taken VARCHAR(64),
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """
        conn.execute(text(ddl))
        applied.append("kiosk_antifraud_event.create")
        logger.info("Tabela kiosk_antifraud_event criada")
    
    # Índices
    if _has_table(inspector, "kiosk_antifraud_event"):
        indexes = [
            ("ix_kiosk_antifraud_kiosk_id", "CREATE INDEX IF NOT EXISTS ix_kiosk_antifraud_kiosk_id ON kiosk_antifraud_event (kiosk_id)"),
            ("ix_kiosk_antifraud_created_at", "CREATE INDEX IF NOT EXISTS ix_kiosk_antifraud_created_at ON kiosk_antifraud_event (created_at)"),
        ]
        for idx_name, ddl in indexes:
            if not _has_index(inspector, "kiosk_antifraud_event", idx_name):
                conn.execute(text(ddl))
                applied.append(idx_name)


# =============================================================================
# MIGRAÇÃO: LOGIN_OTP
# =============================================================================

def _migrate_login_otp(conn: Any, applied: list[str]) -> None:
    """Cria tabela login_otp se não existir."""
    inspector = inspect(conn)
    
    if not _has_table(inspector, "login_otp"):
        ddl = """
            CREATE TABLE IF NOT EXISTS login_otp (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL REFERENCES users(id),
                otp_hash VARCHAR(255) NOT NULL,
                phone VARCHAR(32),
                email VARCHAR(255),
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                used_at TIMESTAMP WITH TIME ZONE,
                attempt_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            )
        """
        conn.execute(text(ddl))
        applied.append("login_otp.create")
        logger.info("Tabela login_otp criada")
    
    # Índices
    if _has_table(inspector, "login_otp"):
        if not _has_index(inspector, "login_otp", "ix_login_otp_user_id"):
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_login_otp_user_id ON login_otp (user_id)"))
            applied.append("ix_login_otp_user_id")


# =============================================================================
# FUNÇÃO PRINCIPAL DE MIGRAÇÃO
# =============================================================================

def migrate_postgres_schema() -> dict[str, Any]:
    """
    Executa todas as migrações do schema PostgreSQL.
    Retorna dicionário com status e lista de migrações aplicadas.
    """
    applied: list[str] = []
    errors: list[str] = []
    
    try:
        with engine.begin() as conn:
            # 1. Garante tabela de histórico de migrações
            _ensure_migration_history_table(conn)
            
            # 2. Executa migrações em ordem de dependência
            migrations = [
                ("migration_history_table", lambda: _ensure_migration_history_table(conn)),
                ("orders_columns", lambda: _migrate_orders_columns(conn, applied)),
                ("orders_indexes", lambda: _migrate_orders_indexes(conn, applied)),
                ("allocations", lambda: _migrate_allocations(conn, applied)),
                ("pickups", lambda: _migrate_pickups(conn, applied)),
                ("users", lambda: _migrate_users(conn, applied)),
                ("auth_sessions", lambda: _migrate_auth_sessions(conn, applied)),
                ("notification_logs", lambda: _migrate_notification_logs(conn, applied)),
                ("fiscal_documents", lambda: _migrate_fiscal_documents(conn, applied)),
                ("lockers", lambda: _migrate_lockers(conn, applied)),
                ("capability_catalog", lambda: _migrate_capability_catalog(conn, applied)),
                ("domain_event_outbox", lambda: _migrate_domain_event_outbox(conn, applied)),
                ("pickup_tokens", lambda: _migrate_pickup_tokens(conn, applied)),
                ("credit", lambda: _migrate_credit(conn, applied)),
                ("kiosk_antifraud_event", lambda: _migrate_kiosk_antifraud_event(conn, applied)),
                ("login_otp", lambda: _migrate_login_otp(conn, applied)),
            ]
            
            for migration_name, migration_func in migrations:
                try:
                    if _migration_already_applied(conn, migration_name):
                        logger.info(f"Migração já aplicada: {migration_name}")
                        continue
                    
                    logger.info(f"Executando migração: {migration_name}")
                    migration_func()
                    _register_migration(conn, migration_name, success=True)
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Erro na migração {migration_name}: {error_msg}")
                    _register_migration(conn, migration_name, success=False, error_message=error_msg)
                    errors.append(f"{migration_name}: {error_msg}")
                    # Continua para próximas migrações (não aborta tudo)
            
            conn.commit()
            
    except Exception as e:
        logger.error(f"Erro crítico na migração: {str(e)}")
        errors.append(f"CRITICAL: {str(e)}")
    
    return {
        "ok": len(errors) == 0,
        "applied": applied,
        "errors": errors,
        "total_applied": len(applied),
        "total_errors": len(errors),
    }


# =============================================================================
# FUNÇÃO DE INICIALIZAÇÃO (CHAMADA NO STARTUP)
# =============================================================================

def _run_startup_migrations_if_enabled() -> dict[str, Any]:
    """
    Executa migrações no startup da aplicação.
    Deve ser chamada durante a inicialização do serviço.
    """
    from app.core.config import settings
    
    if not getattr(settings, 'run_db_migrations_on_startup', True):
        logger.info("RUN_DB_MIGRATIONS_ON_STARTUP=false; migrações automáticas desabilitadas.")
        return {"ok": True, "applied": [], "skipped": True}
    
    logger.info("🚀 Executando migrações automáticas do order_pickup_service...")
    result = migrate_postgres_schema()
    
    if result.get("applied"):
        logger.info(f"✅ Migrações aplicadas ({len(result['applied'])}): {', '.join(result['applied'][:5])}...")
    else:
        logger.info("✔ Nenhuma migração pendente foi aplicada.")
    
    if result.get("errors"):
        logger.error(f"❌ Erros nas migrações ({len(result['errors'])}): {result['errors'][:3]}")
    
    return result


# =============================================================================
# EXECUÇÃO DIRETA (PARA TESTES/CLI)
# =============================================================================

if __name__ == "__main__":
    import sys
    import json
    
    print("=" * 80)
    print("🔧 MIGRAÇÃO DE SCHEMA POSTGRESQL")
    print("=" * 80)
    
    result = _run_startup_migrations_if_enabled()
    
    print("\n" + "=" * 80)
    print("📊 RESULTADO:")
    print("=" * 80)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("ok"):
        print("\n✅ Migração concluída com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Migração falhou. Verifique os erros acima.")
        sys.exit(1)