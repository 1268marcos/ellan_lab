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
    """
    Valida o schema mínimo esperado pela versão atual do serviço.

    IMPORTANTE:
    - create_all() não faz migração de colunas novas em tabelas já existentes
    - create_all() não deve ser tratado como substituto de migration
    - se o schema estiver defasado, o serviço deve falhar no startup
    """
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
        "provider_name",
        "provider_message_id",
        "status",
        "error_message",
        "created_at",
        "sent_at",
        "delivered_at",
        "failed_at",
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

    # Nesta fase validamos índices apenas para tabelas cujo nome do índice
    # é criado explicitamente por migration. Para users/auth_sessions/notification_logs,
    # create_all() pode gerar nomes diferentes dependendo do banco/dialeto/modelo.
    orders_indexes = _get_indexes_set(inspector, "orders")
    allocations_indexes = _get_indexes_set(inspector, "allocations")

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
    }

    required_allocations_indexes = {
        "idx_allocations_order_id",
        "idx_allocations_state",
        "idx_allocations_locker_slot_state",
        "idx_allocations_created_at",
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


def _run_startup_migrations_if_enabled() -> None:
    if not settings.run_db_migrations_on_startup:
        logger.info(
            "RUN_DB_MIGRATIONS_ON_STARTUP=false; migrações automáticas não serão executadas."
        )
        return

    from app.core.db_migrations import migrate_order_pickup_schema

    logger.info("Executando migrações automáticas do order_pickup_service...")
    result = migrate_order_pickup_schema()

    applied = result.get("applied", []) if isinstance(result, dict) else []
    if applied:
        logger.info("Migrações aplicadas: %s", ", ".join(applied))
    else:
        logger.info("Nenhuma migração pendente foi aplicada.")


def init_db():
    """
    Bootstrap inicial + migração opcional + validação de schema.

    Regras:
    - create_all() serve apenas para criação inicial
    - tabelas já existentes NÃO são migradas por create_all()
    - migração automática só roda se RUN_DB_MIGRATIONS_ON_STARTUP=true
    - após bootstrap/migração, validamos o schema exigido pela versão atual do serviço
    """
    from app.models import allocation  # noqa: F401
    from app.models import credit  # noqa: F401
    from app.models import kiosk_antifraud_event  # noqa: F401
    from app.models import login_otp  # noqa: F401
    from app.models import order  # noqa: F401
    from app.models import pickup  # noqa: F401
    from app.models import pickup_token  # noqa: F401
    from app.models import user  # noqa: F401
    from app.models.auth_session import AuthSession  # noqa: F401
    from app.models.notification_log import NotificationLog  # noqa: F401
    from app.models import domain_event_outbox  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _run_startup_migrations_if_enabled()
    _assert_required_schema()