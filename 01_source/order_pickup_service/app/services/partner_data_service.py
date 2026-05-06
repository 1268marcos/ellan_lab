from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session


_MEM_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_MEM_TTL_SEC = 30
_REDIS_CLIENT = None
_REDIS_ATTEMPTED = False
_REDIS_TTL_SEC = 30


@dataclass(frozen=True)
class PartnerAuthContext:
    partner_id: str
    api_key_hash: str


def _normalize_partner_id(partner_id: str) -> str:
    normalized = str(partner_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=404, detail="partner not found")
    return normalized


def _normalize_locker_id(locker_id: str) -> str:
    normalized = str(locker_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=404, detail="locker not found")
    return normalized


def _hash_api_key(raw_api_key: str) -> str:
    return hashlib.sha256(raw_api_key.encode("utf-8")).hexdigest()


def validate_partner_access(db: Session, partner_id: str, raw_api_key: str) -> PartnerAuthContext:
    normalized_partner_id = _normalize_partner_id(partner_id)
    api_key = str(raw_api_key or "").strip()
    if not api_key:
        raise HTTPException(status_code=403, detail="access denied")
    api_key_hash = _hash_api_key(api_key)
    api_key_row = db.execute(
        text(
            """
            SELECT id
            FROM partner_api_keys
            WHERE partner_id = :partner_id
              AND key_hash = :key_hash
              AND revoked_at IS NULL
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"partner_id": normalized_partner_id, "key_hash": api_key_hash},
    ).mappings().first()
    if not api_key_row:
        raise HTTPException(status_code=403, detail="access denied")
    partner_row = db.execute(
        text(
            """
            SELECT id
            FROM ecommerce_partners
            WHERE id = :partner_id
            LIMIT 1
            """
        ),
        {"partner_id": normalized_partner_id},
    ).mappings().first()
    if not partner_row:
        raise HTTPException(status_code=404, detail="partner not found")
    return PartnerAuthContext(partner_id=normalized_partner_id, api_key_hash=api_key_hash)


def _get_redis_client():
    global _REDIS_CLIENT, _REDIS_ATTEMPTED
    if _REDIS_ATTEMPTED:
        return _REDIS_CLIENT
    _REDIS_ATTEMPTED = True
    redis_host = str(os.getenv("REDIS_INTERNAL", "")).strip()
    if not redis_host:
        return None
    try:
        import redis  # type: ignore

        _REDIS_CLIENT = redis.Redis(host=redis_host, port=6379, db=0, socket_timeout=0.3, socket_connect_timeout=0.3)
    except Exception:
        _REDIS_CLIENT = None
    return _REDIS_CLIENT


def _cache_get(cache_key: str) -> dict[str, Any] | None:
    redis_client = _get_redis_client()
    if redis_client is not None:
        try:
            cached_raw = redis_client.get(cache_key)
            if cached_raw:
                return json.loads(cached_raw)
        except Exception:
            pass
    cached = _MEM_CACHE.get(cache_key)
    if not cached:
        return None
    expires_at, payload = cached
    if expires_at < time.time():
        _MEM_CACHE.pop(cache_key, None)
        return None
    return payload


def _cache_set(cache_key: str, payload: dict[str, Any]) -> None:
    redis_client = _get_redis_client()
    if redis_client is not None:
        try:
            redis_client.setex(cache_key, _REDIS_TTL_SEC, json.dumps(payload, default=str))
            return
        except Exception:
            pass
    _MEM_CACHE[cache_key] = (time.time() + _MEM_TTL_SEC, payload)


def _ensure_locker_allowed_for_partner(db: Session, partner_id: str, locker_id: str) -> None:
    assignment_row = db.execute(
        text(
            """
            SELECT 1
            FROM partner_service_areas psa
            WHERE psa.partner_id = :partner_id
              AND psa.locker_id = :locker_id
              AND psa.is_active IS TRUE
              AND (psa.valid_until IS NULL OR psa.valid_until >= CURRENT_DATE)
            LIMIT 1
            """
        ),
        {"partner_id": partner_id, "locker_id": locker_id},
    ).mappings().first()
    if not assignment_row:
        raise HTTPException(status_code=403, detail="access denied")


def get_locker_summary(db: Session, locker_id: str, partner_id: str) -> dict[str, Any]:
    normalized_locker_id = _normalize_locker_id(locker_id)
    normalized_partner_id = _normalize_partner_id(partner_id)
    cache_key = f"partner:locker-summary:{normalized_partner_id}:{normalized_locker_id}"
    cached_payload = _cache_get(cache_key)
    if cached_payload is not None:
        return cached_payload

    locker_row = db.execute(
        text(
            """
            SELECT
                l.id::text AS locker_id,
                l.display_name::text AS display_name,
                l.region::text AS region,
                l.city::text AS city,
                l.state::text AS state,
                l.active AS active,
                l.slots_count AS slots_count,
                l.slots_available AS slots_available,
                l.updated_at AS updated_at
            FROM lockers l
            WHERE l.id = :locker_id
              AND l.deleted_at IS NULL
            LIMIT 1
            """
        ),
        {"locker_id": normalized_locker_id},
    ).mappings().first()
    if not locker_row:
        raise HTTPException(status_code=404, detail="locker not found")

    _ensure_locker_allowed_for_partner(db, normalized_partner_id, normalized_locker_id)

    pickups_count_row = db.execute(
        text(
            """
            SELECT COUNT(*)::integer AS active_pickups
            FROM pickups p
            WHERE p.locker_id = :locker_id
              AND p.status = 'ACTIVE'
            """
        ),
        {"locker_id": normalized_locker_id},
    ).mappings().first()

    payload = {
        "locker_id": locker_row["locker_id"],
        "display_name": locker_row.get("display_name"),
        "region": locker_row.get("region"),
        "city": locker_row.get("city"),
        "state": locker_row.get("state"),
        "active": bool(locker_row.get("active")),
        "slots_count": int(locker_row.get("slots_count") or 0),
        "slots_available": int(locker_row.get("slots_available") or 0),
        "active_pickups": int((pickups_count_row or {}).get("active_pickups") or 0),
        "updated_at": str(locker_row.get("updated_at")) if locker_row.get("updated_at") else None,
    }
    _cache_set(cache_key, payload)
    return payload


def get_active_pickups(db: Session, partner_id: str, limit: int = 50) -> dict[str, Any]:
    normalized_partner_id = _normalize_partner_id(partner_id)
    safe_limit = max(1, min(int(limit), 200))
    cache_key = f"partner:active-pickups:{normalized_partner_id}:{safe_limit}"
    cached_payload = _cache_get(cache_key)
    if cached_payload is not None:
        return cached_payload

    partner_row = db.execute(
        text(
            """
            SELECT id
            FROM ecommerce_partners
            WHERE id = :partner_id
            LIMIT 1
            """
        ),
        {"partner_id": normalized_partner_id},
    ).mappings().first()
    if not partner_row:
        raise HTTPException(status_code=404, detail="partner not found")

    rows = db.execute(
        text(
            """
            SELECT
                p.id::text AS pickup_id,
                p.order_id::text AS order_id,
                p.locker_id::text AS locker_id,
                p.slot::text AS slot,
                p.status::text AS status,
                p.lifecycle_stage::text AS lifecycle_stage,
                p.ready_at AS ready_at,
                p.expires_at AS expires_at,
                p.updated_at AS updated_at
            FROM pickups p
            INNER JOIN orders o ON o.id = p.order_id
            INNER JOIN partner_service_areas psa
                ON psa.partner_id = :partner_id
               AND psa.locker_id = p.locker_id
               AND psa.is_active IS TRUE
               AND (psa.valid_until IS NULL OR psa.valid_until >= CURRENT_DATE)
            WHERE o.ecommerce_partner_id = :partner_id
              AND p.status = 'ACTIVE'
            ORDER BY p.updated_at DESC
            LIMIT :limit
            """
        ),
        {"partner_id": normalized_partner_id, "limit": safe_limit},
    ).mappings().all()

    items = [
        {
            "pickup_id": str(row.get("pickup_id") or ""),
            "order_id": str(row.get("order_id") or ""),
            "locker_id": row.get("locker_id"),
            "slot": row.get("slot"),
            "status": row.get("status"),
            "lifecycle_stage": row.get("lifecycle_stage"),
            "ready_at": str(row.get("ready_at")) if row.get("ready_at") else None,
            "expires_at": str(row.get("expires_at")) if row.get("expires_at") else None,
            "updated_at": str(row.get("updated_at")) if row.get("updated_at") else None,
        }
        for row in rows
    ]
    payload = {
        "partner_id": normalized_partner_id,
        "total": len(items),
        "limit": safe_limit,
        "items": items,
    }
    _cache_set(cache_key, payload)
    return payload
