# order_pickup_service/app/core/health/credits.py
from __future__ import annotations

import time
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.health.exceptions import HealthCheckError


def _compute_half_credit(amount_cents: int) -> int:
    return int(amount_cents) // 2


def check_credits(db: Session, *, sample_order_id: Optional[str] = None) -> Dict[str, Any]:
    started = time.perf_counter()
    details: Dict[str, Any] = {
        "rule": {},
        "orders_table": {"ok": False},
    }

    try:
        rule_ok = (_compute_half_credit(101) == 50) and (_compute_half_credit(100) == 50)
        details["rule"] = {
            "ok": rule_ok,
            "examples": {"101": _compute_half_credit(101), "100": _compute_half_credit(100)},
        }

        db.execute(text("SELECT 1"))

        table_exists = False
        try:
            r = db.execute(
                text("SELECT 1 FROM sqlite_master WHERE type='table' AND name='orders' LIMIT 1")
            ).fetchone()
            table_exists = r is not None
        except Exception:
            r = db.execute(
                text("SELECT 1 FROM information_schema.tables WHERE table_name='orders' LIMIT 1")
            ).fetchone()
            table_exists = r is not None

        if not table_exists:
            details["orders_table"] = {
                "ok": False,
                "status": "missing",
                "message": "Tabela 'orders' não encontrada para validar crédito em pedido real.",
            }
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            raise HealthCheckError(
                "credits",
                status="degraded",
                details=details,
                elapsed_ms=elapsed_ms,
                http_status_code=503,
            )

        details["orders_table"]["ok"] = True

        if sample_order_id:
            row = db.execute(
                text("SELECT id, amount_cents, status FROM orders WHERE id = :id LIMIT 1"),
                {"id": sample_order_id},
            ).fetchone()
        else:
            row = db.execute(
                text("SELECT id, amount_cents, status FROM orders ORDER BY created_at DESC LIMIT 1")
            ).fetchone()

        if not row:
            details["orders_table"]["sample"] = None
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            raise HealthCheckError(
                "credits",
                status="degraded",
                details=details,
                elapsed_ms=elapsed_ms,
                http_status_code=503,
            )

        order_id, amount_cents, status = row[0], int(row[1] or 0), row[2]
        details["orders_table"]["sample"] = {
            "order_id": order_id,
            "status": status,
            "amount_cents": amount_cents,
            "computed_credit_cents": _compute_half_credit(amount_cents),
        }

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        if not rule_ok:
            raise HealthCheckError(
                "credits",
                status="degraded",
                details=details,
                elapsed_ms=elapsed_ms,
                http_status_code=503,
            )

        return {"ok": True, "check": "credits", "status": "ok", "elapsed_ms": elapsed_ms, "details": details}

    except HealthCheckError:
        raise
    except Exception as e:
        details["error"] = {"type": e.__class__.__name__, "message": str(e)}
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        raise HealthCheckError(
            "credits",
            status="error",
            details=details,
            elapsed_ms=elapsed_ms,
            http_status_code=503,
        )