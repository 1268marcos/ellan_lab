"""Garante tabelas do domínio rental (migrações idempotentes sob demanda)."""
from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core import db_migrations
from app.core.db import engine


_RENTAL_TABLE_MIGRATIONS: list[tuple[str, object]] = [
    ("rental_plans", db_migrations._create_rental_plans),
    ("rental_contracts", db_migrations._create_rental_contracts),
    ("rental_webhook_endpoints", db_migrations._create_rental_webhook_endpoints),
    ("rental_api_keys", db_migrations._create_rental_api_keys),
    ("rental_networks", db_migrations._create_rental_networks),
    ("rental_network_corridors", db_migrations._create_rental_network_corridors),
    ("rental_operators", db_migrations._create_rental_operators),
    ("rental_contract_events", db_migrations._create_rental_contract_events),
    ("rental_billing_invoices", db_migrations._create_rental_billing_invoices),
    ("rental_sla_policies", db_migrations._create_rental_sla_policies),
    ("rental_webhook_deliveries", db_migrations._create_rental_webhook_deliveries),
]

_PRE_FK_MIGRATIONS = [
    db_migrations._migrate_rental_plans_primary_key_v1,
    db_migrations._migrate_rental_contracts_primary_key_v1,
]

_POST_TABLE_MIGRATIONS = [
    db_migrations._migrate_rental_plans_network_id_v1,
    db_migrations._migrate_rental_contracts_operator_id_v1,
]


def ensure_rental_schema(db: Session | None = None) -> list[str]:
    """Aplica migrações rental pendentes (útil quando o DB veio sem PK nas tabelas base)."""
    del db  # usa engine dedicado para não conflitar com a sessão da request
    bind = engine
    try:
        existing = set(inspect(bind).get_table_names())
    except Exception:
        existing = set()

    applied: list[str] = []
    with bind.begin() as conn:
        for migrate_fn in _PRE_FK_MIGRATIONS:
            migrate_fn(conn, applied)

        for table_name, migrate_fn in _RENTAL_TABLE_MIGRATIONS:
            if table_name not in existing:
                migrate_fn(conn, applied)
                existing.add(table_name)

        for migrate_fn in _POST_TABLE_MIGRATIONS:
            migrate_fn(conn, applied)

    return applied


def rental_core_tables_ready() -> bool:
    """True se planos/contratos existem (mínimo para listagens legadas)."""
    try:
        names = set(inspect(engine).get_table_names())
        return "rental_plans" in names and "rental_contracts" in names
    except Exception:
        return False
