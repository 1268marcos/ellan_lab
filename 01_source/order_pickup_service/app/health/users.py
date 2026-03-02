# order_pickup_service/app/core/health/users.py
from __future__ import annotations

import time
from typing import Any, Dict

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.security import JWT_SECRET, JWT_ALG
from app.core.health.exceptions import HealthCheckError


def check_users(db: Session, *, sample_limit: int = 5) -> Dict[str, Any]:
    started = time.perf_counter()
    details: Dict[str, Any] = {
        "jwt": {
            "alg": JWT_ALG,
            "secret_set": bool(JWT_SECRET and JWT_SECRET != "CHANGE_ME_IN_PROD"),
        },
        "users_table": {"ok": False},
    }

    try:
        if not details["jwt"]["secret_set"]:
            details["jwt"]["warning"] = "JWT_SECRET não definido (ou está no valor padrão)."

        db.execute(text("SELECT 1"))

        table_exists = False
        try:
            r = db.execute(
                text("SELECT 1 FROM sqlite_master WHERE type='table' AND name='users' LIMIT 1")
            ).fetchone()
            table_exists = r is not None
        except Exception:
            r = db.execute(
                text("SELECT 1 FROM information_schema.tables WHERE table_name='users' LIMIT 1")
            ).fetchone()
            table_exists = r is not None

        # Aqui você decidiu: “todos levantam exceção”.
        # Então: se não existir users, vira DEGRADED e levanta.
        if not table_exists:
            details["users_table"] = {
                "ok": False,
                "status": "missing",
                "message": "Tabela 'users' não existe neste ambiente.",
            }
            elapsed_ms = int((time.perf_counter() - started) * 1000)
            raise HealthCheckError(
                "users",
                status="degraded",
                details=details,
                elapsed_ms=elapsed_ms,
                http_status_code=503,
            )

        details["users_table"]["ok"] = True

        total = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        details["users_table"]["count"] = int(total or 0)

        active = None
        try:
            active = db.execute(text("SELECT COUNT(*) FROM users WHERE is_active = 1")).scalar()
        except Exception:
            active = None
        details["users_table"]["active_count"] = int(active) if active is not None else None

        rows = db.execute(
            text(
                """
                SELECT id, email, is_active, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"limit": int(sample_limit)},
        ).fetchall()

        details["users_table"]["sample"] = [
            {"id": r[0], "email": r[1], "is_active": r[2], "created_at": str(r[3])}
            for r in rows
        ]

        # JWT secret ausente = degraded
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        if not details["jwt"]["secret_set"]:
            raise HealthCheckError(
                "users",
                status="degraded",
                details=details,
                elapsed_ms=elapsed_ms,
                http_status_code=503,
            )

        return {"ok": True, "check": "users", "status": "ok", "elapsed_ms": elapsed_ms, "details": details}

    except HealthCheckError:
        raise
    except Exception as e:
        details["error"] = {"type": e.__class__.__name__, "message": str(e)}
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        raise HealthCheckError(
            "users",
            status="error",
            details=details,
            elapsed_ms=elapsed_ms,
            http_status_code=503,
        )