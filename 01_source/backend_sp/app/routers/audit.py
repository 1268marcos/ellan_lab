# 01_source/backend_sp/app/routers/audit.py
import os
import json
import hashlib
from fastapi import APIRouter, Query, Header, HTTPException, Request
from typing import Optional, List, Dict, Any

from app.core.db import get_conn

router = APIRouter(prefix="/audit", tags=["audit"])

INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN")  # opcional (recomendado)
DEFAULT_MACHINE_ID = os.getenv("MACHINE_ID", "CACIFO-XX-001")

def _require_internal_token(x_internal_token: str | None):
    if INTERNAL_TOKEN and x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(
            status_code=401,
            detail={"type": "UNAUTHORIZED", "message": "invalid internal token", "retryable": False},
        )

def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _sha256_prefixed(s: str) -> str:
    return "sha256:" + _sha256_hex(s)

def _normalize_hash(h: Optional[str]) -> Optional[str]:
    """
    Compat: aceita hash antigo sem prefixo e normaliza para 'sha256:<hex>'.
    """
    if h is None:
        return None
    h = str(h)
    if h.startswith("sha256:"):
        return h
    # assume legacy hex
    if len(h) == 64:
        return "sha256:" + h
    return h  # não mexe se formato desconhecido

def _safe_json_loads(s: str) -> dict:
    try:
        return json.loads(s)
    except Exception:
        return {"_raw": s, "_parse_error": True}

@router.get("/events")
def list_events(
    request: Request,
    machine_id: str = Query(default=DEFAULT_MACHINE_ID),
    door_id: Optional[int] = Query(None),
    limit: int = Query(200, ge=1, le=2000),
    x_internal_token: str | None = Header(default=None),
) -> Dict[str, Any]:
    """
    Lista eventos do SQLite (append-only).
    Retorna JSON rico e resiliente a payload inválido.
    """
    _require_internal_token(x_internal_token)

    try:
        conn = get_conn()

        if door_id is None:
            cur = conn.execute(
                """
                SELECT id, ts, machine_id, door_id, event_type, severity, correlation_id,
                       sale_id, command_id, old_state, new_state, payload_json, prev_hash, hash
                FROM events
                WHERE machine_id = ?
                ORDER BY id DESC
                LIMIT ?;
                """,
                (machine_id, limit),
            )
        else:
            cur = conn.execute(
                """
                SELECT id, ts, machine_id, door_id, event_type, severity, correlation_id,
                       sale_id, command_id, old_state, new_state, payload_json, prev_hash, hash
                FROM events
                WHERE machine_id = ? AND door_id = ?
                ORDER BY id DESC
                LIMIT ?;
                """,
                (machine_id, door_id, limit),
            )

        rows = cur.fetchall()
        out = []
        for r in rows:
            payload_json = r[11] or "{}"
            out.append(
                {
                    "event_id": r[0],
                    "ts": r[1],
                    "machine_id": r[2],
                    "door_id": r[3],
                    "event_type": r[4],
                    "severity": r[5],
                    "correlation_id": r[6],
                    "sale_id": r[7],
                    "command_id": r[8],
                    "old_state": r[9],
                    "new_state": r[10],
                    "payload": _safe_json_loads(payload_json),
                    "payload_json": payload_json,
                    "prev_hash": _normalize_hash(r[12]),
                    "hash": _normalize_hash(r[13]),
                }
            )

        return {
            "ok": True,
            "endpoint": str(request.url.path),
            "machine_id": machine_id,
            "door_id": door_id,
            "limit": limit,
            "returned": len(out),
            "events": out,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "AUDIT_LIST_EVENTS_FAILED",
                "message": str(e),
                "retryable": True,
                "endpoint": str(request.url.path),
                "machine_id": machine_id,
                "door_id": door_id,
            },
        )

@router.get("/verify")
def verify_chain(
    request: Request,
    machine_id: str = Query(default=DEFAULT_MACHINE_ID),
    max_events: int = Query(5000, ge=1, le=50000),
    strict_salt: bool = Query(default=True, description="Se true, falha se LOG_HASH_SALT estiver vazio"),
    stop_on_first_error: bool = Query(default=True, description="Se false, acumula mismatches (mais lento)"),
    x_internal_token: str | None = Header(default=None),
) -> Dict[str, Any]:
    """
    Verifica integridade da cadeia:
    - prev_hash encadeado
    - hash recalculado com SALT (sha256:<hex>)
    Compatível com hashes legacy sem prefixo.
    """
    _require_internal_token(x_internal_token)

    salt = os.getenv("LOG_HASH_SALT", "")

    if strict_salt and not salt:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "SALT_NOT_SET",
                "message": "LOG_HASH_SALT is not set; cannot verify chain in strict mode",
                "retryable": False,
                "endpoint": str(request.url.path),
                "machine_id": machine_id,
            },
        )

    try:
        conn = get_conn()
        cur = conn.execute(
            """
            SELECT id, ts, machine_id, door_id, event_type, severity,
                   correlation_id, sale_id, command_id,
                   old_state, new_state, payload_json,
                   prev_hash, hash
            FROM events
            WHERE machine_id = ?
            ORDER BY id ASC
            LIMIT ?;
            """,
            (machine_id, max_events),
        )
        rows = cur.fetchall()

        prev_norm = None
        mismatches = []
        checked = 0

        for r in rows:
            (
                event_id,
                ts,
                mid,
                door_id,
                event_type,
                severity,
                correlation_id,
                sale_id,
                command_id,
                old_state,
                new_state,
                payload_json,
                prev_hash,
                h,
            ) = r

            prev_hash_norm = _normalize_hash(prev_hash)
            h_norm = _normalize_hash(h)

            # 1) prev_hash chain check
            if prev_hash_norm != prev_norm:
                mismatches.append({
                    "event_id": event_id,
                    "type": "PREV_HASH_MISMATCH",
                    "message": "prev_hash does not match previous event hash",
                    "expected_prev_hash": prev_norm,
                    "got_prev_hash": prev_hash_norm,
                })
                if stop_on_first_error:
                    break

            # 2) recompute hash
            base = "|".join(
                [
                    ts,
                    mid,
                    str(door_id or ""),
                    event_type,
                    severity,
                    correlation_id,
                    sale_id or "",
                    command_id or "",
                    old_state or "",
                    new_state or "",
                    payload_json or "{}",
                    (prev_hash_norm or "").replace("sha256:", ""),  # compat: base antiga pode ter sido sem prefixo
                    salt,
                ]
            )
            expected_norm = _sha256_prefixed(base)

            # 3) compare
            if h_norm != expected_norm:
                mismatches.append({
                    "event_id": event_id,
                    "type": "HASH_MISMATCH",
                    "message": "hash does not match recomputed value",
                    "expected_hash": expected_norm,
                    "got_hash": h_norm,
                })
                if stop_on_first_error:
                    break

            prev_norm = h_norm
            checked += 1

        ok = (len(mismatches) == 0)

        return {
            "ok": ok,
            "endpoint": str(request.url.path),
            "machine_id": machine_id,
            "events_checked": checked,
            "events_seen": len(rows),
            "salt_used": bool(salt),
            "strict_salt": strict_salt,
            "stop_on_first_error": stop_on_first_error,
            "mismatches": mismatches,
            "note": "Hash verification assumes current algorithm; legacy compatibility handled via normalization",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "AUDIT_VERIFY_FAILED",
                "message": str(e),
                "retryable": True,
                "endpoint": str(request.url.path),
                "machine_id": machine_id,
            },
        )