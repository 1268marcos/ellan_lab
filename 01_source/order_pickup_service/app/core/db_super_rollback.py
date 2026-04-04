# 01_source/order_pickup_service/app/core/db_super_rollback.py
# 04/04/2026 - Script de rollback para migrações PostgreSQL
# Compatível com PostgreSQL 15+ e sistema de migration_history

# 🔒 Checklist de Segurança Antes do Rollback
# 0. Backup (sempre!)  docker exec postgres_central pg_dump -U admin -d locker_central > backup_$(date +%Y%m%d_%H%M%S).sql
# 1. Backup       pg_dump -U admin -d locker_central > backup_rollback.sql
# 2. Status       python -m app.core.db_rollback status
# 3. Dry-run      python -m app.core.db_rollback last --dry-run
#                 SEMPRE use --dry-run primeiro para ver o que será afetado
# 4. Executar     python -m app.core.db_rollback last
# 5. Validar      python -m app.core.db_rollback status

# 1. Verificar Status das Migrações
# Ver quais migrações foram aplicadas
#   docker exec -it order_pickup_service python -m app.core.db_rollback status

# 2. Reverter Última Migração
# Simular primeiro (dry-run)
#   docker exec -it order_pickup_service python -m app.core.db_rollback last --dry-run
# Executar rollback real
#   docker exec -it order_pickup_service python -m app.core.db_rollback last

# 3. Reverter N Migrações
# Reverter últimas 3 migrações (simular)
#   docker exec -it order_pickup_service python -m app.core.db_rollback n 3 --dry-run
# Executar rollback real
#   docker exec -it order_pickup_service python -m app.core.db_rollback n 3

# 4. Reverter TODAS as Migrações ⚠️
# SIMULAR primeiro (NUNCA pule esta etapa!)
#   docker exec -it order_pickup_service python -m app.core.db_rollback all --dry-run
# Executar rollback completo (PERIGO - remove tabelas!)
#   docker exec -it order_pickup_service python -m app.core.db_rollback all --confirm

from __future__ import annotations
import logging
from typing import Any, Optional
from datetime import datetime, timezone
from sqlalchemy import inspect, text
from app.core.db import engine

logger = logging.getLogger("order_pickup_service.rollback")


# =============================================================================
# FUNÇÕES AUXILIARES
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


def _get_last_migration(conn: Any) -> Optional[str]:
    """Obtém última migração aplicada com sucesso."""
    result = conn.execute(
        text("""
            SELECT migration_name FROM migration_history
            WHERE success = TRUE
            ORDER BY applied_at DESC
            LIMIT 1
        """)
    ).fetchone()
    return result[0] if result else None


def _get_applied_migrations(conn: Any, limit: Optional[int] = None) -> list[str]:
    """Obtém lista de migrações aplicadas (mais recentes primeiro)."""
    query = """
        SELECT migration_name FROM migration_history
        WHERE success = TRUE
        ORDER BY applied_at DESC
    """
    if limit:
        query += f" LIMIT {limit}"
    result = conn.execute(text(query)).fetchall()
    return [row[0] for row in result]


def _mark_migration_rolled_back(conn: Any, migration_name: str) -> None:
    """Registra que migração foi revertida."""
    conn.execute(
        text("""
            INSERT INTO migration_history (migration_name, success, error_message)
            VALUES (:name, FALSE, :error)
        """),
        {"name": f"ROLLBACK:{migration_name}", "error": "Reverted by rollback script"}
    )


def _drop_column_if_exists(conn: Any, table: str, column: str) -> bool:
    """Remove coluna se existir."""
    inspector = inspect(conn)
    if _has_table(inspector, table) and _has_column(inspector, table, column):
        conn.execute(text(f"ALTER TABLE {table} DROP COLUMN IF EXISTS {column}"))
        logger.info(f"Coluna removida: {table}.{column}")
        return True
    return False


def _drop_index_if_exists(conn: Any, table: str, index_name: str) -> bool:
    """Remove índice se existir."""
    inspector = inspect(conn)
    if _has_table(inspector, table) and _has_index(inspector, table, index_name):
        conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
        logger.info(f"Índice removido: {index_name}")
        return True
    return False


def _drop_table_if_exists(conn: Any, table_name: str) -> bool:
    """Remove tabela se existir (com CASCADE para dependências)."""
    inspector = inspect(conn)
    if _has_table(inspector, table_name):
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
        logger.info(f"Tabela removida: {table_name}")
        return True
    return False


# =============================================================================
# ROLLBACK: ORDERS - COLUNAS
# =============================================================================

def _rollback_orders_columns(conn: Any) -> list[str]:
    """Reverte colunas adicionadas na tabela orders."""
    removed = []
    inspector = inspect(conn)
    
    if not _has_table(inspector, "orders"):
        logger.warning("Tabela orders não existe, pulando rollback de colunas")
        return removed
    
    # Colunas que podem ser removidas com segurança (não são PK/FK)
    columns_to_remove = [
        "currency",
        "site_id",
        "tenant_id",
        "ecommerce_partner_id",
        "partner_order_ref",
        "sku_description",
        "slot_size",
        "card_last4",
        "card_brand",
        "installments",
        "guest_name",
        "consent_analytics",
        "cancelled_at",
        "cancel_reason",
        "refunded_at",
        "refund_reason",
        "public_access_token_hash",
    ]
    
    for col_name in columns_to_remove:
        if _drop_column_if_exists(conn, "orders", col_name):
            removed.append(f"orders.{col_name}")
    
    return removed


# =============================================================================
# ROLLBACK: ORDERS - ÍNDICES
# =============================================================================

def _rollback_orders_indexes(conn: Any) -> list[str]:
    """Reverte índices adicionados na tabela orders."""
    removed = []
    inspector = inspect(conn)
    
    if not _has_table(inspector, "orders"):
        return removed
    
    indexes_to_remove = [
        "ix_orders_user_id",
        "ix_orders_ecommerce_partner",
        "ix_orders_pickup_deadline",
        "idx_orders_public_access_token_hash",
        "idx_orders_status",
        "idx_orders_channel_status",
        "idx_orders_region_status",
        "idx_orders_region_totem_status",
        "idx_orders_region_totem_created_at",
        "idx_orders_paid_at",
        "idx_orders_picked_up_at",
        "idx_orders_status_picked_up",
        "idx_orders_totem_picked_up",
    ]
    
    for idx_name in indexes_to_remove:
        if _drop_index_if_exists(conn, "orders", idx_name):
            removed.append(idx_name)
    
    return removed


# =============================================================================
# ROLLBACK: ALLOCATIONS
# =============================================================================

def _rollback_allocations(conn: Any) -> list[str]:
    """Reverte alterações na tabela allocations."""
    removed = []
    inspector = inspect(conn)
    
    if not _has_table(inspector, "allocations"):
        return removed
    
    # Colunas
    columns_to_remove = [
        "slot_size",
        "allocated_at",
        "released_at",
        "release_reason",
    ]
    
    for col_name in columns_to_remove:
        if _drop_column_if_exists(conn, "allocations", col_name):
            removed.append(f"allocations.{col_name}")
    
    # Índices
    indexes_to_remove = [
        "idx_allocations_order_id",
        "idx_allocations_state",
        "idx_allocations_locker_slot_state",
        "idx_allocations_created_at",
    ]
    
    for idx_name in indexes_to_remove:
        if _drop_index_if_exists(conn, "allocations", idx_name):
            removed.append(idx_name)
    
    return removed


# =============================================================================
# ROLLBACK: PICKUPS
# =============================================================================

def _rollback_pickups(conn: Any) -> list[str]:
    """Reverte alterações na tabela pickups."""
    removed = []
    inspector = inspect(conn)
    
    if not _has_table(inspector, "pickups"):
        return removed
    
    # Colunas
    columns_to_remove = [
        "channel",
        "locker_id",
        "machine_id",
        "slot",
        "operator_id",
        "tenant_id",
        "site_id",
        "lifecycle_stage",
        "activated_at",
        "ready_at",
        "door_opened_at",
        "item_removed_at",
        "door_closed_at",
        "expired_at",
        "cancelled_at",
        "cancel_reason",
        "correlation_id",
        "source_event_id",
        "sensor_event_id",
        "notes",
    ]
    
    for col_name in columns_to_remove:
        if _drop_column_if_exists(conn, "pickups", col_name):
            removed.append(f"pickups.{col_name}")
    
    # Índices
    indexes_to_remove = [
        "ix_pickups_order_id",
        "ix_pickups_status",
        "ix_pickups_channel_status",
        "ix_pickups_region_status",
        "ix_pickups_locker_status",
        "ix_pickups_machine_status",
        "ix_pickups_slot_status",
        "ix_pickups_operator_status",
        "ix_pickups_tenant_status",
        "ix_pickups_site_status",
        "ix_pickups_expires_at",
        "ix_pickups_redeemed_at",
        "ix_pickups_created_at",
        "ix_pickups_lifecycle_stage",
    ]
    
    for idx_name in indexes_to_remove:
        if _drop_index_if_exists(conn, "pickups", idx_name):
            removed.append(idx_name)
    
    return removed


# =============================================================================
# ROLLBACK: USERS
# =============================================================================

def _rollback_users(conn: Any) -> list[str]:
    """Reverte alterações na tabela users."""
    removed = []
    inspector = inspect(conn)
    
    if not _has_table(inspector, "users"):
        return removed
    
    # Colunas
    columns_to_remove = [
        "full_name",
        "phone",
        "password_hash",
        "is_active",
        "email_verified",
        "phone_verified",
        "locale",
        "totp_secret_ref",
        "totp_enabled",
        "anonymized_at",
    ]
    
    for col_name in columns_to_remove:
        if _drop_column_if_exists(conn, "users", col_name):
            removed.append(f"users.{col_name}")
    
    # Índices
    indexes_to_remove = [
        "ix_users_email",
        "ix_users_phone",
    ]
    
    for idx_name in indexes_to_remove:
        if _drop_index_if_exists(conn, "users", idx_name):
            removed.append(idx_name)
    
    return removed


# =============================================================================
# ROLLBACK: AUTH_SESSIONS
# =============================================================================

def _rollback_auth_sessions(conn: Any) -> list[str]:
    """Reverte alterações na tabela auth_sessions."""
    removed = []
    inspector = inspect(conn)
    
    if not _has_table(inspector, "auth_sessions"):
        return removed
    
    # Colunas
    columns_to_remove = [
        "user_agent",
        "ip_address",
        "revoked_at",
    ]
    
    for col_name in columns_to_remove:
        if _drop_column_if_exists(conn, "auth_sessions", col_name):
            removed.append(f"auth_sessions.{col_name}")
    
    # Índices
    indexes_to_remove = [
        "ix_auth_sessions_session_token_hash",
        "ix_auth_sessions_user_id",
    ]
    
    for idx_name in indexes_to_remove:
        if _drop_index_if_exists(conn, "auth_sessions", idx_name):
            removed.append(idx_name)
    
    return removed


# =============================================================================
# ROLLBACK: NOTIFICATION_LOGS
# =============================================================================

def _rollback_notification_logs(conn: Any) -> list[str]:
    """Reverte alterações na tabela notification_logs."""
    removed = []
    inspector = inspect(conn)
    
    if not _has_table(inspector, "notification_logs"):
        return removed
    
    # Colunas
    columns_to_remove = [
        "destination_value",
        "attempt_count",
        "payload_json",
        "dedupe_key",
        "processing_started_at",
        "last_attempt_at",
        "next_attempt_at",
        "pickup_id",
        "delivery_id",
        "rental_id",
        "locale",
        "provider_status",
        "error_detail",
    ]
    
    for col_name in columns_to_remove:
        if _drop_column_if_exists(conn, "notification_logs", col_name):
            removed.append(f"notification_logs.{col_name}")
    
    # Índices
    indexes_to_remove = [
        "ux_notification_logs_dedupe",
        "ix_notification_logs_next_attempt_at",
        "ix_notification_logs_status_next_attempt_at",
        "ix_notif_order",
        "ix_notif_pickup",
        "ix_notif_delivery",
        "ix_notif_next_attempt",
    ]
    
    for idx_name in indexes_to_remove:
        if _drop_index_if_exists(conn, "notification_logs", idx_name):
            removed.append(idx_name)
    
    return removed


# =============================================================================
# ROLLBACK: FISCAL_DOCUMENTS
# =============================================================================

def _rollback_fiscal_documents(conn: Any) -> list[str]:
    """Reverte alterações na tabela fiscal_documents."""
    removed = []
    inspector = inspect(conn)
    
    if not _has_table(inspector, "fiscal_documents"):
        return removed
    
    # Colunas
    columns_to_remove = [
        "tenant_id",
        "tax_amount_cents",
        "tax_breakdown_json",
        "sent_at",
        "printed_at",
        "xml_signed",
        "chave_acesso",
        "cancelled_at",
        "cancel_reason",
    ]
    
    for col_name in columns_to_remove:
        if _drop_column_if_exists(conn, "fiscal_documents", col_name):
            removed.append(f"fiscal_documents.{col_name}")
    
    return removed


# =============================================================================
# ROLLBACK: LOCKERS E CONFIGURAÇÕES
# =============================================================================

def _rollback_lockers(conn: Any) -> list[str]:
    """Reverte alterações nas tabelas de lockers."""
    removed = []
    inspector = inspect(conn)
    
    # Tabela lockers
    if _has_table(inspector, "lockers"):
        columns_to_remove = [
            "slots_available",
            "geolocation_wkt",
            "has_kiosk",
            "has_printer",
            "has_card_reader",
            "has_nfc",
        ]
        for col_name in columns_to_remove:
            if _drop_column_if_exists(conn, "lockers", col_name):
                removed.append(f"lockers.{col_name}")
        
        # Índices
        indexes_to_remove = [
            "idx_lockers_active",
            "idx_lockers_operator",
            "idx_lockers_region",
            "idx_lockers_site_id",
            "ix_lockers_tenant_id",
            "ix_lockers_machine_id",
            "ix_lockers_lat_lng",
        ]
        for idx_name in indexes_to_remove:
            if _drop_index_if_exists(conn, "lockers", idx_name):
                removed.append(idx_name)
    
    # Tabela locker_slot_configs
    if _has_table(inspector, "locker_slot_configs"):
        columns_to_remove = [
            "width_mm",
            "height_mm",
            "depth_mm",
            "max_weight_g",
        ]
        for col_name in columns_to_remove:
            if _drop_column_if_exists(conn, "locker_slot_configs", col_name):
                removed.append(f"locker_slot_configs.{col_name}")
        
        if _drop_index_if_exists(conn, "locker_slot_configs", "idx_locker_slot_locker"):
            removed.append("idx_locker_slot_locker")
    
    # Tabela locker_operators
    if _has_table(inspector, "locker_operators"):
        columns_to_remove = [
            "country",
            "contract_start_at",
            "contract_end_at",
            "contract_ref",
            "sla_pickup_hours",
            "sla_return_hours",
        ]
        for col_name in columns_to_remove:
            if _drop_column_if_exists(conn, "locker_operators", col_name):
                removed.append(f"locker_operators.{col_name}")
        
        if _drop_index_if_exists(conn, "locker_operators", "idx_operator_document"):
            removed.append("idx_operator_document")
    
    # Tabela product_categories
    if _has_table(inspector, "product_categories"):
        if _drop_column_if_exists(conn, "product_categories", "max_weight_g"):
            removed.append("product_categories.max_weight_g")
        
        if _drop_index_if_exists(conn, "product_categories", "idx_product_categories_parent"):
            removed.append("idx_product_categories_parent")
    
    # Tabela product_locker_configs
    if _has_table(inspector, "product_locker_configs"):
        columns_to_remove = [
            "min_value_cents",
            "max_value_cents",
            "max_weight_g",
            "max_width_mm",
            "max_height_mm",
            "max_depth_mm",
            "requires_id_check",
        ]
        for col_name in columns_to_remove:
            if _drop_column_if_exists(conn, "product_locker_configs", col_name):
                removed.append(f"product_locker_configs.{col_name}")
        
        indexes_to_remove = [
            "idx_product_config_locker",
            "idx_product_config_category",
            "uq_locker_category",
        ]
        for idx_name in indexes_to_remove:
            if _drop_index_if_exists(conn, "product_locker_configs", idx_name):
                removed.append(idx_name)
    
    return removed


# =============================================================================
# ROLLBACK: CAPABILITY CATALOG (14 TABELAS)
# =============================================================================

def _rollback_capability_catalog(conn: Any) -> list[str]:
    """Remove tabelas do Capability Catalog (ordem inversa de dependência)."""
    removed = []
    inspector = inspect(conn)
    
    # Ordem inversa de criação (dependências primeiro)
    tables_to_drop = [
        "capability_profile_snapshot",
        "capability_profile_target",
        "capability_profile_constraint",
        "capability_profile_action",
        "capability_profile_method_requirement",
        "capability_profile_method_interface",
        "capability_profile_method",
        "capability_profile",
        "capability_requirement_catalog",
        "wallet_provider_catalog",
        "payment_interface_catalog",
        "payment_method_catalog",
        "capability_context",
        "capability_channel",
        "capability_region",
    ]
    
    for table_name in tables_to_drop:
        if _drop_table_if_exists(conn, table_name):
            removed.append(f"{table_name}.drop")
    
    return removed


# =============================================================================
# ROLLBACK: DOMAIN EVENT OUTBOX
# =============================================================================

def _rollback_domain_event_outbox(conn: Any) -> list[str]:
    """Remove tabela domain_event_outbox."""
    removed = []
    inspector = inspect(conn)
    
    if _drop_table_if_exists(conn, "domain_event_outbox"):
        removed.append("domain_event_outbox.drop")
    
    return removed


# =============================================================================
# ROLLBACK: PICKUP_TOKENS
# =============================================================================

def _rollback_pickup_tokens(conn: Any) -> list[str]:
    """Remove tabela pickup_tokens."""
    removed = []
    inspector = inspect(conn)
    
    if _has_table(inspector, "pickup_tokens"):
        indexes_to_remove = [
            "ix_pickup_tokens_token_hash",
            "ix_pickup_tokens_pickup_id",
        ]
        for idx_name in indexes_to_remove:
            if _drop_index_if_exists(conn, "pickup_tokens", idx_name):
                removed.append(idx_name)
        
        if _drop_table_if_exists(conn, "pickup_tokens"):
            removed.append("pickup_tokens.drop")
    
    return removed


# =============================================================================
# ROLLBACK: CREDIT
# =============================================================================

def _rollback_credit(conn: Any) -> list[str]:
    """Remove tabela credit."""
    removed = []
    inspector = inspect(conn)
    
    if _has_table(inspector, "credit"):
        if _drop_index_if_exists(conn, "credit", "ix_credit_user_id"):
            removed.append("ix_credit_user_id")
        
        if _drop_table_if_exists(conn, "credit"):
            removed.append("credit.drop")
    
    return removed


# =============================================================================
# ROLLBACK: KIOSK_ANTIFRAUD_EVENT
# =============================================================================

def _rollback_kiosk_antifraud_event(conn: Any) -> list[str]:
    """Remove tabela kiosk_antifraud_event."""
    removed = []
    inspector = inspect(conn)
    
    if _has_table(inspector, "kiosk_antifraud_event"):
        indexes_to_remove = [
            "ix_kiosk_antifraud_kiosk_id",
            "ix_kiosk_antifraud_created_at",
        ]
        for idx_name in indexes_to_remove:
            if _drop_index_if_exists(conn, "kiosk_antifraud_event", idx_name):
                removed.append(idx_name)
        
        if _drop_table_if_exists(conn, "kiosk_antifraud_event"):
            removed.append("kiosk_antifraud_event.drop")
    
    return removed


# =============================================================================
# ROLLBACK: LOGIN_OTP
# =============================================================================

def _rollback_login_otp(conn: Any) -> list[str]:
    """Remove tabela login_otp."""
    removed = []
    inspector = inspect(conn)
    
    if _has_table(inspector, "login_otp"):
        if _drop_index_if_exists(conn, "login_otp", "ix_login_otp_user_id"):
            removed.append("ix_login_otp_user_id")
        
        if _drop_table_if_exists(conn, "login_otp"):
            removed.append("login_otp.drop")
    
    return removed


# =============================================================================
# ROLLBACK: MIGRATION_HISTORY (último registro)
# =============================================================================

def _rollback_migration_history_entry(conn: Any, migration_name: str) -> bool:
    """Remove último registro de migração aplicada."""
    conn.execute(
        text("""
            DELETE FROM migration_history
            WHERE migration_name = :name
            AND success = TRUE
        """),
        {"name": migration_name}
    )
    logger.info(f"Registro de migração removido: {migration_name}")
    return True


# =============================================================================
# MAPA DE ROLLBACK POR MIGRAÇÃO
# =============================================================================

ROLLBACK_MAP = {
    "migration_history_table": lambda conn: [],  # Não remover, é essencial
    "orders_columns": _rollback_orders_columns,
    "orders_indexes": _rollback_orders_indexes,
    "allocations": _rollback_allocations,
    "pickups": _rollback_pickups,
    "users": _rollback_users,
    "auth_sessions": _rollback_auth_sessions,
    "notification_logs": _rollback_notification_logs,
    "fiscal_documents": _rollback_fiscal_documents,
    "lockers": _rollback_lockers,
    "capability_catalog": _rollback_capability_catalog,
    "domain_event_outbox": _rollback_domain_event_outbox,
    "pickup_tokens": _rollback_pickup_tokens,
    "credit": _rollback_credit,
    "kiosk_antifraud_event": _rollback_kiosk_antifraud_event,
    "login_otp": _rollback_login_otp,
}


# =============================================================================
# FUNÇÕES PRINCIPAIS DE ROLLBACK
# =============================================================================

def rollback_last_migration(dry_run: bool = False) -> dict[str, Any]:
    """
    Reverte a última migração aplicada.
    
    Args:
        dry_run: Se True, apenas simula sem aplicar mudanças
    
    Returns:
        Dicionário com status e detalhes do rollback
    """
    result = {
        "ok": False,
        "migration_rolled_back": None,
        "actions": [],
        "errors": [],
        "dry_run": dry_run,
    }
    
    try:
        with engine.begin() as conn:
            # Verifica se migration_history existe
            inspector = inspect(conn)
            if not _has_table(inspector, "migration_history"):
                result["errors"].append("Tabela migration_history não existe")
                return result
            
            # Obtém última migração
            last_migration = _get_last_migration(conn)
            if not last_migration:
                result["errors"].append("Nenhuma migração para reverter")
                return result
            
            result["migration_rolled_back"] = last_migration
            
            if dry_run:
                logger.info(f"[DRY RUN] Rollback de: {last_migration}")
                result["ok"] = True
                return result
            
            # Executa rollback
            if last_migration in ROLLBACK_MAP:
                logger.info(f"Revertendo migração: {last_migration}")
                actions = ROLLBACK_MAP[last_migration](conn)
                result["actions"] = actions
                
                # Remove registro da migration_history
                _rollback_migration_history_entry(conn, last_migration)
                _mark_migration_rolled_back(conn, last_migration)
                
                result["ok"] = True
                logger.info(f"Rollback concluído: {last_migration}")
            else:
                result["errors"].append(f"Rollback não implementado para: {last_migration}")
    
    except Exception as e:
        result["errors"].append(str(e))
        logger.error(f"Erro no rollback: {str(e)}")
    
    return result


def rollback_n_migrations(n: int, dry_run: bool = False) -> dict[str, Any]:
    """
    Reverte as últimas N migrações aplicadas.
    
    Args:
        n: Número de migrações para reverter
        dry_run: Se True, apenas simula sem aplicar mudanças
    
    Returns:
        Dicionário com status e detalhes do rollback
    """
    result = {
        "ok": False,
        "migrations_rolled_back": [],
        "total_actions": 0,
        "errors": [],
        "dry_run": dry_run,
    }
    
    try:
        with engine.begin() as conn:
            # Verifica se migration_history existe
            inspector = inspect(conn)
            if not _has_table(inspector, "migration_history"):
                result["errors"].append("Tabela migration_history não existe")
                return result
            
            # Obtém últimas N migrações
            migrations = _get_applied_migrations(conn, limit=n)
            if not migrations:
                result["errors"].append("Nenhuma migração para reverter")
                return result
            
            if dry_run:
                logger.info(f"[DRY RUN] Rollback de {len(migrations)} migrações:")
                for m in migrations:
                    logger.info(f"  - {m}")
                result["ok"] = True
                result["migrations_rolled_back"] = migrations
                return result
            
            # Executa rollback em cada migração (ordem inversa)
            for migration_name in migrations:
                logger.info(f"Revertendo migração: {migration_name}")
                
                if migration_name in ROLLBACK_MAP:
                    actions = ROLLBACK_MAP[migration_name](conn)
                    result["migrations_rolled_back"].append(migration_name)
                    result["total_actions"] += len(actions)
                    
                    # Remove registro da migration_history
                    _rollback_migration_history_entry(conn, migration_name)
                    _mark_migration_rolled_back(conn, migration_name)
                else:
                    result["errors"].append(f"Rollback não implementado para: {migration_name}")
            
            result["ok"] = len(result["errors"]) == 0
    
    except Exception as e:
        result["errors"].append(str(e))
        logger.error(f"Erro no rollback: {str(e)}")
    
    return result


def rollback_all_migrations(dry_run: bool = False, confirm: bool = False) -> dict[str, Any]:
    """
    Reverte TODAS as migrações aplicadas.
    ⚠️ USE COM EXTREMO CUIDADO - REMOVE TODAS AS TABELAS CUSTOMIZADAS
    
    Args:
        dry_run: Se True, apenas simula sem aplicar mudanças
        confirm: Se True, requer confirmação explícita
    
    Returns:
        Dicionário com status e detalhes do rollback
    """
    result = {
        "ok": False,
        "migrations_rolled_back": [],
        "total_actions": 0,
        "errors": [],
        "dry_run": dry_run,
        "warning": "⚠️ ESTE ROLLBACK REMOVE TODAS AS TABELAS CUSTOMIZADAS",
    }
    
    if not confirm and not dry_run:
        result["errors"].append(
            "Rollback all requer confirm=True. Use com extremo cuidado!"
        )
        return result
    
    try:
        with engine.begin() as conn:
            # Verifica se migration_history existe
            inspector = inspect(conn)
            if not _has_table(inspector, "migration_history"):
                result["errors"].append("Tabela migration_history não existe")
                return result
            
            # Obtém todas as migrações
            migrations = _get_applied_migrations(conn)
            if not migrations:
                result["errors"].append("Nenhuma migração para reverter")
                return result
            
            if dry_run:
                logger.info(f"[DRY RUN] Rollback de TODAS as {len(migrations)} migrações:")
                for m in migrations:
                    logger.info(f"  - {m}")
                result["ok"] = True
                result["migrations_rolled_back"] = migrations
                return result
            
            logger.warning(f"⚠️ INICIANDO ROLLBACK COMPLETO DE {len(migrations)} MIGRAÇÕES")
            
            # Executa rollback em cada migração (ordem inversa)
            for migration_name in migrations:
                logger.info(f"Revertendo migração: {migration_name}")
                
                if migration_name in ROLLBACK_MAP:
                    actions = ROLLBACK_MAP[migration_name](conn)
                    result["migrations_rolled_back"].append(migration_name)
                    result["total_actions"] += len(actions)
                    
                    # Remove registro da migration_history
                    _rollback_migration_history_entry(conn, migration_name)
                    _mark_migration_rolled_back(conn, migration_name)
                else:
                    result["errors"].append(f"Rollback não implementado para: {migration_name}")
            
            result["ok"] = len(result["errors"]) == 0
            logger.warning("⚠️ ROLLBACK COMPLETO CONCLUÍDO")
    
    except Exception as e:
        result["errors"].append(str(e))
        logger.error(f"Erro no rollback: {str(e)}")
    
    return result


def get_migration_status() -> dict[str, Any]:
    """
    Obtém status atual das migrações.
    
    Returns:
        Dicionário com status detalhado
    """
    result = {
        "total_migrations": 0,
        "successful": 0,
        "failed": 0,
        "last_migration": None,
        "recent_migrations": [],
    }
    
    try:
        with engine.connect() as conn:
            inspector = inspect(conn)
            if not _has_table(inspector, "migration_history"):
                result["error"] = "Tabela migration_history não existe"
                return result
            
            # Total
            total = conn.execute(
                text("SELECT COUNT(*) FROM migration_history")
            ).scalar()
            result["total_migrations"] = total or 0
            
            # Sucesso
            success = conn.execute(
                text("SELECT COUNT(*) FROM migration_history WHERE success = TRUE")
            ).scalar()
            result["successful"] = success or 0
            
            # Falhas
            failed = conn.execute(
                text("SELECT COUNT(*) FROM migration_history WHERE success = FALSE")
            ).scalar()
            result["failed"] = failed or 0
            
            # Última migração
            last = _get_last_migration(conn)
            result["last_migration"] = last
            
            # Últimas 10 migrações
            recent = _get_applied_migrations(conn, limit=10)
            result["recent_migrations"] = recent
    
    except Exception as e:
        result["error"] = str(e)
    
    return result


# =============================================================================
# EXECUÇÃO VIA CLI
# =============================================================================

if __name__ == "__main__":
    import sys
    import json
    
    print("=" * 80)
    print("🔄 ROLLBACK DE MIGRAÇÕES POSTGRESQL")
    print("=" * 80)
    
    if len(sys.argv) < 2:
        print("\nUso:")
        print("  python db_rollback.py last              - Reverte última migração")
        print("  python db_rollback.py last --dry-run    - Simula reversão da última")
        print("  python db_rollback.py n <quantidade>    - Reverte N migrações")
        print("  python db_rollback.py n <quantidade> --dry-run")
        print("  python db_rollback.py all --confirm     - Reverte TODAS (⚠️ PERIGOSO)")
        print("  python db_rollback.py all --dry-run     - Simula reversão de todas")
        print("  python db_rollback.py status            - Mostra status das migrações")
        sys.exit(1)
    
    command = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    confirm = "--confirm" in sys.argv
    
    if command == "status":
        result = get_migration_status()
        print("\n📊 STATUS DAS MIGRAÇÕES:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)
    
    elif command == "last":
        print(f"\n🔄 Revertendo última migração... (dry_run={dry_run})")
        result = rollback_last_migration(dry_run=dry_run)
    
    elif command == "n":
        if len(sys.argv) < 3:
            print("❌ Erro: Especifique quantidade (ex: n 3)")
            sys.exit(1)
        try:
            n = int(sys.argv[2])
        except ValueError:
            print("❌ Erro: Quantidade deve ser número inteiro")
            sys.exit(1)
        print(f"\n🔄 Revertendo {n} migrações... (dry_run={dry_run})")
        result = rollback_n_migrations(n, dry_run=dry_run)
    
    elif command == "all":
        if not confirm and not dry_run:
            print("\n⚠️  ATENÇÃO: Rollback completo requer --confirm")
            print("Isso removerá TODAS as tabelas customizadas do banco!")
            print("\nUse: python db_rollback.py all --confirm")
            sys.exit(1)
        print(f"\n⚠️  REVERTENDO TODAS AS MIGRAÇÕES... (dry_run={dry_run}, confirm={confirm})")
        result = rollback_all_migrations(dry_run=dry_run, confirm=confirm)
    
    else:
        print(f"❌ Comando desconhecido: {command}")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("📊 RESULTADO:")
    print("=" * 80)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    
    if result.get("ok"):
        print("\n✅ Rollback concluído com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Rollback falhou. Verifique os erros acima.")
        sys.exit(1)