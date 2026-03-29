# 01_source/order_pickup_service/app/core/db.py
import logging

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

logger = logging.getLogger("order_pickup_service.db")


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_columns_map(inspector, table_name: str) -> dict[str, dict]:
    return {col["name"]: col for col in inspector.get_columns(table_name)}


def _get_indexes_set(inspector, table_name: str) -> set[str]:
    return {idx["name"] for idx in inspector.get_indexes(table_name)}


def _assert_required_schema() -> None:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    required_tables = {
        "orders",
        "allocations",
        "pickups",
        "pickup_tokens",
        "users",
        "auth_sessions",
        "notification_logs",
        "fiscal_documents",
        # Novas tabelas de lockers
        "lockers",
        "locker_slot_configs",
        "locker_operators",
        "product_locker_configs",
        "product_categories",
    }

    missing_tables = sorted(required_tables - tables)
    if missing_tables:
        raise RuntimeError(
            "Schema incompatível: tabelas obrigatórias ausentes: "
            + ", ".join(missing_tables)
        )

    orders_columns = _get_columns_map(inspector, "orders")
    allocations_columns = _get_columns_map(inspector, "allocations")
    users_columns = _get_columns_map(inspector, "users")
    auth_sessions_columns = _get_columns_map(inspector, "auth_sessions")
    notification_logs_columns = _get_columns_map(inspector, "notification_logs")
    fiscal_documents_columns = _get_columns_map(inspector, "fiscal_documents")
    lockers_columns = _get_columns_map(inspector, "lockers")
    locker_slot_configs_columns = _get_columns_map(inspector, "locker_slot_configs")
    locker_operators_columns = _get_columns_map(inspector, "locker_operators")
    product_locker_configs_columns = _get_columns_map(inspector, "product_locker_configs")
    product_categories_columns = _get_columns_map(inspector, "product_categories")

    required_orders_columns = {
        "id",
        "user_id",
        "channel",
        "region",
        "totem_id",
        "sku_id",
        "amount_cents",
        "status",
        "gateway_transaction_id",
        "payment_method",
        "payment_status",
        "card_type",
        "payment_updated_at",
        "paid_at",
        "pickup_deadline_at",
        "picked_up_at",
        "guest_session_id",
        "receipt_email",
        "receipt_phone",
        "consent_marketing",
        "guest_phone",
        "guest_email",
        "created_at",
        "updated_at",
        "public_access_token_hash",
    }

    required_allocations_columns = {
        "id",
        "order_id",
        "locker_id",
        "slot",
        "state",
        "locked_until",
        "created_at",
        "updated_at",
    }

    required_users_columns = {
        "id",
        "full_name",
        "email",
        "phone",
        "password_hash",
        "is_active",
        "email_verified",
        "phone_verified",
        "created_at",
        "updated_at",
    }

    required_auth_sessions_columns = {
        "id",
        "user_id",
        "session_token_hash",
        "user_agent",
        "ip_address",
        "created_at",
        "expires_at",
        "revoked_at",
    }

    required_notification_logs_columns = {
        "id",
        "user_id",
        "order_id",
        "channel",
        "template_key",
        "destination_masked",
        "destination_value",
        "dedupe_key",
        "provider_name",
        "provider_message_id",
        "status",
        "attempt_count",
        "error_message",
        "payload_json",
        "processing_started_at",
        "last_attempt_at",
        "next_attempt_at",
        "created_at",
        "sent_at",
        "delivered_at",
        "failed_at",
    }

    required_fiscal_documents_columns = {
        "id",
        "order_id",
        "receipt_code",
        "document_type",
        "channel",
        "region",
        "amount_cents",
        "currency",
        "delivery_mode",
        "send_status",
        "send_target",
        "print_status",
        "print_site_path",
        "payload_json",
        "issued_at",
        "created_at",
        "updated_at",
    }

    required_lockers_columns = {
        "id",
        "external_id",
        "display_name",
        "description",
        "region",
        "site_id",
        "timezone",
        "address_line",
        "address_number",
        "address_extra",
        "district",
        "city",
        "state",
        "postal_code",
        "country",
        "latitude",
        "longitude",
        "active",
        "slots_count",
        "machine_id",
        "allowed_channels",
        "allowed_payment_methods",
        "temperature_zone",
        "security_level",
        "has_camera",
        "has_alarm",
        "access_hours",
        "operator_id",
        "tenant_id",
        "is_rented",
        "metadata_json",
        "created_at",
        "updated_at",
    }

    required_locker_slot_configs_columns = {
        "id",
        "locker_id",
        "slot_size",
        "slot_count",
        "available_count",
        "width_cm",
        "height_cm",
        "depth_cm",
        "max_weight_kg",
        "created_at",
        "updated_at",
    }

    required_locker_operators_columns = {
        "id",
        "name",
        "document",
        "email",
        "phone",
        "operator_type",
        "active",
        "commission_rate",
        "currency",
        "created_at",
        "updated_at",
    }

    required_product_locker_configs_columns = {
        "id",
        "locker_id",
        "category",
        "subcategory",
        "allowed",
        "temperature_zone",
        "min_value",
        "max_value",
        "max_weight_kg",
        "max_width_cm",
        "max_height_cm",
        "max_depth_cm",
        "requires_signature",
        "requires_id",
        "is_fragile",
        "is_hazardous",
        "priority",
        "notes",
        "created_at",
        "updated_at",
    }

    required_product_categories_columns = {
        "id",
        "name",
        "description",
        "parent_category",
        "default_temperature_zone",
        "default_security_level",
        "is_hazardous",
        "requires_age_verification",
        "created_at",
        "updated_at",
    }

    missing_orders_columns = sorted(required_orders_columns - set(orders_columns.keys()))
    if missing_orders_columns:
        raise RuntimeError(
            "Schema incompatível em orders: colunas ausentes: "
            + ", ".join(missing_orders_columns)
        )

    missing_allocations_columns = sorted(
        required_allocations_columns - set(allocations_columns.keys())
    )
    if missing_allocations_columns:
        raise RuntimeError(
            "Schema incompatível em allocations: colunas ausentes: "
            + ", ".join(missing_allocations_columns)
        )

    missing_users_columns = sorted(required_users_columns - set(users_columns.keys()))
    if missing_users_columns:
        raise RuntimeError(
            "Schema incompatível em users: colunas ausentes: "
            + ", ".join(missing_users_columns)
        )

    missing_auth_sessions_columns = sorted(
        required_auth_sessions_columns - set(auth_sessions_columns.keys())
    )
    if missing_auth_sessions_columns:
        raise RuntimeError(
            "Schema incompatível em auth_sessions: colunas ausentes: "
            + ", ".join(missing_auth_sessions_columns)
        )

    missing_notification_logs_columns = sorted(
        required_notification_logs_columns - set(notification_logs_columns.keys())
    )
    if missing_notification_logs_columns:
        raise RuntimeError(
            "Schema incompatível em notification_logs: colunas ausentes: "
            + ", ".join(missing_notification_logs_columns)
        )

    missing_fiscal_documents_columns = sorted(
        required_fiscal_documents_columns - set(fiscal_documents_columns.keys())
    )
    if missing_fiscal_documents_columns:
        raise RuntimeError(
            "Schema incompatível em fiscal_documents: colunas ausentes: "
            + ", ".join(missing_fiscal_documents_columns)
        )

    missing_lockers_columns = sorted(
        required_lockers_columns - set(lockers_columns.keys())
    )
    if missing_lockers_columns:
        raise RuntimeError(
            "Schema incompatível em lockers: colunas ausentes: "
            + ", ".join(missing_lockers_columns)
        )

    missing_locker_slot_configs_columns = sorted(
        required_locker_slot_configs_columns - set(locker_slot_configs_columns.keys())
    )
    if missing_locker_slot_configs_columns:
        raise RuntimeError(
            "Schema incompatível em locker_slot_configs: colunas ausentes: "
            + ", ".join(missing_locker_slot_configs_columns)
        )

    missing_locker_operators_columns = sorted(
        required_locker_operators_columns - set(locker_operators_columns.keys())
    )
    if missing_locker_operators_columns:
        raise RuntimeError(
            "Schema incompatível em locker_operators: colunas ausentes: "
            + ", ".join(missing_locker_operators_columns)
        )

    missing_product_locker_configs_columns = sorted(
        required_product_locker_configs_columns - set(product_locker_configs_columns.keys())
    )
    if missing_product_locker_configs_columns:
        raise RuntimeError(
            "Schema incompatível em product_locker_configs: colunas ausentes: "
            + ", ".join(missing_product_locker_configs_columns)
        )

    missing_product_categories_columns = sorted(
        required_product_categories_columns - set(product_categories_columns.keys())
    )
    if missing_product_categories_columns:
        raise RuntimeError(
            "Schema incompatível em product_categories: colunas ausentes: "
            + ", ".join(missing_product_categories_columns)
        )

    orders_indexes = _get_indexes_set(inspector, "orders")
    allocations_indexes = _get_indexes_set(inspector, "allocations")
    notification_logs_indexes = _get_indexes_set(inspector, "notification_logs")
    lockers_indexes = _get_indexes_set(inspector, "lockers")
    locker_slot_configs_indexes = _get_indexes_set(inspector, "locker_slot_configs")
    locker_operators_indexes = _get_indexes_set(inspector, "locker_operators")
    product_locker_configs_indexes = _get_indexes_set(inspector, "product_locker_configs")
    product_categories_indexes = _get_indexes_set(inspector, "product_categories")

    required_orders_indexes = {
        "idx_orders_status",
        "idx_orders_channel_status",
        "idx_orders_region_status",
        "idx_orders_region_totem_status",
        "idx_orders_region_totem_created_at",
        "idx_orders_paid_at",
        "idx_orders_picked_up_at",
        "idx_orders_status_picked_up",
        "idx_orders_totem_picked_up",
        "idx_orders_public_access_token_hash",
    }

    required_allocations_indexes = {
        "idx_allocations_order_id",
        "idx_allocations_state",
        "idx_allocations_locker_slot_state",
        "idx_allocations_created_at",
    }

    required_notification_logs_indexes = {
        "ux_notification_logs_dedupe",
        "ix_notification_logs_next_attempt_at",
        "ix_notification_logs_status_next_attempt_at",
    }

    required_lockers_indexes = {
        "idx_lockers_region",
        "idx_lockers_site_id",
        "idx_lockers_active",
        "idx_lockers_operator",
    }

    required_locker_slot_configs_indexes = {
        "idx_locker_slot_locker",
    }

    required_locker_operators_indexes = {
        "idx_operator_document",
    }

    required_product_locker_configs_indexes = {
        "idx_product_config_locker",
        "idx_product_config_category",
    }

    required_product_categories_indexes = {
        "idx_product_categories_parent",
    }

    missing_orders_indexes = sorted(required_orders_indexes - orders_indexes)
    if missing_orders_indexes:
        raise RuntimeError(
            "Schema incompatível em orders: índices ausentes: "
            + ", ".join(missing_orders_indexes)
        )

    missing_allocations_indexes = sorted(required_allocations_indexes - allocations_indexes)
    if missing_allocations_indexes:
        raise RuntimeError(
            "Schema incompatível em allocations: índices ausentes: "
            + ", ".join(missing_allocations_indexes)
        )

    missing_notification_logs_indexes = sorted(
        required_notification_logs_indexes - notification_logs_indexes
    )
    if missing_notification_logs_indexes:
        raise RuntimeError(
            "Schema incompatível em notification_logs: índices ausentes: "
            + ", ".join(missing_notification_logs_indexes)
        )

    missing_lockers_indexes = sorted(required_lockers_indexes - lockers_indexes)
    if missing_lockers_indexes:
        raise RuntimeError(
            "Schema incompatível em lockers: índices ausentes: "
            + ", ".join(missing_lockers_indexes)
        )

    missing_locker_slot_configs_indexes = sorted(
        required_locker_slot_configs_indexes - locker_slot_configs_indexes
    )
    if missing_locker_slot_configs_indexes:
        raise RuntimeError(
            "Schema incompatível em locker_slot_configs: índices ausentes: "
            + ", ".join(missing_locker_slot_configs_indexes)
        )

    missing_locker_operators_indexes = sorted(
        required_locker_operators_indexes - locker_operators_indexes
    )
    if missing_locker_operators_indexes:
        raise RuntimeError(
            "Schema incompatível em locker_operators: índices ausentes: "
            + ", ".join(missing_locker_operators_indexes)
        )

    missing_product_locker_configs_indexes = sorted(
        required_product_locker_configs_indexes - product_locker_configs_indexes
    )
    if missing_product_locker_configs_indexes:
        raise RuntimeError(
            "Schema incompatível em product_locker_configs: índices ausentes: "
            + ", ".join(missing_product_locker_configs_indexes)
        )

    missing_product_categories_indexes = sorted(
        required_product_categories_indexes - product_categories_indexes
    )
    if missing_product_categories_indexes:
        raise RuntimeError(
            "Schema incompatível em product_categories: índices ausentes: "
            + ", ".join(missing_product_categories_indexes)
        )


def _run_startup_migrations_if_enabled() -> None:
    if not settings.run_db_migrations_on_startup:
        logger.info(
            "RUN_DB_MIGRATIONS_ON_STARTUP=false; migrações automáticas não serão executadas."
        )
        return

    from app.core.db_migrations import _run_startup_migrations_if_enabled as run_all_startup_migrations

    logger.info("Executando migrações automáticas do order_pickup_service...")
    result = run_all_startup_migrations()

    applied = result.get("applied", []) if isinstance(result, dict) else []
    if applied:
        logger.info("Migrações aplicadas: %s", ", ".join(applied))
    else:
        logger.info("Nenhuma migração pendente foi aplicada.")


def init_db():
    # =========================
    # IMPORTS EXPLÍCITOS (CRÍTICO)
    # =========================
    from app.models.allocation import Allocation  # noqa: F401
    from app.models.credit import Credit  # noqa: F401
    from app.models.kiosk_antifraud_event import KioskAntifraudEvent  # noqa: F401
    from app.models.login_otp import LoginOTP  # noqa: F401
    from app.models.order import Order  # noqa: F401
    from app.models.pickup import Pickup  # noqa: F401
    from app.models.pickup_token import PickupToken  # noqa: F401
    from app.models.user import User  # noqa: F401
    from app.models.auth_session import AuthSession  # noqa: F401
    from app.models.notification_log import NotificationLog  # noqa: F401
    from app.models.domain_event_outbox import DomainEventOutbox  # noqa: F401
    from app.models.fiscal_document import FiscalDocument  # noqa: F401

    # 🔥 LOCKERS (EXPLÍCITO — ESSENCIAL)
    from app.models.locker import Locker, LockerSlotConfig, LockerOperator  # noqa: F401

    # 🔥 PRODUCT CONFIG
    from app.models.product_locker_config import ProductLockerConfig, ProductCategory  # noqa: F401

    # =========================
    # 1. MIGRATIONS PRIMEIRO
    # =========================
    _run_startup_migrations_if_enabled()

    # =========================
    # 2. CREATE TABLES (fallback)
    # =========================
    # Base.metadata.create_all(bind=engine)

    # =========================
    # 3. VALIDAR SCHEMA
    # =========================
    _assert_required_schema()