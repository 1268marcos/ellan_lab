# 01_source/order_pickup_service/app/core/db_migrations.py

from __future__ import annotations

from sqlalchemy import inspect, text

from app.core.db import engine


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    cols = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in cols)


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    indexes = inspector.get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def _sqlite_table_sql(conn, table_name: str) -> str | None:
    row = conn.execute(
        text(
            """
            SELECT sql
              FROM sqlite_master
             WHERE type = 'table'
               AND name = :table_name
            """
        ),
        {"table_name": table_name},
    ).fetchone()
    return row[0] if row and row[0] else None


def _normalize_sql(sql: str | None) -> str:
    return " ".join((sql or "").lower().split())


def _sqlite_users_id_needs_rebuild_to_text(conn) -> bool:
    sql = _normalize_sql(_sqlite_table_sql(conn, "users"))
    if not sql:
        return False

    return "id varchar(36)" not in sql and "id text" not in sql and "id varchar" not in sql


def _sqlite_orders_user_id_needs_rebuild_to_text(conn) -> bool:
    sql = _normalize_sql(_sqlite_table_sql(conn, "orders"))
    if not sql:
        return False

    return "user_id varchar(36)" not in sql and "user_id text" not in sql and "user_id varchar" not in sql


def _sqlite_auth_sessions_user_id_needs_rebuild_to_text(conn) -> bool:
    sql = _normalize_sql(_sqlite_table_sql(conn, "auth_sessions"))
    if not sql:
        return False

    return "user_id varchar(36)" not in sql and "user_id text" not in sql and "user_id varchar" not in sql


def _sqlite_pickups_needs_rebuild_for_final_model(conn) -> bool:
    sql = _normalize_sql(_sqlite_table_sql(conn, "pickups"))
    if not sql:
        return False

    required_fragments = [
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

    return not all(fragment in sql for fragment in required_fragments)


def _rebuild_users_sqlite_to_text_id(conn, applied: list[str]) -> None:
    inspector = inspect(conn)
    existing = {col["name"] for col in inspector.get_columns("users")}

    conn.execute(text("PRAGMA foreign_keys=OFF"))

    conn.execute(
        text(
            """
            CREATE TABLE users_new (
                id VARCHAR(36) NOT NULL PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                phone VARCHAR(32) NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_active BOOLEAN NOT NULL,
                email_verified BOOLEAN NOT NULL,
                phone_verified BOOLEAN NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
    )

    full_name_expr = (
        "full_name"
        if "full_name" in existing
        else ("name" if "name" in existing else "email")
    )
    phone_expr = "phone" if "phone" in existing else "NULL"
    password_hash_expr = "password_hash" if "password_hash" in existing else "''"
    is_active_expr = "COALESCE(is_active, 1)" if "is_active" in existing else "1"
    email_verified_expr = (
        "COALESCE(email_verified, 0)" if "email_verified" in existing else "0"
    )
    phone_verified_expr = (
        "COALESCE(phone_verified, 0)" if "phone_verified" in existing else "0"
    )
    created_at_expr = "COALESCE(created_at, CURRENT_TIMESTAMP)" if "created_at" in existing else "CURRENT_TIMESTAMP"
    updated_at_expr = "COALESCE(updated_at, CURRENT_TIMESTAMP)" if "updated_at" in existing else "CURRENT_TIMESTAMP"

    conn.execute(
        text(
            f"""
            INSERT INTO users_new (
                id,
                full_name,
                email,
                phone,
                password_hash,
                is_active,
                email_verified,
                phone_verified,
                created_at,
                updated_at
            )
            SELECT
                CAST(id AS TEXT),
                {full_name_expr},
                email,
                {phone_expr},
                {password_hash_expr},
                {is_active_expr},
                {email_verified_expr},
                {phone_verified_expr},
                {created_at_expr},
                {updated_at_expr}
            FROM users
            """
        )
    )

    conn.execute(text("DROP TABLE users"))
    conn.execute(text("ALTER TABLE users_new RENAME TO users"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_phone ON users (phone)"))
    conn.execute(text("PRAGMA foreign_keys=ON"))

    applied.append("users.sqlite_table_rebuild_text_id")


def _rebuild_orders_sqlite_user_id_to_text(conn, applied: list[str]) -> None:
    inspector = inspect(conn)
    existing = {col["name"] for col in inspector.get_columns("orders")}

    conn.execute(text("PRAGMA foreign_keys=OFF"))

    conn.execute(
        text(
            """
            CREATE TABLE orders_new (
                id VARCHAR NOT NULL PRIMARY KEY,
                user_id VARCHAR(36) NULL,
                channel VARCHAR(6) NOT NULL,
                region VARCHAR NOT NULL,
                totem_id VARCHAR NOT NULL,
                sku_id VARCHAR NOT NULL,
                amount_cents INTEGER NOT NULL,
                status VARCHAR(18) NOT NULL,
                gateway_transaction_id VARCHAR NULL,
                payment_method VARCHAR(21) NULL,
                payment_status VARCHAR(30) NOT NULL,
                card_type VARCHAR(10) NULL,
                payment_updated_at DATETIME NULL,
                paid_at DATETIME NULL,
                pickup_deadline_at DATETIME NULL,
                picked_up_at DATETIME NULL,
                guest_session_id VARCHAR NULL,
                receipt_email VARCHAR NULL,
                receipt_phone VARCHAR NULL,
                consent_marketing INTEGER NOT NULL,
                guest_phone VARCHAR NULL,
                guest_email VARCHAR NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
        )
    )

    gateway_transaction_id_expr = (
        "gateway_transaction_id" if "gateway_transaction_id" in existing else "NULL"
    )
    payment_method_expr = "payment_method" if "payment_method" in existing else "NULL"
    payment_status_expr = (
        "COALESCE(payment_status, 'CREATED')" if "payment_status" in existing else "'CREATED'"
    )
    card_type_expr = "card_type" if "card_type" in existing else "NULL"
    payment_updated_at_expr = (
        "payment_updated_at" if "payment_updated_at" in existing else "NULL"
    )
    paid_at_expr = "paid_at" if "paid_at" in existing else "NULL"
    pickup_deadline_at_expr = (
        "pickup_deadline_at" if "pickup_deadline_at" in existing else "NULL"
    )
    picked_up_at_expr = "picked_up_at" if "picked_up_at" in existing else "NULL"
    guest_session_id_expr = (
        "guest_session_id" if "guest_session_id" in existing else "NULL"
    )
    receipt_email_expr = "receipt_email" if "receipt_email" in existing else "NULL"
    receipt_phone_expr = "receipt_phone" if "receipt_phone" in existing else "NULL"
    consent_marketing_expr = (
        "COALESCE(consent_marketing, 0)" if "consent_marketing" in existing else "0"
    )
    guest_phone_expr = "guest_phone" if "guest_phone" in existing else "NULL"
    guest_email_expr = "guest_email" if "guest_email" in existing else "NULL"
    updated_at_expr = "COALESCE(updated_at, created_at)" if "updated_at" in existing else "created_at"

    conn.execute(
        text(
            f"""
            INSERT INTO orders_new (
                id,
                user_id,
                channel,
                region,
                totem_id,
                sku_id,
                amount_cents,
                status,
                gateway_transaction_id,
                payment_method,
                payment_status,
                card_type,
                payment_updated_at,
                paid_at,
                pickup_deadline_at,
                picked_up_at,
                guest_session_id,
                receipt_email,
                receipt_phone,
                consent_marketing,
                guest_phone,
                guest_email,
                created_at,
                updated_at
            )
            SELECT
                id,
                CASE
                    WHEN user_id IS NULL THEN NULL
                    ELSE CAST(user_id AS TEXT)
                END,
                channel,
                region,
                totem_id,
                sku_id,
                amount_cents,
                status,
                {gateway_transaction_id_expr},
                {payment_method_expr},
                {payment_status_expr},
                {card_type_expr},
                {payment_updated_at_expr},
                {paid_at_expr},
                {pickup_deadline_at_expr},
                {picked_up_at_expr},
                {guest_session_id_expr},
                {receipt_email_expr},
                {receipt_phone_expr},
                {consent_marketing_expr},
                {guest_phone_expr},
                {guest_email_expr},
                created_at,
                {updated_at_expr}
            FROM orders
            """
        )
    )

    conn.execute(text("DROP TABLE orders"))
    conn.execute(text("ALTER TABLE orders_new RENAME TO orders"))

    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_channel_status ON orders (channel, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_region_status ON orders (region, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_region_totem_status ON orders (region, totem_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_region_totem_created_at ON orders (region, totem_id, created_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_paid_at ON orders (paid_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_picked_up_at ON orders (picked_up_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_status_picked_up ON orders (status, picked_up_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_totem_picked_up ON orders (totem_id, picked_up_at)"))

    conn.execute(text("PRAGMA foreign_keys=ON"))

    applied.append("orders.sqlite_table_rebuild_user_id_text")


def _rebuild_auth_sessions_sqlite_user_id_to_text(conn, applied: list[str]) -> None:
    inspector = inspect(conn)
    existing = {col["name"] for col in inspector.get_columns("auth_sessions")}

    conn.execute(text("PRAGMA foreign_keys=OFF"))

    conn.execute(
        text(
            """
            CREATE TABLE auth_sessions_new (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR(36) NOT NULL,
                session_token_hash VARCHAR(255) NOT NULL,
                user_agent VARCHAR(500) NULL,
                ip_address VARCHAR(64) NULL,
                created_at DATETIME NOT NULL,
                expires_at DATETIME NOT NULL,
                revoked_at DATETIME NULL,
                FOREIGN KEY(user_id) REFERENCES users (id)
            )
            """
        )
    )

    conn.execute(
        text(
            f"""
            INSERT INTO auth_sessions_new (
                id,
                user_id,
                session_token_hash,
                user_agent,
                ip_address,
                created_at,
                expires_at,
                revoked_at
            )
            SELECT
                id,
                CAST(user_id AS TEXT),
                session_token_hash,
                {"user_agent" if "user_agent" in existing else "NULL"},
                {"ip_address" if "ip_address" in existing else "NULL"},
                created_at,
                expires_at,
                {"revoked_at" if "revoked_at" in existing else "NULL"}
            FROM auth_sessions
            """
        )
    )

    conn.execute(text("DROP TABLE auth_sessions"))
    conn.execute(text("ALTER TABLE auth_sessions_new RENAME TO auth_sessions"))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_auth_sessions_session_token_hash ON auth_sessions (session_token_hash)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_auth_sessions_user_id ON auth_sessions (user_id)"))
    conn.execute(text("PRAGMA foreign_keys=ON"))

    applied.append("auth_sessions.sqlite_table_rebuild_user_id_text")


def _rebuild_pickups_sqlite_final_model(conn, applied: list[str]) -> None:
    inspector = inspect(conn)
    existing = {col["name"] for col in inspector.get_columns("pickups")}

    conn.execute(text("PRAGMA foreign_keys=OFF"))

    conn.execute(
        text(
            """
            CREATE TABLE pickups_new (
                id VARCHAR NOT NULL PRIMARY KEY,
                order_id VARCHAR NOT NULL UNIQUE,
                channel VARCHAR(8) NOT NULL,
                region VARCHAR NOT NULL,
                locker_id VARCHAR NULL,
                machine_id VARCHAR NULL,
                slot VARCHAR NULL,
                operator_id VARCHAR NULL,
                tenant_id VARCHAR NULL,
                site_id VARCHAR NULL,
                status VARCHAR(16) NOT NULL,
                lifecycle_stage VARCHAR(24) NOT NULL,
                current_token_id VARCHAR NULL,
                activated_at DATETIME NOT NULL,
                ready_at DATETIME NULL,
                expires_at DATETIME NULL,
                door_opened_at DATETIME NULL,
                item_removed_at DATETIME NULL,
                door_closed_at DATETIME NULL,
                redeemed_at DATETIME NULL,
                redeemed_via VARCHAR(16) NULL,
                expired_at DATETIME NULL,
                cancelled_at DATETIME NULL,
                cancel_reason VARCHAR NULL,
                correlation_id VARCHAR NULL,
                source_event_id VARCHAR NULL,
                sensor_event_id VARCHAR NULL,
                notes VARCHAR NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY(order_id) REFERENCES orders (id)
            )
            """
        )
    )

    region_expr = "region" if "region" in existing else "'PT'"
    status_expr = "COALESCE(status, 'ACTIVE')" if "status" in existing else "'ACTIVE'"
    current_token_expr = "current_token_id" if "current_token_id" in existing else "NULL"
    expires_at_expr = "expires_at" if "expires_at" in existing else "NULL"
    redeemed_at_expr = "redeemed_at" if "redeemed_at" in existing else "NULL"
    redeemed_via_expr = "redeemed_via" if "redeemed_via" in existing else "NULL"
    created_at_expr = "COALESCE(created_at, CURRENT_TIMESTAMP)" if "created_at" in existing else "CURRENT_TIMESTAMP"
    updated_at_expr = "COALESCE(updated_at, CURRENT_TIMESTAMP)" if "updated_at" in existing else "CURRENT_TIMESTAMP"

    channel_expr = """
        CASE
            WHEN EXISTS (
                SELECT 1
                  FROM orders o
                 WHERE o.id = pickups.order_id
                   AND o.channel = 'KIOSK'
            ) THEN 'KIOSK'
            ELSE 'ONLINE'
        END
    """

    lifecycle_expr = """
        CASE
            WHEN COALESCE(status, 'ACTIVE') = 'REDEEMED' THEN 'COMPLETED'
            WHEN COALESCE(status, 'ACTIVE') = 'EXPIRED' THEN 'EXPIRED'
            WHEN COALESCE(status, 'ACTIVE') = 'CANCELLED' THEN 'CANCELLED'
            ELSE 'READY_FOR_PICKUP'
        END
    """

    locker_id_expr = """
        (
            SELECT COALESCE(a.locker_id, o.totem_id)
              FROM orders o
              LEFT JOIN allocations a ON a.order_id = o.id
             WHERE o.id = pickups.order_id
             LIMIT 1
        )
    """

    machine_id_expr = """
        (
            SELECT o.totem_id
              FROM orders o
             WHERE o.id = pickups.order_id
             LIMIT 1
        )
    """

    slot_expr = """
        (
            SELECT CAST(a.slot AS TEXT)
              FROM allocations a
             WHERE a.order_id = pickups.order_id
             ORDER BY a.created_at DESC, a.id DESC
             LIMIT 1
        )
    """

    ready_at_expr = """
        CASE
            WHEN COALESCE(status, 'ACTIVE') IN ('ACTIVE', 'REDEEMED')
            THEN COALESCE(created_at, CURRENT_TIMESTAMP)
            ELSE NULL
        END
    """

    expired_at_expr = """
        CASE
            WHEN COALESCE(status, 'ACTIVE') = 'EXPIRED'
            THEN COALESCE(expires_at, updated_at, created_at, CURRENT_TIMESTAMP)
            ELSE NULL
        END
    """

    cancelled_at_expr = """
        CASE
            WHEN COALESCE(status, 'ACTIVE') = 'CANCELLED'
            THEN COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)
            ELSE NULL
        END
    """

    conn.execute(
        text(
            f"""
            INSERT INTO pickups_new (
                id,
                order_id,
                channel,
                region,
                locker_id,
                machine_id,
                slot,
                operator_id,
                tenant_id,
                site_id,
                status,
                lifecycle_stage,
                current_token_id,
                activated_at,
                ready_at,
                expires_at,
                door_opened_at,
                item_removed_at,
                door_closed_at,
                redeemed_at,
                redeemed_via,
                expired_at,
                cancelled_at,
                cancel_reason,
                correlation_id,
                source_event_id,
                sensor_event_id,
                notes,
                created_at,
                updated_at
            )
            SELECT
                id,
                order_id,
                {channel_expr},
                {region_expr},
                {locker_id_expr},
                {machine_id_expr},
                {slot_expr},
                NULL,
                NULL,
                NULL,
                {status_expr},
                {lifecycle_expr},
                {current_token_expr},
                {created_at_expr},
                {ready_at_expr},
                {expires_at_expr},
                NULL,
                NULL,
                NULL,
                {redeemed_at_expr},
                {redeemed_via_expr},
                {expired_at_expr},
                {cancelled_at_expr},
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                {created_at_expr},
                {updated_at_expr}
            FROM pickups
            """
        )
    )

    conn.execute(text("DROP TABLE pickups"))
    conn.execute(text("ALTER TABLE pickups_new RENAME TO pickups"))

    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_order_id ON pickups (order_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_status ON pickups (status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_channel_status ON pickups (channel, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_region_status ON pickups (region, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_locker_status ON pickups (locker_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_machine_status ON pickups (machine_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_slot_status ON pickups (slot, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_operator_status ON pickups (operator_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_tenant_status ON pickups (tenant_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_site_status ON pickups (site_id, status)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_expires_at ON pickups (expires_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_redeemed_at ON pickups (redeemed_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_created_at ON pickups (created_at)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pickups_lifecycle_stage ON pickups (lifecycle_stage)"))

    conn.execute(text("PRAGMA foreign_keys=ON"))

    applied.append("pickups.sqlite_table_rebuild_final_model")


def migrate_order_pickup_schema() -> dict:
    """
    Migração alinhada ao domínio atual:

    - IDs textuais/UUID
    - users.id -> TEXT
    - orders.user_id -> TEXT
    - auth_sessions.user_id -> TEXT
    - pickups -> modelo final com auditoria, sensores e SaaS
    """

    applied: list[str] = []

    with engine.begin() as conn:
        inspector = inspect(conn)
        dialect = engine.dialect.name

        # =========================
        # SQLITE REBUILDS ESTRUTURAIS
        # =========================
        if dialect == "sqlite":
            if _has_table(inspector, "users") and _sqlite_users_id_needs_rebuild_to_text(conn):
                _rebuild_users_sqlite_to_text_id(conn, applied)
                inspector = inspect(conn)

            if _has_table(inspector, "orders") and _sqlite_orders_user_id_needs_rebuild_to_text(conn):
                _rebuild_orders_sqlite_user_id_to_text(conn, applied)
                inspector = inspect(conn)

            if _has_table(inspector, "auth_sessions") and _sqlite_auth_sessions_user_id_needs_rebuild_to_text(conn):
                _rebuild_auth_sessions_sqlite_user_id_to_text(conn, applied)
                inspector = inspect(conn)

            if _has_table(inspector, "pickups") and _sqlite_pickups_needs_rebuild_for_final_model(conn):
                _rebuild_pickups_sqlite_final_model(conn, applied)
                inspector = inspect(conn)

        # =========================
        # USERS — colunas complementares
        # =========================
        if _has_table(inspector, "users"):
            if not _has_column(inspector, "users", "full_name"):
                conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(255)"))
                applied.append("users.full_name")

            if not _has_column(inspector, "users", "phone"):
                conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(32)"))
                applied.append("users.phone")

            if not _has_column(inspector, "users", "password_hash"):
                conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
                applied.append("users.password_hash")

            if not _has_column(inspector, "users", "is_active"):
                conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN"))
                conn.execute(text("UPDATE users SET is_active = 1 WHERE is_active IS NULL"))
                applied.append("users.is_active")

            if not _has_column(inspector, "users", "email_verified"):
                conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN"))
                conn.execute(text("UPDATE users SET email_verified = 0 WHERE email_verified IS NULL"))
                applied.append("users.email_verified")

            if not _has_column(inspector, "users", "phone_verified"):
                conn.execute(text("ALTER TABLE users ADD COLUMN phone_verified BOOLEAN"))
                conn.execute(text("UPDATE users SET phone_verified = 0 WHERE phone_verified IS NULL"))
                applied.append("users.phone_verified")

            if not _has_column(inspector, "users", "created_at"):
                conn.execute(text("ALTER TABLE users ADD COLUMN created_at DATETIME"))
                conn.execute(text("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
                applied.append("users.created_at")

            if not _has_column(inspector, "users", "updated_at"):
                conn.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME"))
                conn.execute(text("UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"))
                applied.append("users.updated_at")

        inspector = inspect(conn)

        # =========================
        # ORDERS — colunas complementares
        # =========================
        if _has_table(inspector, "orders"):
            if not _has_column(inspector, "orders", "payment_status"):
                conn.execute(text("ALTER TABLE orders ADD COLUMN payment_status VARCHAR(64)"))
                conn.execute(
                    text(
                        """
                        UPDATE orders
                           SET payment_status = CASE
                               WHEN paid_at IS NOT NULL THEN 'APPROVED'
                               ELSE 'CREATED'
                           END
                         WHERE payment_status IS NULL
                        """
                    )
                )
                applied.append("orders.payment_status")

            if not _has_column(inspector, "orders", "card_type"):
                conn.execute(text("ALTER TABLE orders ADD COLUMN card_type VARCHAR(64)"))
                applied.append("orders.card_type")

            if not _has_column(inspector, "orders", "payment_updated_at"):
                conn.execute(text("ALTER TABLE orders ADD COLUMN payment_updated_at DATETIME"))
                conn.execute(
                    text(
                        """
                        UPDATE orders
                           SET payment_updated_at = COALESCE(paid_at, created_at)
                         WHERE payment_updated_at IS NULL
                        """
                    )
                )
                applied.append("orders.payment_updated_at")

            if not _has_column(inspector, "orders", "updated_at"):
                conn.execute(text("ALTER TABLE orders ADD COLUMN updated_at DATETIME"))
                conn.execute(
                    text(
                        """
                        UPDATE orders
                           SET updated_at = COALESCE(created_at, CURRENT_TIMESTAMP)
                         WHERE updated_at IS NULL
                        """
                    )
                )
                applied.append("orders.updated_at")

        inspector = inspect(conn)

        # =========================
        # ALLOCATIONS — colunas complementares
        # =========================
        if _has_table(inspector, "allocations"):
            if not _has_column(inspector, "allocations", "locker_id"):
                conn.execute(text("ALTER TABLE allocations ADD COLUMN locker_id VARCHAR"))
                applied.append("allocations.locker_id")

            if not _has_column(inspector, "allocations", "updated_at"):
                conn.execute(text("ALTER TABLE allocations ADD COLUMN updated_at DATETIME"))
                conn.execute(
                    text(
                        """
                        UPDATE allocations
                           SET updated_at = COALESCE(created_at, CURRENT_TIMESTAMP)
                         WHERE updated_at IS NULL
                        """
                    )
                )
                applied.append("allocations.updated_at")

        inspector = inspect(conn)

        # =========================
        # PICKUPS — garantir colunas finais se tabela já estiver próxima do alvo
        # =========================
        if _has_table(inspector, "pickups"):
            pickup_columns_to_add = {
                "channel": "ALTER TABLE pickups ADD COLUMN channel VARCHAR(8)",
                "locker_id": "ALTER TABLE pickups ADD COLUMN locker_id VARCHAR",
                "machine_id": "ALTER TABLE pickups ADD COLUMN machine_id VARCHAR",
                "slot": "ALTER TABLE pickups ADD COLUMN slot VARCHAR",
                "operator_id": "ALTER TABLE pickups ADD COLUMN operator_id VARCHAR",
                "tenant_id": "ALTER TABLE pickups ADD COLUMN tenant_id VARCHAR",
                "site_id": "ALTER TABLE pickups ADD COLUMN site_id VARCHAR",
                "lifecycle_stage": "ALTER TABLE pickups ADD COLUMN lifecycle_stage VARCHAR(24)",
                "activated_at": "ALTER TABLE pickups ADD COLUMN activated_at DATETIME",
                "ready_at": "ALTER TABLE pickups ADD COLUMN ready_at DATETIME",
                "door_opened_at": "ALTER TABLE pickups ADD COLUMN door_opened_at DATETIME",
                "item_removed_at": "ALTER TABLE pickups ADD COLUMN item_removed_at DATETIME",
                "door_closed_at": "ALTER TABLE pickups ADD COLUMN door_closed_at DATETIME",
                "expired_at": "ALTER TABLE pickups ADD COLUMN expired_at DATETIME",
                "cancelled_at": "ALTER TABLE pickups ADD COLUMN cancelled_at DATETIME",
                "cancel_reason": "ALTER TABLE pickups ADD COLUMN cancel_reason VARCHAR",
                "correlation_id": "ALTER TABLE pickups ADD COLUMN correlation_id VARCHAR",
                "source_event_id": "ALTER TABLE pickups ADD COLUMN source_event_id VARCHAR",
                "sensor_event_id": "ALTER TABLE pickups ADD COLUMN sensor_event_id VARCHAR",
                "notes": "ALTER TABLE pickups ADD COLUMN notes VARCHAR",
            }

            for col, ddl in pickup_columns_to_add.items():
                if not _has_column(inspector, "pickups", col):
                    conn.execute(text(ddl))
                    applied.append(f"pickups.{col}")

            conn.execute(text("UPDATE pickups SET channel = 'ONLINE' WHERE channel IS NULL"))
            conn.execute(text("UPDATE pickups SET lifecycle_stage = 'READY_FOR_PICKUP' WHERE lifecycle_stage IS NULL"))
            conn.execute(text("UPDATE pickups SET activated_at = COALESCE(created_at, CURRENT_TIMESTAMP) WHERE activated_at IS NULL"))
            conn.execute(text("UPDATE pickups SET ready_at = COALESCE(created_at, CURRENT_TIMESTAMP) WHERE ready_at IS NULL AND status IN ('ACTIVE', 'REDEEMED')"))
            conn.execute(text("UPDATE pickups SET expired_at = COALESCE(expires_at, updated_at, created_at, CURRENT_TIMESTAMP) WHERE expired_at IS NULL AND status = 'EXPIRED'"))
            conn.execute(text("UPDATE pickups SET cancelled_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP) WHERE cancelled_at IS NULL AND status = 'CANCELLED'"))

        inspector = inspect(conn)

        # =========================
        # BACKFILL allocations.locker_id
        # =========================
        if _has_table(inspector, "orders") and _has_table(inspector, "allocations") and _has_column(inspector, "allocations", "locker_id"):
            conn.execute(
                text(
                    """
                    UPDATE allocations
                       SET locker_id = (
                           SELECT orders.totem_id
                             FROM orders
                            WHERE orders.id = allocations.order_id
                       )
                     WHERE locker_id IS NULL
                    """
                )
            )
            applied.append("allocations.locker_id_backfill_from_orders")

        # =========================
        # BACKFILL pickups context
        # =========================
        inspector = inspect(conn)
        if _has_table(inspector, "pickups") and _has_table(inspector, "orders"):
            if _has_column(inspector, "pickups", "channel"):
                conn.execute(
                    text(
                        """
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
                            OR TRIM(channel) = ''
                        """
                    )
                )
                applied.append("pickups.channel_backfill_from_orders")

            if _has_column(inspector, "pickups", "machine_id"):
                conn.execute(
                    text(
                        """
                        UPDATE pickups
                           SET machine_id = (
                               SELECT orders.totem_id
                                 FROM orders
                                WHERE orders.id = pickups.order_id
                           )
                         WHERE machine_id IS NULL
                        """
                    )
                )
                applied.append("pickups.machine_id_backfill_from_orders")

            if _has_column(inspector, "pickups", "locker_id"):
                conn.execute(
                    text(
                        """
                        UPDATE pickups
                           SET locker_id = COALESCE(
                               (
                                   SELECT allocations.locker_id
                                     FROM allocations
                                    WHERE allocations.order_id = pickups.order_id
                                    ORDER BY allocations.created_at DESC, allocations.id DESC
                                    LIMIT 1
                               ),
                               (
                                   SELECT orders.totem_id
                                     FROM orders
                                    WHERE orders.id = pickups.order_id
                               )
                           )
                         WHERE locker_id IS NULL
                        """
                    )
                )
                applied.append("pickups.locker_id_backfill")

            if _has_column(inspector, "pickups", "slot"):
                conn.execute(
                    text(
                        """
                        UPDATE pickups
                           SET slot = (
                               SELECT CAST(allocations.slot AS TEXT)
                                 FROM allocations
                                WHERE allocations.order_id = pickups.order_id
                                ORDER BY allocations.created_at DESC, allocations.id DESC
                                LIMIT 1
                           )
                         WHERE slot IS NULL
                        """
                    )
                )
                applied.append("pickups.slot_backfill")

        # =========================
        # INDEXES - ORDERS
        # =========================
        order_indexes = [
            ("orders", "idx_orders_status", "CREATE INDEX idx_orders_status ON orders (status)"),
            ("orders", "idx_orders_channel_status", "CREATE INDEX idx_orders_channel_status ON orders (channel, status)"),
            ("orders", "idx_orders_region_status", "CREATE INDEX idx_orders_region_status ON orders (region, status)"),
            ("orders", "idx_orders_region_totem_status", "CREATE INDEX idx_orders_region_totem_status ON orders (region, totem_id, status)"),
            ("orders", "idx_orders_region_totem_created_at", "CREATE INDEX idx_orders_region_totem_created_at ON orders (region, totem_id, created_at)"),
            ("orders", "idx_orders_paid_at", "CREATE INDEX idx_orders_paid_at ON orders (paid_at)"),
            ("orders", "idx_orders_picked_up_at", "CREATE INDEX idx_orders_picked_up_at ON orders (picked_up_at)"),
            ("orders", "idx_orders_status_picked_up", "CREATE INDEX idx_orders_status_picked_up ON orders (status, picked_up_at)"),
            ("orders", "idx_orders_totem_picked_up", "CREATE INDEX idx_orders_totem_picked_up ON orders (totem_id, picked_up_at)"),
        ]

        allocation_indexes = [
            ("allocations", "idx_allocations_order_id", "CREATE INDEX idx_allocations_order_id ON allocations (order_id)"),
            ("allocations", "idx_allocations_state", "CREATE INDEX idx_allocations_state ON allocations (state)"),
            ("allocations", "idx_allocations_locker_slot_state", "CREATE INDEX idx_allocations_locker_slot_state ON allocations (locker_id, slot, state)"),
            ("allocations", "idx_allocations_created_at", "CREATE INDEX idx_allocations_created_at ON allocations (created_at)"),
        ]

        pickup_indexes = [
            ("pickups", "ix_pickups_order_id", "CREATE INDEX ix_pickups_order_id ON pickups (order_id)"),
            ("pickups", "ix_pickups_status", "CREATE INDEX ix_pickups_status ON pickups (status)"),
            ("pickups", "ix_pickups_channel_status", "CREATE INDEX ix_pickups_channel_status ON pickups (channel, status)"),
            ("pickups", "ix_pickups_region_status", "CREATE INDEX ix_pickups_region_status ON pickups (region, status)"),
            ("pickups", "ix_pickups_locker_status", "CREATE INDEX ix_pickups_locker_status ON pickups (locker_id, status)"),
            ("pickups", "ix_pickups_machine_status", "CREATE INDEX ix_pickups_machine_status ON pickups (machine_id, status)"),
            ("pickups", "ix_pickups_slot_status", "CREATE INDEX ix_pickups_slot_status ON pickups (slot, status)"),
            ("pickups", "ix_pickups_operator_status", "CREATE INDEX ix_pickups_operator_status ON pickups (operator_id, status)"),
            ("pickups", "ix_pickups_tenant_status", "CREATE INDEX ix_pickups_tenant_status ON pickups (tenant_id, status)"),
            ("pickups", "ix_pickups_site_status", "CREATE INDEX ix_pickups_site_status ON pickups (site_id, status)"),
            ("pickups", "ix_pickups_expires_at", "CREATE INDEX ix_pickups_expires_at ON pickups (expires_at)"),
            ("pickups", "ix_pickups_redeemed_at", "CREATE INDEX ix_pickups_redeemed_at ON pickups (redeemed_at)"),
            ("pickups", "ix_pickups_created_at", "CREATE INDEX ix_pickups_created_at ON pickups (created_at)"),
            ("pickups", "ix_pickups_lifecycle_stage", "CREATE INDEX ix_pickups_lifecycle_stage ON pickups (lifecycle_stage)"),
        ]

        for table_name, index_name, ddl in order_indexes + allocation_indexes + pickup_indexes:
            inspector = inspect(conn)
            if _has_table(inspector, table_name) and not _has_index(inspector, table_name, index_name):
                conn.execute(text(ddl))
                applied.append(index_name)


        # =========================
        # FISCAL DOCUMENTS
        # =========================
        inspector = inspect(conn)

        if not _has_table(inspector, "fiscal_documents"):
            conn.execute(
                text(
                    """
                    CREATE TABLE fiscal_documents (
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
                        issued_at DATETIME NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                    """
                )
            )

            applied.append("fiscal_documents.create_table")


        # =========================
        # NOTIFICATION LOGS
        # =========================
        inspector = inspect(conn)

        if _has_table(inspector, "notification_logs"):
            if not _has_column(inspector, "notification_logs", "destination_value"):
                conn.execute(text("ALTER TABLE notification_logs ADD COLUMN destination_value VARCHAR(255)"))
                applied.append("notification_logs.destination_value")

            if not _has_column(inspector, "notification_logs", "attempt_count"):
                conn.execute(text("ALTER TABLE notification_logs ADD COLUMN attempt_count INTEGER"))
                conn.execute(text("UPDATE notification_logs SET attempt_count = 0 WHERE attempt_count IS NULL"))
                applied.append("notification_logs.attempt_count")

            if not _has_column(inspector, "notification_logs", "payload_json"):
                conn.execute(text("ALTER TABLE notification_logs ADD COLUMN payload_json TEXT"))
                applied.append("notification_logs.payload_json")


    return {
        "ok": True,
        "applied": applied,
    }


if __name__ == "__main__":
    result = migrate_order_pickup_schema()
    print(result)