"""Logística COO — manifestos, roteirização e inventário por depot (locker)."""

from __future__ import annotations

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.allocation import Allocation, AllocationState
from app.models.locker import Locker
from app.models.logistics_manifest import LogisticsManifest as LogisticsManifestORM
from app.schemas.coo import DepotInventoryRow, LogisticsManifest, LogisticsRoutingRow


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


_ACTIVE_MANIFEST_STATUS = ("PENDING", "IN_TRANSIT")


class LogisticsService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_active_manifests(self, depot_id: str | None) -> list[LogisticsManifest]:
        db = self._db
        q = db.query(LogisticsManifestORM).filter(LogisticsManifestORM.status.in_(_ACTIVE_MANIFEST_STATUS))
        if depot_id and depot_id.strip():
            q = q.filter(LogisticsManifestORM.locker_id == depot_id.strip())
        rows = q.order_by(LogisticsManifestORM.manifest_date.desc()).limit(200).all()
        out: list[LogisticsManifest] = []
        for m in rows:
            md = m.manifest_date.isoformat() if m.manifest_date else ""
            out.append(
                LogisticsManifest(
                    id=str(m.id),
                    logistics_partner_id=str(m.logistics_partner_id),
                    locker_id=str(m.locker_id),
                    status=str(m.status),
                    manifest_date=md,
                    expected_parcel_count=int(m.expected_parcel_count or 0),
                    actual_parcel_count=int(m.actual_parcel_count or 0),
                    carrier_route_code=m.carrier_route_code,
                )
            )
        return out

    def get_realtime_routing(self, region: str | None) -> list[LogisticsRoutingRow]:
        db = self._db
        in_trans = case((LogisticsManifestORM.status == "IN_TRANSIT", 1), else_=0)

        q = (
            db.query(
                Locker.region,
                LogisticsManifestORM.locker_id,
                func.count(LogisticsManifestORM.id).label("active_manifests"),
                func.sum(in_trans).label("in_transit"),
            )
            .join(Locker, LogisticsManifestORM.locker_id == Locker.id)
            .filter(LogisticsManifestORM.status.in_(_ACTIVE_MANIFEST_STATUS))
        )
        if region and region.strip():
            q = q.filter(Locker.region == region.strip().upper())
        rows = (
            q.group_by(Locker.region, LogisticsManifestORM.locker_id)
            .order_by(Locker.region, LogisticsManifestORM.locker_id)
            .limit(300)
            .all()
        )

        result: list[LogisticsRoutingRow] = []
        for reg, locker_id, am, it in rows:
            result.append(
                LogisticsRoutingRow(
                    region=str(reg) if reg is not None else None,
                    locker_id=str(locker_id),
                    active_manifests=int(am or 0),
                    in_transit=int(it or 0),
                )
            )
        return result

    def get_inventory_by_depot(self, depot_id: str | None) -> list[DepotInventoryRow]:
        db = self._db
        reserved = func.sum(
            case(
                (
                    Allocation.state.in_(
                        [
                            AllocationState.RESERVED_PENDING_PAYMENT,
                            AllocationState.RESERVED_PAID_PENDING_PICKUP,
                            AllocationState.OPENED_FOR_PICKUP,
                        ]
                    ),
                    1,
                ),
                else_=0,
            )
        )

        q = (
            db.query(
                Locker.id,
                Locker.region,
                Locker.slots_count,
                func.coalesce(reserved, 0).label("reserved_hint"),
            )
            .outerjoin(Allocation, Allocation.locker_id == Locker.id)
            .group_by(Locker.id, Locker.region, Locker.slots_count)
        )
        if depot_id and depot_id.strip():
            q = q.filter(Locker.id == depot_id.strip())
        rows = q.order_by(Locker.region, Locker.id).limit(300).all()

        return [
            DepotInventoryRow(
                locker_id=str(lid),
                region=str(reg) if reg is not None else None,
                total_slots=int(slots or 0),
                reserved_hint=int(rh or 0),
            )
            for lid, reg, slots, rh in rows
        ]
