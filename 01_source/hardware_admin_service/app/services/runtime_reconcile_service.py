from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.clients.domain_http import DomainHttpError
from app.clients import runtime_client
from app.models.hardware_ops import HardwareSyncQueue
from app.models.runtime import RuntimeLocker
from app.schemas.runtime import RuntimeLockerIn, RuntimeLockerUpdate
from app.services.crypto_util import new_id
from app.services import runtime_service


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _admin_locker_payload(row: RuntimeLocker) -> dict[str, Any]:
    return {
        "locker_id": row.locker_id,
        "machine_id": row.machine_id,
        "display_name": row.display_name,
        "region": row.region,
        "country": row.country,
        "timezone": row.timezone,
        "operator_id": row.operator_id,
        "vendor_id": row.vendor_id,
        "mqtt_region": row.mqtt_region,
        "mqtt_locker_id": row.mqtt_locker_id,
        "slot_count_total": row.slot_count_total,
        "payment_methods_json": row.payment_methods_json or [],
    }


def _runtime_item_to_admin_in(item: dict[str, Any]) -> RuntimeLockerIn:
    lid = str(item.get("locker_id") or "")
    return RuntimeLockerIn(
        locker_id=lid,
        machine_id=str(item.get("machine_id") or f"MACHINE-{lid}"),
        display_name=str(item.get("display_name") or lid),
        region=str(item.get("region") or "BR-SP"),
        country=str(item.get("country") or "BR"),
        timezone=str(item.get("timezone") or "America/Sao_Paulo"),
        operator_id=item.get("operator_id"),
        vendor_id=item.get("vendor_id"),
        temperature_zone=str(item.get("temperature_zone") or "AMBIENT"),
        security_level=str(item.get("security_level") or "STANDARD"),
        active=bool(item.get("active", True)),
        runtime_enabled=bool(item.get("runtime_enabled", True)),
        mqtt_region=str(item.get("mqtt_region") or "br"),
        mqtt_locker_id=str(item.get("mqtt_locker_id") or lid.lower()),
        topology_version=int(item.get("topology_version") or 1),
        slot_count_total=int(item.get("slot_count_total") or 24),
        payment_methods_json=item.get("payment_methods_json") or [],
    )


def reconcile_runtime(db: Session) -> dict[str, Any]:
    admin_ids = {r.locker_id for r in db.query(RuntimeLocker).all()}
    try:
        runtime_items = runtime_client.list_runtime_registry_lockers()
        runtime_ids = {str(i.get("locker_id") or "") for i in runtime_items}
    except DomainHttpError as exc:
        return {
            "runtime_reachable": False,
            "error": exc.detail,
            "admin_only": sorted(admin_ids),
            "runtime_only": [],
            "in_both": [],
            "conflicts": [],
        }

    in_both = sorted(admin_ids & runtime_ids)
    admin_only = sorted(admin_ids - runtime_ids)
    runtime_only = sorted(runtime_ids - admin_ids)
    conflicts: list[dict[str, Any]] = []
    runtime_by_id = {str(i.get("locker_id")): i for i in runtime_items}
    for lid in in_both:
        admin = db.get(RuntimeLocker, lid)
        remote = runtime_by_id.get(lid) or {}
        if admin and str(admin.machine_id) != str(remote.get("machine_id") or ""):
            conflicts.append(
                {
                    "locker_id": lid,
                    "field": "machine_id",
                    "admin": admin.machine_id,
                    "runtime": remote.get("machine_id"),
                }
            )

    return {
        "runtime_reachable": True,
        "admin_count": len(admin_ids),
        "runtime_count": len(runtime_ids),
        "in_both": in_both,
        "admin_only": admin_only,
        "runtime_only": runtime_only,
        "conflicts": conflicts,
    }


def pull_from_runtime(db: Session, *, locker_id: str | None = None) -> dict[str, int]:
    items = runtime_client.list_runtime_registry_lockers()
    if locker_id:
        items = [i for i in items if str(i.get("locker_id") or "") == locker_id]

    inserted = updated = skipped = 0
    for item in items:
        lid = str(item.get("locker_id") or "")
        if not lid:
            skipped += 1
            continue
        existing = db.get(RuntimeLocker, lid)
        body = _runtime_item_to_admin_in(item)
        if existing:
            runtime_service.update_runtime_locker(
                db,
                lid,
                RuntimeLockerUpdate(
                    display_name=body.display_name,
                    operator_id=body.operator_id,
                    vendor_id=body.vendor_id,
                    slot_count_total=body.slot_count_total,
                    payment_methods_json=body.payment_methods_json,
                    active=body.active,
                    runtime_enabled=body.runtime_enabled,
                ),
            )
            updated += 1
        else:
            runtime_service.create_runtime_locker(db, body)
            inserted += 1

    return {"inserted": inserted, "updated": updated, "skipped": skipped, "pulled": len(items)}


def push_to_runtime(db: Session, *, locker_id: str | None = None, enqueue_only: bool = True) -> dict[str, Any]:
    q = db.query(RuntimeLocker)
    if locker_id:
        q = q.filter(RuntimeLocker.locker_id == locker_id)
    rows = q.all()

    queued = 0
    central_sync: dict[str, Any] | None = None
    for row in rows:
        payload = _admin_locker_payload(row)
        exists = (
            db.query(HardwareSyncQueue)
            .filter(
                HardwareSyncQueue.locker_id == row.locker_id,
                HardwareSyncQueue.operation == "RUNTIME_REGISTRY_PUSH",
                HardwareSyncQueue.status.in_(["PENDING", "RETRY"]),
            )
            .first()
        )
        if not exists:
            db.add(
                HardwareSyncQueue(
                    id=new_id(),
                    locker_id=row.locker_id,
                    operation="RUNTIME_REGISTRY_PUSH",
                    status="PENDING",
                    payload_json=payload,
                )
            )
            queued += 1

    if not enqueue_only:
        try:
            central_sync = runtime_client.trigger_runtime_central_sync(locker_id)
            for item in (
                db.query(HardwareSyncQueue)
                .filter(
                    HardwareSyncQueue.operation == "RUNTIME_REGISTRY_PUSH",
                    HardwareSyncQueue.status == "PENDING",
                )
                .all()
            ):
                if locker_id and item.locker_id != locker_id:
                    continue
                item.status = "COMPLETED"
                item.processed_at = _utcnow()
            db.commit()
        except DomainHttpError as exc:
            db.commit()
            return {"queued": queued, "central_sync": None, "error": exc.detail}

    db.commit()
    return {"queued": queued, "lockers": len(rows), "central_sync": central_sync}
