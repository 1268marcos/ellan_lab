# order_pickup_service/app/core/health/orders.py
from __future__ import annotations

import time
from typing import Any, Dict

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.health.exceptions import HealthCheckError


def check_orders(db: Session, *, sample_limit: int = 5) -> Dict[str, Any]:
    started = time.perf_counter()
    details: Dict[str, Any] = {
        "db": {"ok": False},
        "orders_table": {"ok": False},
    }

    try:
        db.execute(text("SELECT 1"))
        details["db"]["ok"] = True

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
                "error": "orders_table_missing",
                "message": "Tabela 'orders' não encontrada no schema atual.",
            }
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            raise HealthCheckError(
                "orders",
                status="error",
                details=details,
                elapsed_ms=elapsed_ms,
                http_status_code=503,
            )

        details["orders_table"]["ok"] = True

        total = db.execute(text("SELECT COUNT(*) FROM orders")).scalar()
        details["orders_table"]["count"] = int(total or 0)

        rows = db.execute(
            text(
                """
                SELECT id, status, channel, region, totem_id, sku_id, amount_cents, created_at
                FROM orders
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"limit": int(sample_limit)},
        ).fetchall()

        details["orders_table"]["sample"] = [
            {
                "id": r[0],
                "status": r[1],
                "channel": r[2],
                "region": r[3],
                "totem_id": r[4],
                "sku_id": r[5],
                "amount_cents": r[6],
                "created_at": str(r[7]),
            }
            for r in rows
        ]

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {"ok": True, "check": "orders", "status": "ok", "elapsed_ms": elapsed_ms, "details": details}

    except HealthCheckError:
        raise
    except Exception as e:
        details["error"] = {"type": e.__class__.__name__, "message": str(e)}
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        raise HealthCheckError(
            "orders",
            status="error",
            details=details,
            elapsed_ms=elapsed_ms,
            http_status_code=503,
        )