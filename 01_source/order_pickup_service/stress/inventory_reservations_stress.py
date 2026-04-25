from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.db import SessionLocal
from app.jobs.inventory_reserved_reconciliation import run_inventory_reserved_reconciliation_once
from app.jobs.inventory_reservations_expiry import run_inventory_reservations_expiry_once
from app.routers.inventory import (
    post_inventory_reservation_consume,
    post_inventory_reservation_release,
    post_inventory_reserve,
)
from app.schemas.inventory import InventoryReserveIn


@dataclass
class StressTarget:
    product_id: str
    locker_id: str
    slot_size: str
    inventory_id: str


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pick_target(*, min_available: int) -> StressTarget:
    db = SessionLocal()
    try:
        row = db.execute(
            text(
                """
                SELECT id, product_id, locker_id, slot_size, quantity_available
                FROM product_inventory
                WHERE quantity_available >= :min_available
                ORDER BY quantity_available DESC, updated_at DESC
                LIMIT 1
                """
            ),
            {"min_available": int(min_available)},
        ).mappings().first()
        if not row:
            # Fallback para permitir execução automatizada do stress:
            # escolhe o item com maior disponibilidade e faz top-up técnico.
            fallback = db.execute(
                text(
                    """
                    SELECT id, product_id, locker_id, slot_size, quantity_on_hand, quantity_reserved, quantity_available
                    FROM product_inventory
                    ORDER BY quantity_available DESC, updated_at DESC
                    LIMIT 1
                    """
                )
            ).mappings().first()
            if not fallback:
                raise RuntimeError("Tabela product_inventory sem registros para executar o stress D2.")

            deficit = int(min_available) - int(fallback.get("quantity_available") or 0)
            if deficit > 0:
                db.execute(
                    text(
                        """
                        UPDATE product_inventory
                        SET quantity_on_hand = quantity_on_hand + :increment,
                            updated_at = :updated_at
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": str(fallback.get("id") or ""),
                        "increment": deficit + 5,
                        "updated_at": datetime.now(timezone.utc),
                    },
                )
                db.commit()

            row = db.execute(
                text(
                    """
                    SELECT id, product_id, locker_id, slot_size, quantity_available
                    FROM product_inventory
                    WHERE id = :id
                    """
                ),
                {"id": str(fallback.get("id") or "")},
            ).mappings().first()
            if not row:
                raise RuntimeError("Falha ao recarregar item de inventory após top-up técnico do stress.")
        return StressTarget(
            inventory_id=str(row.get("id") or ""),
            product_id=str(row.get("product_id") or ""),
            locker_id=str(row.get("locker_id") or ""),
            slot_size=str(row.get("slot_size") or ""),
        )
    finally:
        db.close()


def _reserve_once(*, target: StressTarget, order_id: str, expires_minutes: int) -> dict:
    db = SessionLocal()
    try:
        payload = InventoryReserveIn(
            order_id=order_id,
            product_id=target.product_id,
            locker_id=target.locker_id,
            slot_size=target.slot_size,
            quantity=1,
            expires_in_minutes=max(1, int(expires_minutes)),
            note="D2 stress reserve",
        )
        actor = SimpleNamespace(id="stress-d2-user")
        result = post_inventory_reserve(payload=payload, current_user=actor, db=db)
        return {
            "ok": True,
            "idempotent": bool(result.idempotent),
            "reservation_id": str(result.reservation.id),
            "status": str(result.reservation.status),
        }
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
        return {
            "ok": False,
            "status_code": int(exc.status_code),
            "detail": detail,
        }
    except SQLAlchemyError as exc:
        db.rollback()
        return {
            "ok": False,
            "status_code": 500,
            "detail": {
                "type": "SQLALCHEMY_ERROR",
                "message": str(exc.__class__.__name__),
            },
        }
    except Exception as exc:
        db.rollback()
        return {
            "ok": False,
            "status_code": 500,
            "detail": {
                "type": "UNEXPECTED_ERROR",
                "message": str(exc.__class__.__name__),
            },
        }
    finally:
        db.close()


def _consume_or_release(*, reservation_id: str, mode: str) -> dict:
    db = SessionLocal()
    try:
        actor = SimpleNamespace(id="stress-d2-user")
        if mode == "consume":
            out = post_inventory_reservation_consume(
                reservation_id=reservation_id,
                current_user=actor,
                db=db,
            )
        else:
            out = post_inventory_reservation_release(
                reservation_id=reservation_id,
                current_user=actor,
                db=db,
            )
        return {
            "ok": True,
            "reservation_id": str(out.reservation.id),
            "status": str(out.reservation.status),
        }
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
        return {
            "ok": False,
            "status_code": int(exc.status_code),
            "detail": detail,
            "reservation_id": reservation_id,
        }
    except SQLAlchemyError as exc:
        db.rollback()
        return {
            "ok": False,
            "status_code": 500,
            "detail": {
                "type": "SQLALCHEMY_ERROR",
                "message": str(exc.__class__.__name__),
            },
            "reservation_id": reservation_id,
        }
    except Exception as exc:
        db.rollback()
        return {
            "ok": False,
            "status_code": 500,
            "detail": {
                "type": "UNEXPECTED_ERROR",
                "message": str(exc.__class__.__name__),
            },
            "reservation_id": reservation_id,
        }
    finally:
        db.close()


def _force_expire(*, reservation_ids: list[str]) -> int:
    if not reservation_ids:
        return 0
    db = SessionLocal()
    try:
        db.execute(
            text(
                """
                UPDATE inventory_reservations
                SET expires_at = :expired_at
                WHERE id = ANY(:ids) AND status = 'ACTIVE'
                """
            ),
            {
                "expired_at": datetime.now(timezone.utc) - timedelta(minutes=5),
                "ids": reservation_ids,
            },
        )
        db.commit()
    finally:
        db.close()

    db = SessionLocal()
    try:
        return int(run_inventory_reservations_expiry_once(db) or 0)
    finally:
        db.close()


def _snapshot_reserved(*, target: StressTarget) -> dict:
    db = SessionLocal()
    try:
        row = db.execute(
            text(
                """
                SELECT
                    pi.quantity_reserved AS reserved_stored,
                    COALESCE(ir.active_reserved, 0) AS reserved_active
                FROM product_inventory pi
                LEFT JOIN (
                    SELECT product_id, locker_id, slot_size, SUM(quantity)::int AS active_reserved
                    FROM inventory_reservations
                    WHERE status = 'ACTIVE'
                    GROUP BY product_id, locker_id, slot_size
                ) ir
                  ON ir.product_id = pi.product_id
                 AND ir.locker_id = pi.locker_id
                 AND ir.slot_size = pi.slot_size
                WHERE pi.id = :inventory_id
                """
            ),
            {"inventory_id": target.inventory_id},
        ).mappings().first() or {}
        return {
            "reserved_stored": int(row.get("reserved_stored") or 0),
            "reserved_active": int(row.get("reserved_active") or 0),
            "delta": int(row.get("reserved_active") or 0) - int(row.get("reserved_stored") or 0),
        }
    finally:
        db.close()


def _inject_divergence(*, target: StressTarget, increment: int) -> None:
    db = SessionLocal()
    try:
        db.execute(
            text(
                """
                UPDATE product_inventory
                SET quantity_reserved = quantity_reserved + :inc,
                    updated_at = :updated_at
                WHERE id = :id
                """
            ),
            {
                "id": target.inventory_id,
                "inc": max(1, int(increment)),
                "updated_at": datetime.now(timezone.utc),
            },
        )
        db.commit()
    finally:
        db.close()


def _run_reconciliation() -> dict:
    db = SessionLocal()
    try:
        return run_inventory_reserved_reconciliation_once(db)
    finally:
        db.close()


def run_stress(
    *,
    workers: int,
    attempts: int,
    min_available: int,
    expires_minutes: int,
    consume_count: int,
    release_count: int,
    expire_count: int,
    evidence_path: Path,
) -> dict:
    started_at = _iso_now()
    target = _pick_target(min_available=min_available)

    reserve_results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, int(workers))) as executor:
        futures = []
        for i in range(max(1, int(attempts))):
            order_id = f"d2-stress-{uuid4()}"
            futures.append(
                executor.submit(
                    _reserve_once,
                    target=target,
                    order_id=order_id,
                    expires_minutes=expires_minutes,
                )
            )
        for future in as_completed(futures):
            reserve_results.append(future.result())

    success_reservations = [r for r in reserve_results if r.get("ok")]
    success_ids = [str(r.get("reservation_id")) for r in success_reservations if r.get("reservation_id")]
    reserve_failures = [r for r in reserve_results if not r.get("ok")]

    consume_ids = success_ids[: max(0, int(consume_count))]
    release_ids = success_ids[len(consume_ids) : len(consume_ids) + max(0, int(release_count))]
    expire_ids = success_ids[
        len(consume_ids) + len(release_ids) : len(consume_ids) + len(release_ids) + max(0, int(expire_count))
    ]

    consume_results = [_consume_or_release(reservation_id=rid, mode="consume") for rid in consume_ids]
    release_results = [_consume_or_release(reservation_id=rid, mode="release") for rid in release_ids]
    expired_by_job = _force_expire(reservation_ids=expire_ids)

    snapshot_before_injected_divergence = _snapshot_reserved(target=target)
    _inject_divergence(target=target, increment=3)
    snapshot_after_injected_divergence = _snapshot_reserved(target=target)
    reconciliation_result = _run_reconciliation()
    snapshot_after_reconciliation = _snapshot_reserved(target=target)

    matched_items = [
        item
        for item in (reconciliation_result.get("items") or [])
        if str(item.get("product_id")) == target.product_id
        and str(item.get("locker_id")) == target.locker_id
        and str(item.get("slot_size")) == target.slot_size
    ]

    report = {
        "scenario": "D2 inventory reservations concurrency + reconciliation",
        "started_at": started_at,
        "finished_at": _iso_now(),
        "target": {
            "product_id": target.product_id,
            "locker_id": target.locker_id,
            "slot_size": target.slot_size,
            "inventory_id": target.inventory_id,
        },
        "reserve_phase": {
            "workers": int(workers),
            "attempts": int(attempts),
            "success_count": len(success_reservations),
            "failure_count": len(reserve_failures),
            "idempotent_hits": sum(1 for r in success_reservations if r.get("idempotent")),
            "failures": reserve_failures[:20],
        },
        "transition_phase": {
            "consume_requested": len(consume_ids),
            "release_requested": len(release_ids),
            "expire_requested": len(expire_ids),
            "consume_success": sum(1 for r in consume_results if r.get("ok")),
            "release_success": sum(1 for r in release_results if r.get("ok")),
            "expired_by_job": int(expired_by_job),
            "consume_failures": [r for r in consume_results if not r.get("ok")][:20],
            "release_failures": [r for r in release_results if not r.get("ok")][:20],
        },
        "reconciliation_evidence": {
            "snapshot_before_injected_divergence": snapshot_before_injected_divergence,
            "snapshot_after_injected_divergence": snapshot_after_injected_divergence,
            "job_result": reconciliation_result,
            "matched_items_for_target": matched_items,
            "snapshot_after_reconciliation": snapshot_after_reconciliation,
        },
    }

    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="D2 stress de concorrência para reservas de inventário + evidência de reconciliação.",
    )
    parser.add_argument("--workers", type=int, default=15)
    parser.add_argument("--attempts", type=int, default=60)
    parser.add_argument("--min-available", type=int, default=40)
    parser.add_argument("--expires-minutes", type=int, default=5)
    parser.add_argument("--consume-count", type=int, default=15)
    parser.add_argument("--release-count", type=int, default=15)
    parser.add_argument("--expire-count", type=int, default=10)
    parser.add_argument(
        "--evidence-path",
        type=Path,
        default=Path("stress/evidence_inventory_d2.json"),
    )
    args = parser.parse_args()

    report = run_stress(
        workers=args.workers,
        attempts=args.attempts,
        min_available=args.min_available,
        expires_minutes=args.expires_minutes,
        consume_count=args.consume_count,
        release_count=args.release_count,
        expire_count=args.expire_count,
        evidence_path=args.evidence_path,
    )

    print("D2_STRESS_OK")
    print("EVIDENCE_PATH", str(args.evidence_path))
    print("RESERVE_SUCCESS", report["reserve_phase"]["success_count"])
    print("RESERVE_FAILURE", report["reserve_phase"]["failure_count"])
    print("CONSUME_SUCCESS", report["transition_phase"]["consume_success"])
    print("RELEASE_SUCCESS", report["transition_phase"]["release_success"])
    print("EXPIRED_BY_JOB", report["transition_phase"]["expired_by_job"])
    snapshot = report["reconciliation_evidence"]["snapshot_after_reconciliation"]
    print("POST_RECONCILE_DELTA", snapshot["delta"])


if __name__ == "__main__":
    main()
