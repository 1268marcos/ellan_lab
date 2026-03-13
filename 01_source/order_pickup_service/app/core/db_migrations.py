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
    - orders.payment_status
    - orders.card_type
    - orders.payment_updated_at
    - orders.updated_at
    - allocations.locker_id
    - allocations.updated_at
    - índices novos em orders
    - índices novos em allocations
    """
    dialect = engine.dialect.name
    applied: list[str] = []

    with engine.begin() as conn:
        inspector = inspect(conn)

        # =========================
        # ORDERS
        # =========================
        if _has_table(inspector, "orders"):
            if not _has_column(inspector, "orders", "payment_status"):
                if dialect == "sqlite":
                    conn.execute(
                        text(
                            "ALTER TABLE orders ADD COLUMN payment_status VARCHAR(64)"
                        )
                    )
                else:
                    conn.execute(
                        text(
                            "ALTER TABLE orders ADD COLUMN payment_status VARCHAR(64) NULL"
                        )
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
                        text(
                            "ALTER TABLE orders ADD COLUMN card_type VARCHAR(64)"
                        )
                    )
                else:
                    conn.execute(
                        text(
                            "ALTER TABLE orders ADD COLUMN card_type VARCHAR(64) NULL"
                        )
                    )
                applied.append("orders.card_type")

            if not _has_column(inspector, "orders", "payment_updated_at"):
                if dialect == "sqlite":
                    conn.execute(
                        text(
                            "ALTER TABLE orders ADD COLUMN payment_updated_at DATETIME"
                        )
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
                    conn.execute(
                        text(
                            "ALTER TABLE orders ADD COLUMN updated_at DATETIME"
                        )
                    )
                else:
                    conn.execute(
                        text(
                            "ALTER TABLE orders ADD COLUMN updated_at TIMESTAMP NULL"
                        )
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
                        text(
                            "ALTER TABLE allocations ADD COLUMN locker_id VARCHAR"
                        )
                    )
                else:
                    conn.execute(
                        text(
                            "ALTER TABLE allocations ADD COLUMN locker_id VARCHAR NULL"
                        )
                    )
                applied.append("allocations.locker_id")

            if not _has_column(inspector, "allocations", "updated_at"):
                if dialect == "sqlite":
                    conn.execute(
                        text(
                            "ALTER TABLE allocations ADD COLUMN updated_at DATETIME"
                        )
                    )
                else:
                    conn.execute(
                        text(
                            "ALTER TABLE allocations ADD COLUMN updated_at TIMESTAMP NULL"
                        )
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