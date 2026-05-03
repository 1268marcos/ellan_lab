#!/usr/bin/env python3
"""100 lockers × 90 dias de ml_features_daily + operador + lockers (idempotente por machine_id MLSYN-)."""
from __future__ import annotations

import os
import random
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

import psycopg2
import psycopg2.extras

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import _pg_dsn  # noqa: E402

OPERATOR_ID = "ml-synthetic-operator"
N_LOCKERS = 100
N_DAYS = 90


def main() -> None:
    # url = os.environ.get("DATABASE_URL", "postgresql://admin:admin@localhost:5432/ellan")
    url = os.environ.get("DATABASE_URL", "postgresql://admin:admin123@postgres_central:5432/locker_central")
    random.seed(42)
    conn = psycopg2.connect(_pg_dsn(url))
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO locker_operators (
            id, name, operator_type, country, active,
            created_at, updated_at, currency
        )
        VALUES (%s, %s, 'OWN', 'BR', TRUE, NOW(), NOW(), 'BRL')
        ON CONFLICT (id) DO UPDATE 
        SET name = EXCLUDED.name, updated_at = NOW()
        """,
        (OPERATOR_ID, "ML Synthetic Operator"),
    )

    locker_ids: list[str] = []
    for i in range(N_LOCKERS):
        lid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ellan-ml-synthetic-locker-{i}"))
        locker_ids.append(lid)
        mid = f"MLSYN-{i:04d}"
        cur.execute(
            """
            INSERT INTO lockers (
                id, display_name, machine_id, operator_id, region, timezone, country,
                slots_count, slots_available, active, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, 'SP', 'America/Sao_Paulo', 'BR', 8, 8, TRUE, NOW(), NOW())
            ON CONFLICT (id) DO UPDATE SET machine_id = EXCLUDED.machine_id
            """,
            (lid, f"ML Synthetic {i}", mid, OPERATOR_ID),
        )

    cur.execute(
        "DELETE FROM ml_features_daily WHERE locker_id = ANY(%s)",
        (locker_ids,),
    )

    today = date.today()
    batch = []
    for lid in locker_ids:
        base_batt = random.uniform(35, 98)
        base_door = random.randint(0, 4)
        base_usage = random.randint(5, 120)
        for day_off in range(1, N_DAYS + 1):
            fd = today - timedelta(days=day_off)
            temp = round(18 + random.gauss(0, 4), 2)
            hum = round(50 + random.gauss(0, 15), 2)
            batt = max(5.0, min(100.0, base_batt + random.gauss(0, 8)))
            df7 = max(0, base_door + random.randint(0, 2))
            u7 = max(0, base_usage + random.randint(-10, 20))
            up = round(min(168.0, 12 + random.random() * 60), 2)
            stress = (100 - batt) / 100.0 + df7 * 0.08 + (temp > 32) * 0.15
            fail = 1 if random.random() < min(0.45, stress * 0.35 + 0.02) else 0
            batch.append(
                (
                    lid,
                    fd,
                    temp,
                    hum,
                    batt,
                    df7,
                    u7,
                    up,
                    fail,
                )
            )

    psycopg2.extras.execute_batch(
        cur,
        """
        INSERT INTO ml_features_daily (
            locker_id, feature_date, temperature_mean, humidity_mean, battery_min,
            door_failures_7d, usage_events_7d, uptime_hours_7d, failure_label_7d
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        batch,
        page_size=500,
    )
    cur.execute("DELETE FROM ml_predictions_log WHERE locker_id = ANY(%s)", (locker_ids,))
    cur.execute(
        """
        INSERT INTO ml_predictions_log (locker_id, failure_probability, health_score, model_version)
        SELECT DISTINCT ON (locker_id)
            locker_id,
            LEAST(0.98, GREATEST(0.02, (100.0 - COALESCE(battery_min, 0)::float) / 130.0))::numeric(8, 6),
            LEAST(99.0, GREATEST(1.0, COALESCE(battery_min, 0)::float * 0.45))::numeric(8, 2),
            'seed-preview'
        FROM ml_features_daily
        WHERE locker_id = ANY(%s)
        ORDER BY locker_id, feature_date DESC
        """,
        (locker_ids,),
    )
    cur.close()
    conn.close()
    print(f"seed ok: {N_LOCKERS} lockers × {N_DAYS} days = {len(batch)} rows + preview predictions")


if __name__ == "__main__":
    main()
