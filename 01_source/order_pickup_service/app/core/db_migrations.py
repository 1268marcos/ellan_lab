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


def migrate_order_pickup_schema() -> dict:
    """
    Migração incremental e idempotente do schema do order_pickup_service.

    Objetivos desta versão:
    - users.full_name
    - users.phone
    - users.password_hash
    - users.is_active
    - users.email_verified
    - users.phone_verified
    - users.created_at
    - users.updated_at
    - orders.payment_status
    - orders.card_type
    - orders.payment_updated_at
    - orders.updated_at
    - allocations.locker_id
    - allocations.updated_at
    - índices explícitos em orders
    - índices explícitos em allocations
    """
    dialect = engine.dialect.name
    applied: list[str] = []

    with engine.begin() as conn:
        inspector = inspect(conn)

        # =========================
        # USERS
        # =========================
        if _has_table(inspector, "users"):
            if not _has_column(inspector, "users", "full_name"):
                if dialect == "sqlite":
                    conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(255)"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(255) NULL"))
                applied.append("users.full_name")

            if not _has_column(inspector, "users", "phone"):
                if dialect == "sqlite":
                    conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(32)"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(32) NULL"))
                applied.append("users.phone")

            if not _has_column(inspector, "users", "password_hash"):
                if dialect == "sqlite":
                    conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) NULL"))
                applied.append("users.password_hash")

            if not _has_column(inspector, "users", "is_active"):
                if dialect == "sqlite":
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NULL"))
                conn.execute(
                    text(
                        """
                        UPDATE users
                           SET is_active = 1
                         WHERE is_active IS NULL
                        """
                    )
                )
                applied.append("users.is_active")

            if not _has_column(inspector, "users", "email_verified"):
                if dialect == "sqlite":
                    conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN NULL"))
                conn.execute(
                    text(
                        """
                        UPDATE users
                           SET email_verified = 0
                         WHERE email_verified IS NULL
                        """
                    )
                )
                applied.append("users.email_verified")

            if not _has_column(inspector, "users", "phone_verified"):
                if dialect == "sqlite":
                    conn.execute(text("ALTER TABLE users ADD COLUMN phone_verified BOOLEAN"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN phone_verified BOOLEAN NULL"))
                conn.execute(
                    text(
                        """
                        UPDATE users
                           SET phone_verified = 0
                         WHERE phone_verified IS NULL
                        """
                    )
                )
                applied.append("users.phone_verified")

            if not _has_column(inspector, "users", "created_at"):
                if dialect == "sqlite":
                    conn.execute(text("ALTER TABLE users ADD COLUMN created_at DATETIME"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP NULL"))
                conn.execute(
                    text(
                        """
                        UPDATE users
                           SET created_at = CURRENT_TIMESTAMP
                         WHERE created_at IS NULL
                        """
                    )
                )
                applied.append("users.created_at")

            if not _has_column(inspector, "users", "updated_at"):
                if dialect == "sqlite":
                    conn.execute(text("ALTER TABLE users ADD COLUMN updated_at DATETIME"))
                else:
                    conn.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP NULL"))
                conn.execute(
                    text(
                        """
                        UPDATE users
                           SET updated_at = COALESCE(created_at, CURRENT_TIMESTAMP)
                         WHERE updated_at IS NULL
                        """
                    )
                )
                applied.append("users.updated_at")

        # refresh inspector após alterações
        inspector = inspect(conn)

        # Backfill best-effort de full_name
        if _has_table(inspector, "users") and _has_column(inspector, "users", "full_name"):
            existing_user_columns = {col["name"] for col in inspector.get_columns("users")}

            if "name" in existing_user_columns:
                conn.execute(
                    text(
                        """
                        UPDATE users
                           SET full_name = name
                         WHERE full_name IS NULL
                            OR TRIM(full_name) = ''
                        """
                    )
                )
                applied.append("users.full_name_backfill_from_name")
            elif "email" in existing_user_columns:
                conn.execute(
                    text(
                        """
                        UPDATE users
                           SET full_name = email
                         WHERE full_name IS NULL
                            OR TRIM(full_name) = ''
                        """
                    )
                )
                applied.append("users.full_name_backfill_from_email")

        inspector = inspect(conn)

        # =========================
        # ORDERS
        # =========================
        if _has_table(inspector, "orders"):
            if not _has_column(inspector, "orders", "payment_status"):
                if dialect == "sqlite":
                    conn.execute(
                        text("ALTER TABLE orders ADD COLUMN payment_status VARCHAR(64)")
                    )
                else:
                    conn.execute(
                        text("ALTER TABLE orders ADD COLUMN payment_status VARCHAR(64) NULL")
                    )

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
                if dialect == "sqlite":
                    conn.execute(
                        text("ALTER TABLE orders ADD COLUMN card_type VARCHAR(64)")
                    )
                else:
                    conn.execute(
                        text("ALTER TABLE orders ADD COLUMN card_type VARCHAR(64) NULL")
                    )
                applied.append("orders.card_type")

            if not _has_column(inspector, "orders", "payment_updated_at"):
                if dialect == "sqlite":
                    conn.execute(
                        text("ALTER TABLE orders ADD COLUMN payment_updated_at DATETIME")
                    )
                else:
                    conn.execute(
                        text(
                            "ALTER TABLE orders ADD COLUMN payment_updated_at TIMESTAMP NULL"
                        )
                    )

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
                if dialect == "sqlite":
                    conn.execute(text("ALTER TABLE orders ADD COLUMN updated_at DATETIME"))
                else:
                    conn.execute(
                        text("ALTER TABLE orders ADD COLUMN updated_at TIMESTAMP NULL")
                    )

                conn.execute(
                    text(
                        """
                        UPDATE orders
                           SET updated_at = created_at
                         WHERE updated_at IS NULL
                        """
                    )
                )
                applied.append("orders.updated_at")

        inspector = inspect(conn)

        # =========================
        # ALLOCATIONS
        # =========================
        if _has_table(inspector, "allocations"):
            if not _has_column(inspector, "allocations", "locker_id"):
                if dialect == "sqlite":
                    conn.execute(
                        text("ALTER TABLE allocations ADD COLUMN locker_id VARCHAR")
                    )
                else:
                    conn.execute(
                        text("ALTER TABLE allocations ADD COLUMN locker_id VARCHAR NULL")
                    )
                applied.append("allocations.locker_id")

            if not _has_column(inspector, "allocations", "updated_at"):
                if dialect == "sqlite":
                    conn.execute(
                        text("ALTER TABLE allocations ADD COLUMN updated_at DATETIME")
                    )
                else:
                    conn.execute(
                        text("ALTER TABLE allocations ADD COLUMN updated_at TIMESTAMP NULL")
                    )

                conn.execute(
                    text(
                        """
                        UPDATE allocations
                           SET updated_at = created_at
                         WHERE updated_at IS NULL
                        """
                    )
                )
                applied.append("allocations.updated_at")

        inspector = inspect(conn)

        # =========================
        # INDEXES - ORDERS
        # =========================
        orders_indexes = [
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

        # =========================
        # INDEXES - ALLOCATIONS
        # =========================
        allocations_indexes = [
            ("allocations", "idx_allocations_order_id", "CREATE INDEX idx_allocations_order_id ON allocations (order_id)"),
            ("allocations", "idx_allocations_state", "CREATE INDEX idx_allocations_state ON allocations (state)"),
            ("allocations", "idx_allocations_locker_slot_state", "CREATE INDEX idx_allocations_locker_slot_state ON allocations (locker_id, slot, state)"),
            ("allocations", "idx_allocations_created_at", "CREATE INDEX idx_allocations_created_at ON allocations (created_at)"),
        ]

        for table_name, index_name, ddl in orders_indexes + allocations_indexes:
            inspector = inspect(conn)
            if _has_table(inspector, table_name) and not _has_index(inspector, table_name, index_name):
                conn.execute(text(ddl))
                applied.append(index_name)

        # =========================
        # BACKFILL allocations.locker_id
        # =========================
        inspector = inspect(conn)
        if _has_table(inspector, "orders") and _has_table(inspector, "allocations"):
            if _has_column(inspector, "allocations", "locker_id"):
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

    return {
        "ok": True,
        "applied": applied,
    }


if __name__ == "__main__":
    result = migrate_order_pickup_schema()
    print(result)