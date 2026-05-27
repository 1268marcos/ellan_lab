# 01_source/order_pickup_service/app/health/health.py
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal, engine
from app.health.internal import verify_internal_token

logger = logging.getLogger("order_pickup_service")
router = APIRouter()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _table_readable(db: Session, table_sql: str) -> bool:
    """True se ``SELECT 1 FROM <tabela>`` funciona (tabela existe e é acessível)."""
    try:
        db.execute(text(f"SELECT 1 FROM {table_sql} LIMIT 1"))
        return True
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return False


def check_credit_consistency(db: Session) -> dict[str, Any]:
    """
    Verifica créditos em USED sem order_id (NULL ou vazio) e USED com order_id órfão.
    """
    started = time.perf_counter()
    out: dict[str, Any] = {
        "check": "credit_consistency",
        "used_without_order_id_count": 0,
        "used_orphan_order_id_count": 0,
        "status": "healthy",
        "elapsed_ms": 0,
    }
    if not _table_readable(db, "credits"):
        out["status"] = "skipped"
        out["message"] = "tabela credits não existe neste banco"
        out["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
        return out

    try:
        row = db.execute(
            text(
                """
                SELECT COUNT(*) AS n
                FROM credits
                WHERE status = 'USED'
                  AND (order_id IS NULL OR TRIM(order_id) = '')
                """
            )
        ).mappings().first()
        bad = int((row or {}).get("n") or 0)
        out["used_without_order_id_count"] = bad

        orphan = 0
        if _table_readable(db, "orders"):
            row2 = db.execute(
                text(
                    """
                    SELECT COUNT(*) AS n
                    FROM credits c
                    WHERE c.status = 'USED'
                      AND c.order_id IS NOT NULL
                      AND TRIM(c.order_id) <> ''
                      AND NOT EXISTS (SELECT 1 FROM orders o WHERE o.id = c.order_id)
                    """
                )
            ).mappings().first()
            orphan = int((row2 or {}).get("n") or 0)
        out["used_orphan_order_id_count"] = orphan

        if bad > 0 or orphan > 0:
            out["status"] = "unhealthy"
            out["message"] = (
                f"Encontrados {bad} crédito(s) USED sem order_id e {orphan} USED com pedido inexistente."
            )
        else:
            out["message"] = "Nenhuma inconsistência de crédito USED vs order_id."
    except Exception as exc:
        logger.exception("check_credit_consistency_failed")
        out["status"] = "error"
        out["error_type"] = exc.__class__.__name__
        out["message"] = str(exc)[:500]
    out["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
    return out


def check_pending_reconciliation_age(db: Session, *, max_age_sec: int = 3600) -> dict[str, Any]:
    """
    Alerta se pendências de reconciliação (PENDING/PROCESSING/FAILED) têm created_at > max_age_sec.
    """
    started = time.perf_counter()
    out: dict[str, Any] = {
        "check": "reconciliation_pending_age",
        "max_age_sec": max_age_sec,
        "stale_count": 0,
        "oldest_age_sec": None,
        "samples": [],
        "status": "healthy",
        "elapsed_ms": 0,
    }
    if not _table_readable(db, "reconciliation_pending"):
        out["status"] = "skipped"
        out["message"] = "tabela reconciliation_pending não existe"
        out["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
        return out

    now = _utc_now()
    try:
        rows = db.execute(
            text(
                """
                SELECT id, order_id, reason, status, created_at
                FROM reconciliation_pending
                WHERE status IN ('PENDING', 'PROCESSING', 'FAILED')
                ORDER BY created_at ASC
                LIMIT 500
                """
            )
        ).mappings().all()

        stale: list[dict[str, Any]] = []
        oldest_age: float | None = None
        for r in rows:
            created = r.get("created_at")
            if created is None:
                continue
            if getattr(created, "tzinfo", None) is None:
                created = created.replace(tzinfo=timezone.utc)
            age_sec = max(0.0, (now - created).total_seconds())
            if oldest_age is None or age_sec > oldest_age:
                oldest_age = age_sec
            if age_sec > max_age_sec:
                stale.append(
                    {
                        "id": r.get("id"),
                        "order_id": r.get("order_id"),
                        "reason": r.get("reason"),
                        "status": r.get("status"),
                        "age_sec": int(age_sec),
                    }
                )

        out["stale_count"] = len(stale)
        out["oldest_age_sec"] = int(oldest_age) if oldest_age is not None else None
        out["samples"] = stale[:20]

        if stale:
            out["status"] = "warning"
            out["message"] = (
                f"{len(stale)} pendência(s) com idade > {max_age_sec}s (amostra de até 20 em samples)."
            )
        else:
            out["message"] = "Nenhuma pendência acima do limite de idade."
    except Exception as exc:
        logger.exception("check_pending_reconciliation_age_failed")
        out["status"] = "error"
        out["error_type"] = exc.__class__.__name__
        out["message"] = str(exc)[:500]
    out["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
    return out


def check_redis_connection() -> dict[str, Any]:
    """
    Ping no Redis quando REDIS_URL está configurado (settings.redis_url).
    """
    started = time.perf_counter()
    url = str(getattr(settings, "redis_url", None) or "").strip()
    out: dict[str, Any] = {
        "check": "redis_connection",
        "configured": bool(url),
        "status": "skipped",
        "elapsed_ms": 0,
    }
    if not url:
        out["message"] = "REDIS_URL não configurado; verificação ignorada."
        out["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
        return out

    try:
        import redis as redis_lib

        client = redis_lib.from_url(
            url,
            decode_responses=False,
            socket_connect_timeout=2.0,
            socket_timeout=2.0,
        )
        t0 = time.perf_counter()
        client.ping()
        latency_ms = int((time.perf_counter() - t0) * 1000)
        out["status"] = "healthy"
        out["message"] = "PING OK"
        out["latency_ms"] = latency_ms
        try:
            client.close()
        except Exception:
            pass
    except Exception as exc:
        logger.warning(
            "check_redis_connection_failed",
            extra={"error_type": exc.__class__.__name__},
        )
        out["status"] = "unhealthy"
        out["error_type"] = exc.__class__.__name__
        out["message"] = str(exc)[:500]
    out["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
    return out


def check_runtime_sync_lag(db: Session, *, max_lockers_for_divergence: int = 15) -> dict[str, Any]:
    """
    Fila runtime_sync_queue vs estado runtime (hardware): idade da pendência mais antiga
    e divergências de slots (runtime vs Postgres) para lockers com itens pendentes na fila.
    """
    started = time.perf_counter()
    out: dict[str, Any] = {
        "check": "runtime_sync_lag",
        "queue_pending_count": 0,
        "queue_oldest_pending_age_sec": None,
        "divergence_lockers_scanned": 0,
        "total_slot_divergences": 0,
        "per_locker": [],
        "status": "healthy",
        "elapsed_ms": 0,
    }

    if not _table_readable(db, "runtime_sync_queue"):
        out["status"] = "skipped"
        out["message"] = "tabela runtime_sync_queue não existe"
        out["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
        return out

    now = _utc_now()
    try:
        agg = db.execute(
            text(
                """
                SELECT COUNT(*) AS c, MIN(created_at) AS oldest
                FROM runtime_sync_queue
                WHERE status IN ('PENDING', 'PROCESSING')
                """
            )
        ).mappings().first()
        pending_count = int((agg or {}).get("c") or 0)
        oldest_created = (agg or {}).get("oldest")
        out["queue_pending_count"] = pending_count

        if oldest_created is not None:
            oc = oldest_created
            if getattr(oc, "tzinfo", None) is None:
                oc = oc.replace(tzinfo=timezone.utc)
            out["queue_oldest_pending_age_sec"] = int(max(0.0, (now - oc).total_seconds()))

        if engine.dialect.name != "postgresql":
            out["message"] = "Divergências runtime↔PG só calculadas em PostgreSQL; fila reportada acima."
            if pending_count > 0 and (out["queue_oldest_pending_age_sec"] or 0) > 3600:
                out["status"] = "warning"
            out["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
            return out

        locker_rows = db.execute(
            text(
                """
                SELECT DISTINCT q.locker_id
                FROM runtime_sync_queue q
                WHERE q.status IN ('PENDING', 'PROCESSING')
                ORDER BY q.locker_id
                LIMIT :lim
                """
            ),
            {"lim": int(max_lockers_for_divergence)},
        ).mappings().all()

        from app.services import runtime_slot_sync_service as rss

        for lr in locker_rows:
            lid = str(lr.get("locker_id") or "").strip()
            if not lid:
                continue
            region_row = db.execute(
                text("SELECT region FROM lockers WHERE id = :id LIMIT 1"),
                {"id": lid},
            ).mappings().first()
            region = str(region_row.get("region") or "").strip() or None if region_row else None
            try:
                divs = rss.compute_slot_divergences(db, lid, region)
                if divs is None:
                    divs = []
                n = len(divs)
            except Exception as exc:
                out["per_locker"].append(
                    {"locker_id": lid, "divergences_count": -1, "error": str(exc)[:300]}
                )
                continue
            out["per_locker"].append({"locker_id": lid, "divergences_count": n})
            out["total_slot_divergences"] += n
            out["divergence_lockers_scanned"] += 1

        if pending_count > 0 and (out["queue_oldest_pending_age_sec"] or 0) > 3600:
            out["status"] = "warning"
            out["message"] = "Itens na fila de runtime sync com mais de 1 hora."
        elif out["total_slot_divergences"] > 0:
            out["status"] = "warning"
            out["message"] = (
                f"Divergência entre runtime e locker_slots em {out['divergence_lockers_scanned']} "
                f"locker(s) com fila pendente (total {out['total_slot_divergences']} slot(s))."
            )
        else:
            out["message"] = "Fila runtime sync e amostra de divergências runtime↔PG OK."
    except Exception as exc:
        logger.exception("check_runtime_sync_lag_failed")
        out["status"] = "error"
        out["error_type"] = exc.__class__.__name__
        out["message"] = str(exc)[:500]
    out["elapsed_ms"] = int((time.perf_counter() - started) * 1000)
    return out


@router.get("/health")
async def health_check():
    """Health check simples"""
    logger.info("Health check acessado")
    return {
        "status": "healthy",
        "service": "order_pickup_service",
        "timestamp": _utc_now(),
    }


@router.get("/health/ready")
async def ready_check():
    """Ready check"""
    return {"status": "ready"}


@router.get("/health/live")
async def live_check():
    """Live check"""
    return {"status": "alive"}


@router.get("/internal/health/credits")
async def internal_health_credits(_: bool = Depends(verify_internal_token)):
    db = SessionLocal()
    try:
        return {"timestamp": _utc_now(), **check_credit_consistency(db)}
    finally:
        db.close()


@router.get("/internal/health/reconciliation")
async def internal_health_reconciliation(_: bool = Depends(verify_internal_token)):
    db = SessionLocal()
    try:
        return {"timestamp": _utc_now(), **check_pending_reconciliation_age(db)}
    finally:
        db.close()


@router.get("/internal/health/runtime-sync")
async def internal_health_runtime_sync(_: bool = Depends(verify_internal_token)):
    db = SessionLocal()
    try:
        return {
            "timestamp": _utc_now(),
            **check_runtime_sync_lag(db),
            "redis": check_redis_connection(),
        }
    finally:
        db.close()
