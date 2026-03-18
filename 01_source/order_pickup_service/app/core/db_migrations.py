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

            ###
            ##
            #
            # =========================
            # SQLITE USERS TABLE REBUILD
            # =========================
            if dialect == "sqlite" and _has_table(inspector, "users"):
                if _sqlite_users_id_needs_rebuild(conn):
                    conn.execute(text("PRAGMA foreign_keys=OFF"))

                    conn.execute(
                        text(
                            """
                            CREATE TABLE users_new (
                                id INTEGER PRIMARY KEY,
                                full_name VARCHAR(255) NULL,
                                email VARCHAR(255) NOT NULL,
                                phone VARCHAR(32) NULL,
                                password_hash VARCHAR(255) NULL,
                                is_active BOOLEAN NULL,
                                email_verified BOOLEAN NULL,
                                phone_verified BOOLEAN NULL,
                                created_at DATETIME NULL,
                                updated_at DATETIME NULL
                            )
                            """
                        )
                    )

                    existing_user_columns = {col["name"] for col in inspector.get_columns("users")}

                    full_name_expr = (
                        "full_name"
                        if "full_name" in existing_user_columns
                        else ("name" if "name" in existing_user_columns else "email")
                    )

                    phone_expr = "phone" if "phone" in existing_user_columns else "NULL"
                    password_hash_expr = (
                        "password_hash" if "password_hash" in existing_user_columns else "NULL"
                    )
                    is_active_expr = "is_active" if "is_active" in existing_user_columns else "1"
                    email_verified_expr = (
                        "email_verified" if "email_verified" in existing_user_columns else "0"
                    )
                    phone_verified_expr = (
                        "phone_verified" if "phone_verified" in existing_user_columns else "0"
                    )
                    created_at_expr = "created_at" if "created_at" in existing_user_columns else "CURRENT_TIMESTAMP"
                    updated_at_expr = "updated_at" if "updated_at" in existing_user_columns else "CURRENT_TIMESTAMP"

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
                                id,
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
                    conn.execute(text("PRAGMA foreign_keys=ON"))

                    applied.append("users.sqlite_table_rebuild_for_integer_primary_key")
                    inspector = inspect(conn)



            #
            ##
            ###
            
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
        # SQLITE ORDERS TABLE REBUILD (user_id -> INTEGER)
        # =========================
        inspector = inspect(conn)
        if dialect == "sqlite" and _has_table(inspector, "orders"):
            if _sqlite_orders_user_id_needs_rebuild(conn):
                conn.execute(text("PRAGMA foreign_keys=OFF"))

                conn.execute(
                    text(
                        """
                        CREATE TABLE orders_new (
                            id VARCHAR NOT NULL PRIMARY KEY,
                            user_id INTEGER NULL,
                            channel VARCHAR(6) NOT NULL,
                            region VARCHAR NOT NULL,
                            totem_id VARCHAR NOT NULL,
                            sku_id VARCHAR NOT NULL,
                            amount_cents INTEGER NOT NULL,
                            status VARCHAR(18) NOT NULL,
                            gateway_transaction_id VARCHAR NULL,
                            payment_method VARCHAR(21) NULL,
                            payment_status VARCHAR(30) NULL,
                            card_type VARCHAR(10) NULL,
                            payment_updated_at DATETIME NULL,
                            paid_at DATETIME NULL,
                            pickup_deadline_at DATETIME NULL,
                            picked_up_at DATETIME NULL,
                            guest_session_id VARCHAR NULL,
                            receipt_email VARCHAR NULL,
                            receipt_phone VARCHAR NULL,
                            consent_marketing INTEGER NULL,
                            guest_phone VARCHAR NULL,
                            guest_email VARCHAR NULL,
                            created_at DATETIME NOT NULL,
                            updated_at DATETIME NOT NULL
                        )
                        """
                    )
                )

                existing_order_columns = {col["name"] for col in inspector.get_columns("orders")}

                gateway_transaction_id_expr = (
                    "gateway_transaction_id" if "gateway_transaction_id" in existing_order_columns else "NULL"
                )
                payment_method_expr = (
                    "payment_method" if "payment_method" in existing_order_columns else "NULL"
                )
                payment_status_expr = (
                    "payment_status" if "payment_status" in existing_order_columns else "'CREATED'"
                )
                card_type_expr = "card_type" if "card_type" in existing_order_columns else "NULL"
                payment_updated_at_expr = (
                    "payment_updated_at" if "payment_updated_at" in existing_order_columns else "NULL"
                )
                paid_at_expr = "paid_at" if "paid_at" in existing_order_columns else "NULL"
                pickup_deadline_at_expr = (
                    "pickup_deadline_at" if "pickup_deadline_at" in existing_order_columns else "NULL"
                )
                picked_up_at_expr = (
                    "picked_up_at" if "picked_up_at" in existing_order_columns else "NULL"
                )
                guest_session_id_expr = (
                    "guest_session_id" if "guest_session_id" in existing_order_columns else "NULL"
                )
                receipt_email_expr = (
                    "receipt_email" if "receipt_email" in existing_order_columns else "NULL"
                )
                receipt_phone_expr = (
                    "receipt_phone" if "receipt_phone" in existing_order_columns else "NULL"
                )
                consent_marketing_expr = (
                    "consent_marketing" if "consent_marketing" in existing_order_columns else "0"
                )
                guest_phone_expr = "guest_phone" if "guest_phone" in existing_order_columns else "NULL"
                guest_email_expr = "guest_email" if "guest_email" in existing_order_columns else "NULL"
                updated_at_expr = "updated_at" if "updated_at" in existing_order_columns else "created_at"

                # user_id:
                # - se for numérico em texto, converte para INTEGER
                # - se for algo como 'dev_user_1', vira NULL
                user_id_expr = """
                    CASE
                        WHEN user_id IS NULL THEN NULL
                        WHEN TRIM(CAST(user_id AS TEXT)) GLOB '[0-9]*' THEN CAST(user_id AS INTEGER)
                        ELSE NULL
                    END
                """

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
                            {user_id_expr},
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
                conn.execute(text("PRAGMA foreign_keys=ON"))

                applied.append("orders.sqlite_table_rebuild_user_id_to_integer")
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


def _sqlite_users_id_needs_rebuild(conn) -> bool:
    """
    Detecta se a tabela users do SQLite precisa ser recriada para que
    users.id volte a funcionar como INTEGER PRIMARY KEY autoincrement implícito.

    Em SQLite, o comportamento correto de autoincrement do rowid depende de
    users.id estar definido como INTEGER PRIMARY KEY.
    """
    sql = _sqlite_table_sql(conn, "users")
    if not sql:
        return False

    normalized = " ".join(sql.lower().split())

    # Caso saudável esperado:
    # id integer primary key
    if "id integer primary key" in normalized:
        return False

    return True




def _sqlite_orders_id_user_id_sql(conn) -> str | None:
    row = conn.execute(
        text(
            """
            SELECT sql
              FROM sqlite_master
             WHERE type = 'table'
               AND name = 'orders'
            """
        )
    ).fetchone()
    return row[0] if row and row[0] else None


def _sqlite_orders_user_id_needs_rebuild(conn) -> bool:
    """
    Detecta se a tabela orders no SQLite ainda está com user_id em tipo textual.
    Queremos normalizar para INTEGER.
    """
    sql = _sqlite_orders_id_user_id_sql(conn)
    if not sql:
        return False

    normalized = " ".join(sql.lower().split())

    # Caso correto esperado:
    # user_id integer
    if "user_id integer" in normalized:
        return False

    return True




if __name__ == "__main__":
    result = migrate_order_pickup_schema()
    print(result)