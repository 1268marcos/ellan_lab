#!/usr/bin/env python3
"""
Corrige créditos USED com order_id inválido ou pedido inexistente/expirado.

Uso (a partir de order_pickup_service/):
  PYTHONPATH=. python scripts/fix_orphan_credits.py --dry-run
  PYTHONPATH=. python scripts/fix_orphan_credits.py --limit 50
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.credit import Credit, CreditStatus
from app.models.order import Order, OrderStatus
from app.services.ops_audit_service import record_ops_action_audit

AUDIT_ACTION = "SCRIPT_FIX_ORPHAN_CREDIT"
EXPIRED_ORDER_STATUSES = frozenset(
    {
        OrderStatus.EXPIRED.value,
        OrderStatus.EXPIRED_CREDIT_50.value,
    }
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class CreditFixDecision:
    credit_id: str
    order_id: str | None
    action: str
    reason: str
    order_status: str | None = None
    dry_run: bool = False


def find_suspect_used_credits(db: Session, *, limit: int, credit_id: str | None) -> list[Credit]:
    if credit_id:
        row = (
            db.query(Credit)
            .filter(Credit.id == str(credit_id).strip(), Credit.status == CreditStatus.USED)
            .first()
        )
        return [row] if row else []

    out: list[Credit] = []
    rows = (
        db.query(Credit)
        .filter(Credit.status == CreditStatus.USED)
        .order_by(Credit.updated_at.asc())
        .all()
    )
    for credit in rows:
        if len(out) >= max(int(limit), 1):
            break
        oid = str(credit.order_id or "").strip()
        if not oid:
            out.append(credit)
            continue
        order = db.get(Order, oid)
        if order is None:
            out.append(credit)
            continue
        status = str(getattr(order.status, "value", order.status))
        if status in EXPIRED_ORDER_STATUSES:
            out.append(credit)
    return out


def _resolve_order(db: Session, order_id: str | None) -> Order | None:
    oid = str(order_id or "").strip()
    if not oid:
        return None
    return db.get(Order, oid)


def decide_credit_fix(*, credit: Credit, order: Order | None) -> CreditFixDecision:
    oid = str(credit.order_id or "").strip() or None
    if not oid:
        return CreditFixDecision(
            credit_id=credit.id,
            order_id=None,
            action="restore",
            reason="missing_order_id",
        )

    if order is None:
        return CreditFixDecision(
            credit_id=credit.id,
            order_id=oid,
            action="restore",
            reason="order_not_found",
        )

    status = str(getattr(order.status, "value", order.status))
    if status == OrderStatus.PICKED_UP.value:
        return CreditFixDecision(
            credit_id=credit.id,
            order_id=oid,
            action="keep",
            reason="order_picked_up",
            order_status=status,
        )

    if status in EXPIRED_ORDER_STATUSES:
        return CreditFixDecision(
            credit_id=credit.id,
            order_id=oid,
            action="restore",
            reason="order_expired",
            order_status=status,
        )

    return CreditFixDecision(
        credit_id=credit.id,
        order_id=oid,
        action="keep",
        reason="order_active_not_expired",
        order_status=status,
    )


def _restore_credit(*, credit: Credit, ref: datetime, reason: str) -> None:
    note = f"[fix_orphan_credits] Restaurado para AVAILABLE ({reason})."
    credit.status = CreditStatus.AVAILABLE
    credit.used_at = None
    credit.updated_at = ref
    credit.notes = f"{credit.notes}\n{note}".strip() if credit.notes else note


def _audit(
    db: Session,
    *,
    correlation_id: str,
    decision: CreditFixDecision,
    dry_run: bool,
) -> None:
    result_map = {
        "restore": "SUCCESS" if not dry_run else "DRY_RUN",
        "keep": "SKIPPED",
    }
    record_ops_action_audit(
        db=db,
        action=AUDIT_ACTION,
        result=result_map.get(decision.action, "UNKNOWN"),
        correlation_id=correlation_id,
        user_id=None,
        role="system_script",
        order_id=decision.order_id,
        details={
            "credit_id": decision.credit_id,
            "decision_action": decision.action,
            "reason": decision.reason,
            "order_status": decision.order_status,
            "dry_run": dry_run,
            "script": "fix_orphan_credits.py",
        },
    )


def run_fix_orphan_credits(
    db: Session,
    *,
    dry_run: bool,
    limit: int,
    credit_id: str | None,
    correlation_id: str,
) -> dict[str, Any]:
    ref = _utc_now()
    credits = find_suspect_used_credits(db, limit=limit, credit_id=credit_id)
    summary: dict[str, Any] = {
        "correlation_id": correlation_id,
        "dry_run": dry_run,
        "scanned": len(credits),
        "restored": 0,
        "kept": 0,
        "decisions": [],
    }

    for credit in credits:
        order = _resolve_order(db, credit.order_id)
        decision = decide_credit_fix(credit=credit, order=order)
        decision.dry_run = dry_run
        summary["decisions"].append(asdict(decision))

        if decision.action == "restore":
            if not dry_run:
                _restore_credit(credit=credit, ref=ref, reason=decision.reason)
            summary["restored"] += 1
        else:
            summary["kept"] += 1

        if not dry_run:
            _audit(db, correlation_id=correlation_id, decision=decision, dry_run=False)

    if not dry_run:
        db.commit()

    return summary


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Corrige créditos USED órfãos ou ligados a pedido expirado.")
    p.add_argument("--dry-run", action="store_true", help="Simula sem alterar créditos (auditoria DRY_RUN).")
    p.add_argument("--limit", type=int, default=100, help="Máximo de créditos a processar.")
    p.add_argument("--credit-id", type=str, default=None, help="Processar um crédito específico.")
    p.add_argument(
        "--correlation-id",
        type=str,
        default=None,
        help="ID de correlação para ops_action_audit.",
    )
    p.add_argument("--json", action="store_true", help="Imprime resumo JSON.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    correlation_id = str(args.correlation_id or f"fix-orphan-{uuid.uuid4().hex[:16]}")

    db = SessionLocal()
    try:
        summary = run_fix_orphan_credits(
            db,
            dry_run=bool(args.dry_run),
            limit=int(args.limit),
            credit_id=args.credit_id,
            correlation_id=correlation_id,
        )
    except Exception as exc:
        print(f"fix_orphan_credits failed: {exc}", file=sys.stderr)
        db.rollback()
        return 1
    finally:
        db.close()

    if args.json:
        print(json.dumps(summary, indent=2, default=str))
    else:
        mode = "DRY-RUN" if args.dry_run else "APPLY"
        print(f"[{mode}] correlation_id={correlation_id}")
        print(f"scanned={summary['scanned']} restored={summary['restored']} kept={summary['kept']}")
        for d in summary["decisions"]:
            print(
                f"  credit={d['credit_id']} order={d.get('order_id')} "
                f"action={d['action']} reason={d['reason']} order_status={d.get('order_status')}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
