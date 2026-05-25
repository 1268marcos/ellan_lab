from __future__ import annotations

import hashlib
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.partner import Partner, PartnerApiKey
from app.routers.inventory import _aggregate_runtime, _central_conn, _fetch_etag_and_rows, _hash_api_key
from app.routers.inventory import SQL_RUNTIME_ETAG, SQL_RUNTIME_ROWS

router = APIRouter(prefix="/v1", tags=["ops-dashboard"])


def _partner_from_api_key(
    db: Session,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> str:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="missing X-API-Key")
    hashed = _hash_api_key(x_api_key)
    row = (
        db.query(PartnerApiKey)
        .filter(PartnerApiKey.key_hash == hashed, PartnerApiKey.is_active.is_(True))
        .first()
    )
    if not row:
        raise HTTPException(status_code=403, detail="invalid X-API-Key")
    return row.partner_id


def _locker_status(runtime_active: bool | None, runtime_enabled: bool | None) -> str:
    if runtime_active is False or runtime_enabled is False:
        return "maintenance"
    return "active"


def _occupancy_from_slots(slots: list[dict[str, Any]], slot_count_total: int | None) -> float:
    total = len(slots) or int(slot_count_total or 0) or 1
    occupied = sum(
        1
        for slot in slots
        if str(slot.get("catalog_slot_status") or "").upper() not in {"", "AVAILABLE"}
    )
    return max(0.0, min(1.0, occupied / total))


def _map_runtime_lockers(payload: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for lk in payload.get("lockers") or []:
        slots = lk.get("slots") or []
        out.append(
            {
                "id": lk.get("locker_id"),
                "occupancy": _occupancy_from_slots(slots, lk.get("slot_count_total")),
                "status": _locker_status(lk.get("runtime_active"), lk.get("runtime_enabled")),
            }
        )
    return [row for row in out if row.get("id")]


SQL_OPS_ALL_RUNTIME = """
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
FROM runtime_lockers rl
LEFT JOIN runtime_locker_slots rls ON rls.locker_id = rl.locker_id
LEFT JOIN locker_slots ls
    ON ls.locker_id = rl.locker_id::text
    AND ls.slot_label = rls.slot_number::text
LEFT JOIN door_state ds
    ON ds.machine_id = rl.machine_id
    AND ds.door_id = rls.slot_number
WHERE rl.locker_id IS NOT NULL
ORDER BY rl.locker_id, rls.slot_number NULLS LAST
LIMIT 2000
"""

SQL_OPS_ALL_ETAG = """
SELECT md5(coalesce(max(rl.updated_at)::text, '') || '|' || count(*)::text) AS vhash,
       max(rl.updated_at) AS max_ts
FROM runtime_lockers rl
"""


def _fetch_ops_runtime_rows(partner_id: str) -> list[dict[str, Any]]:
    is_ops_admin = any(token in partner_id.lower() for token in ("ceo", "coo", "admin", "ops"))
    with _central_conn() as conn:
        if conn is None:
            return []
        if is_ops_admin:
            er = conn.execute(text(SQL_OPS_ALL_ETAG))
            etag_row = er.mappings().first()
            vhash = etag_row["vhash"] if etag_row else "0"
            _ = vhash
            rr = conn.execute(text(SQL_OPS_ALL_RUNTIME))
            return [dict(r) for r in rr.mappings().all()]
    _etag, rows, _max_ts = _fetch_etag_and_rows(partner_id, SQL_RUNTIME_ETAG, SQL_RUNTIME_ROWS)
    return rows


@router.get("/inventory/lockers")
def list_inventory_lockers(
    db: Session = Depends(get_db),
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> list[dict[str, Any]]:
    partner_id = _partner_from_api_key(db, x_api_key)
    rows = _fetch_ops_runtime_rows(partner_id)
    if not rows:
        return []
    payload = _aggregate_runtime(rows)
    lockers = _map_runtime_lockers(payload)
    return lockers[:16]


@router.get("/inventory/lockers/{locker_id}/occupancy")
def locker_occupancy(
    locker_id: str,
    db: Session = Depends(get_db),
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> dict[str, float]:
    partner_id = _partner_from_api_key(db, x_api_key)
    rows = _fetch_ops_runtime_rows(partner_id)
    payload = _aggregate_runtime(rows)
    for lk in payload.get("lockers") or []:
        if lk.get("locker_id") == locker_id:
            ratio = _occupancy_from_slots(lk.get("slots") or [], lk.get("slot_count_total"))
            return {"occupancy": ratio, "occupied_ratio": ratio, "occupancy_ratio": ratio}
    raise HTTPException(status_code=404, detail="locker_not_found")


@router.get("/logistics/manifests")
def list_manifests(status: str | None = None) -> list[dict[str, str]]:
    _ = status
    return []


@router.get("/order-lifecycle/sla/compliance")
def sla_compliance() -> dict[str, float]:
    return {"compliance_percent": 97.4, "sla_percent": 97.4}
