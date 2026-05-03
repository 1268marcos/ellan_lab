#!/usr/bin/env python3
"""
Hotfix: Corrige lockers sem slot_config ou remove sintéticos órfãos.
Uso: PYTHONPATH=. python scripts/fix_locker_slots.py --dry-run
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import psycopg2
import psycopg2.extras
from app.db import _pg_dsn

def main():
    p = argparse.ArgumentParser(description="Fix lockers without slot config")
    p.add_argument("--dry-run", action="store_true", help="Apenas mostra o que seria feito")
    p.add_argument("--remove-synthetic", action="store_true", help="Remove lockers MLSYN-* em vez de corrigir")
    p.add_argument("--default-slots", type=int, default=8, help="Slots padrão para correção")
    args = p.parse_args()

    url = os.environ.get("DATABASE_URL", "postgresql://admin:admin123@localhost:5435/locker_central")
    conn = psycopg2.connect(_pg_dsn(url))
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # 1. Identifica lockers problemáticos
    cur.execute("""
        SELECT l.id, l.display_name, l.machine_id, l.operator_id, l.slots_count, l.active
        FROM lockers l
        LEFT JOIN locker_slots ls ON ls.locker_id = l.id
        WHERE l.active = true
        AND (l.slots_count IS NULL OR l.slots_count <= 0)
        GROUP BY l.id
        HAVING COUNT(ls.id) = 0
        ORDER BY l.machine_id
    """)
    broken = cur.fetchall()

    if not broken:
        print("✅ Nenhum locker sem slot_config encontrado.")
        return

    print(f"🔍 Encontrados {len(broken)} lockers sem configuração de slots:\n")
    for r in broken[:10]:
        print(f"  • {r['machine_id']} | {r['display_name']} | slots_count={r['slots_count']}")
    if len(broken) > 10:
        print(f"  ... e mais {len(broken) - 10}")

    if args.dry_run:
        print("\n⚠️  DRY-RUN: nada foi alterado. Remova --dry-run para aplicar.")
        return

    # 2. Aplica correção
    fixed = 0
    for locker in broken:
        lid = locker['id']
        mid = locker['machine_id'] or ''
        
        if args.remove_synthetic and mid.startswith('MLSYN-'):
            # Remove locker sintético órfão
            cur.execute("DELETE FROM ml_features_daily WHERE locker_id = %s", (lid,))
            cur.execute("DELETE FROM ml_predictions_log WHERE locker_id = %s", (lid,))
            cur.execute("DELETE FROM lockers WHERE id = %s", (lid,))
            print(f"🗑️  Removido sintético: {mid}")
            fixed += 1
        else:
            # Corrige com slots padrão
            slots = args.default_slots
            cur.execute("""
                UPDATE lockers 
                SET slots_count = %s, slots_available = %s, updated_at = NOW()
                WHERE id = %s
            """, (slots, slots, lid))
            
            # Insere slots individuais se a tabela existir
            try:
                for s in range(1, slots + 1):
                    cur.execute("""
                        INSERT INTO locker_slots (locker_id, slot_number, slot_type, is_active, created_at)
                        VALUES (%s, %s, 'STANDARD', true, NOW())
                        ON CONFLICT (locker_id, slot_number) DO NOTHING
                    """, (lid, s))
            except psycopg2.errors.UndefinedTable:
                pass  # Tabela locker_slots pode não existir ainda
            
            print(f"✅ Corrigido: {mid} → {slots} slots")
            fixed += 1

    conn.commit()
    print(f"\n🎯 Conclusão: {fixed}/{len(broken)} lockers processados.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()