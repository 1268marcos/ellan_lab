#!/usr/bin/env python3
"""Gera 14_seed_schema_migrations.sql a partir dos nomes em db_migrations.py."""
from __future__ import annotations

import re
from pathlib import Path

MIGRATIONS_PY = (
    Path(__file__).resolve().parents[3]
    / "01_source/order_pickup_service/app/core/db_migrations.py"
)
OUT = Path(__file__).resolve().parent / "14_seed_schema_migrations.sql"


def main() -> None:
    text = MIGRATIONS_PY.read_text(encoding="utf-8")
    names = sorted(set(re.findall(r'name = "([^"]+)"', text)))
    lines = [
        "-- Marca migrações do order_pickup_service como já aplicadas após rebuild via pg_dump.",
        "-- Evita reexecução de CREATE/DROP (ex.: ml_features_daily_mv) no primeiro startup.",
        "-- Regenerar: python3 generate_schema_migrations_seed.py",
        "",
        "INSERT INTO public.schema_migrations (name, applied_at)",
        "VALUES",
    ]
    values = ",\n".join(f"    ('{n}', NOW())" for n in names)
    lines.append(values)
    lines.append("ON CONFLICT (name) DO NOTHING;")
    lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(names)} rows -> {OUT}")


if __name__ == "__main__":
    main()
