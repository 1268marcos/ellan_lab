from __future__ import annotations

import hashlib
import json
from collections.abc import Awaitable, Callable, Generator
from contextlib import contextmanager
from functools import lru_cache
from typing import Annotated, Any

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import get_settings
from app.core.database import get_db
from app.models.partner import Partner, PartnerApiKey

router = APIRouter(prefix="/api", tags=["inventory-bff"])

SQL_PARTNER_LOCKERS_CTE = """
WITH partner_lockers AS (
    SELECT DISTINCT psa.locker_id::text AS locker_id
    FROM partner_service_areas psa
    WHERE psa.partner_id = :partner_id
      AND psa.is_active IS TRUE
      AND (psa.valid_until IS NULL OR psa.valid_until >= CURRENT_DATE)
),
scoped_lockers AS (
    SELECT l.id::text AS locker_id,
           l.machine_id::text AS machine_id,
           l.display_name::text AS display_name
    FROM lockers l
    INNER JOIN partner_lockers pl ON pl.locker_id = l.id::text
)
"""

SQL_RUNTIME_ETAG = (
    SQL_PARTNER_LOCKERS_CTE
    + """
SELECT md5(
    concat_ws(
        '|',
        coalesce(max(rl.updated_at)::text, ''),
        coalesce(max(rls.updated_at)::text, ''),
        coalesce(max(ls.updated_at)::text, ''),
        coalesce(max(ds.updated_at)::text, ''),
        coalesce(max(a.updated_at)::text, '')
    )
) AS vhash,
max(
    greatest(
        coalesce(rl.updated_at::timestamptz, '-infinity'::timestamptz),
        coalesce(rls.updated_at::timestamptz, '-infinity'::timestamptz),
        coalesce(ls.updated_at, '-infinity'::timestamptz),
        coalesce(ds.updated_at::timestamptz, '-infinity'::timestamptz),
        coalesce(a.updated_at::timestamptz, '-infinity'::timestamptz)
    )
) AS max_ts
FROM scoped_lockers sl
LEFT JOIN runtime_lockers rl
    ON rl.locker_id = sl.locker_id
    OR (sl.machine_id IS NOT NULL AND rl.machine_id = sl.machine_id)
LEFT JOIN runtime_locker_slots rls
    ON rls.locker_id = rl.locker_id
LEFT JOIN locker_slots ls
    ON ls.locker_id = sl.locker_id
    AND ls.slot_label = rls.slot_number::text
LEFT JOIN door_state ds
    ON ds.machine_id = rl.machine_id
    AND ds.door_id = rls.slot_number
LEFT JOIN allocations a
    ON a.locker_id = sl.locker_id
    AND a.slot = rls.slot_number
"""
)

SQL_RUNTIME_ROWS = (
    SQL_PARTNER_LOCKERS_CTE
    + """
SELECT
    rl.locker_id::text AS runtime_locker_id,
    rl.machine_id::text AS machine_id,
    rl.display_name::text AS runtime_display_name,
    rl.region::text AS region,
    rl.active AS runtime_active,
    rl.runtime_enabled,
    rl.topology_version,
    rl.slot_count_total,
    rls.slot_number,
    rls.slot_size AS runtime_slot_size,
    rls.is_active AS runtime_slot_active,
    ls.id::text AS catalog_slot_id,
    ls.slot_label::text AS slot_label,
    ls.slot_size::text AS catalog_slot_size,
    ls.status::text AS catalog_slot_status,
    ds.state::text AS door_state,
    ds.updated_at AS door_updated_at
FROM scoped_lockers sl
INNER JOIN runtime_lockers rl
    ON rl.locker_id = sl.locker_id
    OR (sl.machine_id IS NOT NULL AND rl.machine_id = sl.machine_id)
LEFT JOIN runtime_locker_slots rls
    ON rls.locker_id = rl.locker_id
LEFT JOIN locker_slots ls
    ON ls.locker_id = sl.locker_id
    AND ls.slot_label = rls.slot_number::text
LEFT JOIN door_state ds
    ON ds.machine_id = rl.machine_id
    AND ds.door_id = rls.slot_number
WHERE rl.locker_id IS NOT NULL
ORDER BY rl.locker_id, rls.slot_number NULLS LAST
"""
)

SQL_ALLOCATIONS_ETAG = (
    SQL_PARTNER_LOCKERS_CTE
    + """
SELECT md5(coalesce(max(a.updated_at)::text, '') || '|' || count(*)::text) AS vhash,
       max(a.updated_at) AS max_ts
FROM allocations a
INNER JOIN partner_lockers pl ON pl.locker_id = a.locker_id
WHERE a.locker_id IS NOT NULL
"""
)

SQL_ALLOCATIONS_ROWS = (
    SQL_PARTNER_LOCKERS_CTE
    + """
SELECT
    a.id::text AS id,
    a.order_id::text AS order_id,
    a.locker_id::text AS locker_id,
    a.slot AS slot,
    a.state::text AS state,
    a.created_at,
    a.updated_at,
    a.allocated_at,
    a.released_at,
    a.slot_size::text AS slot_size,
    a.release_reason::text AS release_reason
FROM allocations a
INNER JOIN partner_lockers pl ON pl.locker_id = a.locker_id
WHERE a.locker_id IS NOT NULL
ORDER BY a.updated_at DESC NULLS LAST
LIMIT 500
"""
)


def _hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _partner_api_key_row(db: Session, partner_id: str, raw_key: str) -> PartnerApiKey | None:
    hashed = _hash_api_key(raw_key)
    return (
        db.query(PartnerApiKey)
        .filter(
            PartnerApiKey.partner_id == partner_id,
            PartnerApiKey.key_hash == hashed,
            PartnerApiKey.is_active.is_(True),
        )
        .first()
    )


def require_partner_inventory_auth(
    partner_id: str,
    db: Session = Depends(get_db),
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="missing X-API-Key")
    partner = db.query(Partner).filter(Partner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="partner not found")
    if not _partner_api_key_row(db, partner_id, x_api_key):
        raise HTTPException(status_code=403, detail="invalid X-API-Key for partner")


@lru_cache(maxsize=8)
def _engine_for(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True)


def _central_db_url() -> str | None:
    s = get_settings()
    if s.inventory_database_url:
        return s.inventory_database_url
    if s.database_url.startswith("postgresql"):
        return s.database_url
    return None


@contextmanager
def _central_conn() -> Generator[Connection | None, None, None]:
    url = _central_db_url()
    if not url:
        yield None
        return
    eng = _engine_for(url)
    conn = eng.connect()
    try:
        yield conn
    finally:
        conn.close()


def _etag_from_hash(vhash: str | None, scope: str) -> str:
    base = vhash or "0"
    return f'W/"{scope}:{base}"'


def _fetch_etag_and_rows(
    partner_id: str,
    etag_sql: str,
    rows_sql: str,
) -> tuple[str, list[dict[str, Any]], str | None]:
    with _central_conn() as conn:
        if conn is None:
            return _etag_from_hash(hashlib.md5(partner_id.encode()).hexdigest(), "noop"), [], None
        er = conn.execute(text(etag_sql), {"partner_id": partner_id})
        etag_row = er.mappings().first()
        vhash = etag_row["vhash"] if etag_row else None
        max_ts = etag_row["max_ts"] if etag_row else None
        etag = _etag_from_hash(vhash, "inv")
        rr = conn.execute(text(rows_sql), {"partner_id": partner_id})
        rows = [dict(r) for r in rr.mappings().all()]
        max_ts_str = str(max_ts) if max_ts is not None else None
        return etag, rows, max_ts_str


def _aggregate_runtime(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_locker: dict[str, dict[str, Any]] = {}
    for r in rows:
        lid = r.get("runtime_locker_id") or ""
        if not lid:
            continue
        if lid not in by_locker:
            by_locker[lid] = {
                "locker_id": lid,
                "machine_id": r.get("machine_id"),
                "display_name": r.get("runtime_display_name"),
                "region": r.get("region"),
                "runtime_active": r.get("runtime_active"),
                "runtime_enabled": r.get("runtime_enabled"),
                "topology_version": r.get("topology_version"),
                "slot_count_total": r.get("slot_count_total"),
                "slots": [],
            }
        by_locker[lid]["slots"].append(
            {
                "slot_number": r.get("slot_number"),
                "runtime_slot_size": r.get("runtime_slot_size"),
                "runtime_slot_active": r.get("runtime_slot_active"),
                "catalog_slot_id": r.get("catalog_slot_id"),
                "slot_label": r.get("slot_label"),
                "catalog_slot_size": r.get("catalog_slot_size"),
                "catalog_slot_status": r.get("catalog_slot_status"),
                "door_state": r.get("door_state"),
                "door_updated_at": str(r["door_updated_at"]) if r.get("door_updated_at") else None,
            }
        )
    lockers = list(by_locker.values())
    total_slots = sum(len(x["slots"]) for x in lockers)
    active_runtime = sum(1 for r in rows if r.get("runtime_slot_active") is True)
    catalog_available = sum(1 for r in rows if (r.get("catalog_slot_status") or "").upper() == "AVAILABLE")
    catalog_occupied = sum(
        1 for r in rows if r.get("catalog_slot_status") and (r.get("catalog_slot_status") or "").upper() != "AVAILABLE"
    )
    occupancy = {
        "total_runtime_slot_rows": total_slots,
        "active_runtime_slots": active_runtime,
        "catalog_available_slots": catalog_available,
        "catalog_non_available_slots": catalog_occupied,
    }
    return {"lockers": lockers, "occupancy": occupancy}


def _apply_cache_headers(response: Response, etag: str) -> None:
    response.headers["Cache-Control"] = "public, max-age=30"
    response.headers["ETag"] = etag


class InventoryPartnerCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        p = request.url.path
        if "/api/partners/" in p and "/inventory/" in p:
            if "Cache-Control" not in response.headers:
                response.headers["Cache-Control"] = "public, max-age=30"
        return response


@router.get("/partners/{partner_id}/inventory/runtime")
def get_partner_inventory_runtime(
    partner_id: str,
    request: Request,
    _auth: None = Depends(require_partner_inventory_auth),
) -> Response:
    if_none = request.headers.get("if-none-match")
    etag, rows, max_ts = _fetch_etag_and_rows(partner_id, SQL_RUNTIME_ETAG, SQL_RUNTIME_ROWS)
    cached = bool(if_none and if_none.strip() == etag)
    if cached:
        payload = {"success": True, "data": None, "meta": {"partner_id": partner_id, "etag": etag, "max_ts": max_ts}, "cached": True}
        out = Response(content=json.dumps(payload), media_type="application/json", status_code=200)
        _apply_cache_headers(out, etag)
        return out
    data = _aggregate_runtime(rows)
    payload = {
        "success": True,
        "data": data,
        "meta": {"partner_id": partner_id, "etag": etag, "max_ts": max_ts, "row_count": len(rows)},
        "cached": False,
    }
    out = Response(content=json.dumps(payload, default=str), media_type="application/json", status_code=200)
    _apply_cache_headers(out, etag)
    return out


@router.get("/partners/{partner_id}/inventory/allocations")
def get_partner_inventory_allocations(
    partner_id: str,
    request: Request,
    _auth: None = Depends(require_partner_inventory_auth),
) -> Response:
    if_none = request.headers.get("if-none-match")
    etag, rows, max_ts = _fetch_etag_and_rows(partner_id, SQL_ALLOCATIONS_ETAG, SQL_ALLOCATIONS_ROWS)
    cached = bool(if_none and if_none.strip() == etag)
    if cached:
        payload = {"success": True, "data": None, "meta": {"partner_id": partner_id, "etag": etag, "max_ts": max_ts}, "cached": True}
        out = Response(content=json.dumps(payload), media_type="application/json", status_code=200)
        _apply_cache_headers(out, etag)
        return out
    payload = {
        "success": True,
        "data": {"allocations": rows},
        "meta": {"partner_id": partner_id, "etag": etag, "max_ts": max_ts, "row_count": len(rows)},
        "cached": False,
    }
    out = Response(content=json.dumps(payload, default=str), media_type="application/json", status_code=200)
    _apply_cache_headers(out, etag)
    return out


def install_inventory_middleware(app: FastAPI) -> None:
    app.add_middleware(InventoryPartnerCacheMiddleware)
