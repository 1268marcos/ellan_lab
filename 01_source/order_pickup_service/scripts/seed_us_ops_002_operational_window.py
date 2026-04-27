from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from random import Random
from uuid import uuid4

from app.core.db import SessionLocal
from app.models.ops_action_audit import OpsActionAudit


LOCKERS = (
    "SP-ALPHAVILLE-SHOP-LK-001",
    "SP-CARAPICUIBA-JDMARILU-LK-001",
    "PT-MAIA-CENTRO-LK-001",
)

SEED_TAG = "US-OPS-002-OPERACIONAL-2026-04-17"


@dataclass(frozen=True)
class PhaseRule:
    start: datetime
    end: datetime
    actions_per_locker_per_hour: int
    error_ratio: float
    base_latency_ms: float
    jitter_ms: float


def utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def build_phase_rules(now: datetime) -> list[PhaseRule]:
    # Regras com aumento gradual de erros para facilitar validação visual
    # de severidades no período mais recente.
    return [
        PhaseRule(
            start=datetime(2026, 4, 17, 0, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 4, 22, 0, 0, 0, tzinfo=timezone.utc),
            actions_per_locker_per_hour=2,
            error_ratio=0.08,
            base_latency_ms=85.0,
            jitter_ms=35.0,
        ),
        PhaseRule(
            start=datetime(2026, 4, 22, 0, 0, 0, tzinfo=timezone.utc),
            end=datetime(2026, 4, 26, 0, 0, 0, tzinfo=timezone.utc),
            actions_per_locker_per_hour=3,
            error_ratio=0.24,
            base_latency_ms=130.0,
            jitter_ms=55.0,
        ),
        PhaseRule(
            start=datetime(2026, 4, 26, 0, 0, 0, tzinfo=timezone.utc),
            end=now,
            actions_per_locker_per_hour=4,
            error_ratio=0.56,
            base_latency_ms=210.0,
            jitter_ms=90.0,
        ),
    ]


def pick_error_message(rng: Random, locker_id: str) -> str:
    samples = [
        f"timeout while contacting locker gateway ({locker_id})",
        f"locker integration http 504 for {locker_id}",
        f"validacao de payload operacional para {locker_id}",
        f"upstream integration error for locker {locker_id}",
        f"infra queue delay processing locker {locker_id}",
    ]
    return samples[rng.randrange(0, len(samples))]


def generate_rows(now: datetime) -> list[OpsActionAudit]:
    rng = Random(20260427)
    rows: list[OpsActionAudit] = []
    phase_rules = build_phase_rules(now)

    for rule in phase_rules:
        start = utc(rule.start)
        end = utc(rule.end)
        if end <= start:
            continue

        current = start
        while current < end:
            for locker_id in LOCKERS:
                for idx in range(rule.actions_per_locker_per_hour):
                    ts = current + timedelta(minutes=idx * (60.0 / rule.actions_per_locker_per_hour))
                    if ts >= end:
                        continue
                    is_error = rng.random() < rule.error_ratio
                    latency = max(20.0, rule.base_latency_ms + rng.uniform(-rule.jitter_ms, rule.jitter_ms))
                    result = "ERROR" if is_error else "SUCCESS"
                    action = (
                        "OPS_RECON_PENDING_RUN_ONCE"
                        if rng.random() < 0.45
                        else "OPS_METRICS_VIEW"
                    )
                    row = OpsActionAudit(
                        id=f"oaa_seed_{uuid4().hex[:24]}",
                        action=action,
                        result=result,
                        correlation_id=f"corr-seed-{uuid4().hex[:20]}",
                        user_id="seed-ops",
                        role="admin_operacao",
                        order_id=f"seed-{uuid4().hex[:12]}",
                        error_message=pick_error_message(rng, locker_id) if is_error else None,
                        details_json={
                            "seed_tag": SEED_TAG,
                            "locker_id": locker_id,
                            "duration_ms": round(latency, 2),
                            "metrics": {"latency_ms": round(latency, 2)},
                            "source": "seed_us_ops_002_operational_window",
                        },
                        created_at=ts,
                    )
                    rows.append(row)
            current += timedelta(hours=1)
    return rows


def run() -> None:
    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        existing = (
            db.query(OpsActionAudit.id)
            .filter(OpsActionAudit.details_json["seed_tag"].as_string() == SEED_TAG)
            .first()
        )
        if existing:
            print(f"Seed já aplicado para tag {SEED_TAG}. Nenhuma ação executada.")
            return

        rows = generate_rows(now)
        db.bulk_save_objects(rows)
        db.commit()
        print(
            f"Seed aplicado com sucesso: {len(rows)} registros em ops_action_audit "
            f"de 2026-04-17 até {now.isoformat()} para lockers: {', '.join(LOCKERS)}."
        )
    finally:
        db.close()


if __name__ == "__main__":
    run()
