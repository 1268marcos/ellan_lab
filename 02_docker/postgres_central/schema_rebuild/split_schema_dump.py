#!/usr/bin/env python3
"""
Divide complete_schema_*.sql (pg_dump) em fases para rebuild controlado do postgres_central.

Uso:
  python3 split_schema_dump.py ../../complete_schema_20260517_e.sql
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PHASES = [
    ("00_preamble.sql", "preamble"),
    ("01_extensions_schemas.sql", "extension"),
    ("02_types.sql", "type"),
    ("03_tables.sql", "table"),
    ("04_sequences_owned_by.sql", "sequence"),
    ("04b_column_defaults.sql", "defaults"),
    ("05_functions.sql", "function"),
    ("06_constraints_pk_unique_check.sql", "constraint_pk"),
    ("07_indexes.sql", "index"),
    ("08_foreign_keys.sql", "fk"),
    ("09_views.sql", "view"),
    ("10_triggers.sql", "trigger"),
    ("11_rls_policies.sql", "policy"),
    ("12_comments_misc.sql", "misc"),
]

HEADER = """-- Gerado por split_schema_dump.py — NÃO editar manualmente; regenere a partir do dump.
-- Fase: {phase}
-- Execução: ver README.md e run_rebuild.sh

"""

SKIP_TIMESCALE_INTERNAL = True


def is_timescale_internal(header: str, body: str) -> bool:
    blob = (header + body).lower()
    return "_timescaledb_internal" in blob


def classify_block(header: str, body: str) -> str:
    h = header.lower()
    b = body.strip()
    if not b and not h.strip():
        return "skip"
    if is_timescale_internal(header, body) and SKIP_TIMESCALE_INTERNAL:
        return "skip"

    if b.startswith("SET default_tablespace") or b.startswith("SET default_table_access_method"):
        return "preamble"
    if b.startswith("ALTER TABLE ONLY public.") and " SET DEFAULT " in b:
        return "defaults"

    if "type: extension" in h or "type: schema" in h:
        return "extension"
    if "type: type" in h and "schema: public" in h:
        return "type"
    if "type: function" in h and "schema: public" in h:
        return "function"
    if "type: table" in h:
        if "schema: _timescaledb_internal" in h and SKIP_TIMESCALE_INTERNAL:
            return "skip"
        if "schema: public" in h:
            return "table"
        return "skip"
    if "type: sequence" in h and "schema: public" in h:
        return "sequence"
    if "sequence owned by" in h.lower():
        return "sequence"
    if "type: view" in h and "schema: public" in h:
        return "view"
    if "type: materialized view" in h and "schema: public" in h:
        return "view"
    if "type: index" in h:
        if "schema: _timescaledb_internal" in h and SKIP_TIMESCALE_INTERNAL:
            return "skip"
        if "schema: public" in h:
            return "index"
        return "skip"
    if "type: constraint" in h or "type: fk constraint" in h:
        if "schema: _timescaledb_internal" in h and SKIP_TIMESCALE_INTERNAL:
            return "skip"
        if "foreign key" in b.lower() or "type: fk constraint" in h:
            return "fk"
        if "primary key" in b.lower() or "unique" in h.lower() or "check" in b.lower():
            return "constraint_pk"
        return "constraint_pk"
    if "type: trigger" in h and "schema: public" in h:
        return "trigger"
    if "type: policy" in h or "type: row security" in h:
        if "schema: public" in h:
            return "policy"
        return "skip"
    if "type: comment" in h or b.startswith("COMMENT ON"):
        return "misc"
    if b.startswith("ALTER TABLE") and "owner to" in b.lower():
        return "misc"
    if b.startswith("SET ") or b.startswith("SELECT pg_catalog"):
        return "preamble"
    if b.startswith("ALTER TABLE ONLY public."):
        return "misc"
    return "misc"


def split_objects(text: str) -> list[tuple[str, str]]:
    """Divide o dump em blocos (-- Name: ... + SQL até o próximo bloco)."""
    lines = text.splitlines(keepends=True)
    chunks: list[tuple[str, str]] = []
    i = 0
    n = len(lines)

    def is_block_start(idx: int) -> bool:
        return (
            idx + 1 < n
            and lines[idx].strip() == "--"
            and lines[idx + 1].startswith("-- Name:")
        )

    while i < n:
        if not is_block_start(i):
            i += 1
            continue

        block_lines = [lines[i]]  # linha "--" separadora
        i += 1
        # Cabeçalho: linhas de comentário (-- Name:, --, vazias após comentário)
        while i < n:
            if is_block_start(i):
                break
            if lines[i].startswith("--") or lines[i].strip() == "":
                block_lines.append(lines[i])
                i += 1
                continue
            break

        header = "".join(block_lines)
        body_lines: list[str] = []
        while i < n:
            if is_block_start(i):
                break
            body_lines.append(lines[i])
            i += 1
        chunks.append((header, "".join(body_lines)))

    return chunks


def extract_preamble(text: str) -> str:
    m = re.search(
        r"(SET statement_timeout.*?SET row_security = off;\n)",
        text,
        re.DOTALL,
    )
    return m.group(1) if m else ""


def main() -> int:
    if len(sys.argv) < 2:
        print("Uso: split_schema_dump.py <complete_schema.sql>", file=sys.stderr)
        return 1

    src = Path(sys.argv[1]).resolve()
    out_dir = Path(__file__).resolve().parent
    text = src.read_text(encoding="utf-8", errors="replace")

    # Strip pg_dump warning lines
    lines = text.splitlines(keepends=True)
    filtered = []
    for line in lines:
        if line.startswith("pg_dump:"):
            continue
        filtered.append(line)
    text = "".join(filtered)

    preamble = extract_preamble(text)
    buckets: dict[str, list[str]] = {p[1]: [] for p in PHASES}
    buckets["preamble"].append(preamble)

    for header, body in split_objects(text):
        kind = classify_block(header, body)
        if kind == "skip":
            continue
        block = header + "\n" + body
        if kind not in buckets:
            buckets["misc"].append(block)
        else:
            buckets[kind].append(block)

    # Remover blocos Timescale internos que tenham escapado para misc
    buckets["misc"] = [
        b
        for b in buckets.get("misc", [])
        if "_timescaledb_internal" not in b.lower()
    ]

    for fname, key in PHASES:
        parts = buckets.get(key, [])
        if not parts and key not in ("preamble", "defaults"):
            (out_dir / fname).write_text(
                HEADER.format(phase=fname) + "-- (vazio neste dump)\n",
                encoding="utf-8",
            )
            continue
        content = HEADER.format(phase=fname) + "".join(parts)
        (out_dir / fname).write_text(content, encoding="utf-8")
        print(f"  {fname}: {len(parts)} bloco(s), {len(content):,} bytes")

    # Estatísticas
    skipped = sum(1 for h, b in split_objects(text) if classify_block(h, b) == "skip")
    print(f"\nBlocos TimescaleDB internos ignorados: {skipped}")
    print(f"Saída: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
