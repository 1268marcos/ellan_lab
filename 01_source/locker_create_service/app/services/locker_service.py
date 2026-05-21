from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.locker import Locker, LockerSlotConfig, ProductLockerConfig
from app.schemas.locker import (
    LockerBulkCreateIn,
    LockerCreateIn,
    LockerOut,
    LockerUpdateIn,
    ProductConfigOut,
    SlotConfigIn,
    SlotConfigOut,
)


def _default_slot_configs() -> list[dict]:
    return [
        {"slot_size": "P", "slot_count": 10, "available_count": 10, "width_mm": 100, "height_mm": 100, "depth_mm": 400, "max_weight_g": 2000},
        {"slot_size": "M", "slot_count": 10, "available_count": 10, "width_mm": 200, "height_mm": 200, "depth_mm": 400, "max_weight_g": 5000},
        {"slot_size": "G", "slot_count": 10, "available_count": 10, "width_mm": 300, "height_mm": 400, "depth_mm": 400, "max_weight_g": 10000},
    ]


def _apply_address(locker: Locker, body: LockerCreateIn) -> None:
    addr = body.address
    locker.city = body.city
    locker.state = body.state
    locker.country = body.country
    locker.district = body.district or (addr.district if addr else None)
    if addr:
        locker.address_line = addr.line
        locker.address_number = addr.number
        locker.address_extra = addr.extra
        locker.district = addr.district or locker.district
        locker.city = addr.city or locker.city
        locker.state = addr.state or locker.state
        locker.postal_code = addr.postal_code
        locker.country = addr.country or locker.country
        locker.latitude = addr.latitude
        locker.longitude = addr.longitude


def _total_slots(slot_rows: list[LockerSlotConfig]) -> int:
    return sum(int(sc.slot_count or 0) for sc in slot_rows)


def _copy_product_configs(db: Session, target_id: str, source_id: str) -> list[ProductLockerConfig]:
    source_rows = db.query(ProductLockerConfig).filter(ProductLockerConfig.locker_id == source_id).all()
    if not source_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"type": "SOURCE_LOCKER_NOT_FOUND", "message": f"Sem product_configs em {source_id}"},
        )
    created: list[ProductLockerConfig] = []
    for row in source_rows:
        cfg = ProductLockerConfig(
            locker_id=target_id,
            category=row.category,
            allowed=row.allowed,
            temperature_zone=row.temperature_zone,
        )
        db.add(cfg)
        created.append(cfg)
    return created


def locker_to_out(locker: Locker) -> LockerOut:
    return LockerOut(
        id=locker.id,
        display_name=locker.display_name,
        region=locker.region,
        city=locker.city,
        state=locker.state,
        country=locker.country,
        timezone=locker.timezone,
        active=locker.active,
        slots_count=locker.slots_count,
        slots_available=locker.slots_available,
        temperature_zone=locker.temperature_zone,
        security_level=locker.security_level,
        operator_id=locker.operator_id,
        has_camera=locker.has_camera,
        has_alarm=locker.has_alarm,
        has_kiosk=locker.has_kiosk,
        has_printer=locker.has_printer,
        has_card_reader=locker.has_card_reader,
        has_nfc=locker.has_nfc,
        slot_configs=[
            SlotConfigOut(
                slot_size=sc.slot_size,
                slot_count=sc.slot_count,
                available_count=sc.available_count if sc.available_count is not None else sc.slot_count,
                width_mm=sc.width_mm,
                height_mm=sc.height_mm,
                depth_mm=sc.depth_mm,
                max_weight_g=sc.max_weight_g,
            )
            for sc in locker.slot_configs
        ],
        product_configs=[
            ProductConfigOut(category=pc.category, allowed=pc.allowed, temperature_zone=pc.temperature_zone)
            for pc in locker.product_configs
        ],
        created_at=locker.created_at,
        updated_at=locker.updated_at,
    )


def get_locker_or_404(db: Session, locker_id: str) -> Locker:
    locker = db.query(Locker).filter(Locker.id == locker_id).first()
    if not locker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"type": "LOCKER_NOT_FOUND", "message": f"Locker {locker_id} nao encontrado"},
        )
    return locker


def create_locker(db: Session, body: LockerCreateIn) -> LockerOut:
    if db.query(Locker).filter(Locker.id == body.id).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"type": "LOCKER_ALREADY_EXISTS", "message": f"Locker {body.id} ja existe"},
        )

    now = datetime.now(timezone.utc)
    locker = Locker(
        id=body.id,
        external_id=body.external_id,
        display_name=body.display_name,
        description=body.description,
        region=body.region,
        site_id=body.site_id,
        timezone=body.timezone,
        operator_id=body.operator_id,
        active=body.active,
        temperature_zone=body.temperature_zone,
        security_level=body.security_level,
        has_camera=body.has_camera,
        has_alarm=body.has_alarm,
        has_kiosk=body.has_kiosk,
        has_printer=body.has_printer,
        has_card_reader=body.has_card_reader,
        has_nfc=body.has_nfc,
        created_at=now,
        updated_at=now,
    )
    _apply_address(locker, body)
    db.add(locker)
    db.flush()

    configs_in = body.slot_configs
    if not configs_in:
        configs_in = [SlotConfigIn(**row) for row in _default_slot_configs()]

    slot_rows: list[LockerSlotConfig] = []
    for slot in configs_in:
        sc = LockerSlotConfig(
            locker_id=locker.id,
            slot_size=slot.slot_size,
            slot_count=slot.slot_count,
            available_count=slot.available_count if slot.available_count is not None else slot.slot_count,
            width_mm=slot.width_mm,
            height_mm=slot.height_mm,
            depth_mm=slot.depth_mm,
            max_weight_g=slot.max_weight_g,
            created_at=now,
            updated_at=now,
        )
        db.add(sc)
        slot_rows.append(sc)

    if body.product_configs:
        for prod in body.product_configs:
            db.add(
                ProductLockerConfig(
                    locker_id=locker.id,
                    category=prod.category,
                    allowed=prod.allowed,
                    temperature_zone=prod.temperature_zone,
                    created_at=now,
                    updated_at=now,
                )
            )
    elif body.copy_product_configs_from:
        _copy_product_configs(db, locker.id, body.copy_product_configs_from)

    locker.slots_count = _total_slots(slot_rows)
    locker.slots_available = locker.slots_count
    locker.updated_at = now
    db.commit()
    db.refresh(locker)
    return locker_to_out(locker)


def bulk_create(db: Session, body: LockerBulkCreateIn) -> tuple[list[LockerOut], list[dict]]:
    created: list[LockerOut] = []
    failed: list[dict] = []
    for item in body.lockers:
        try:
            created.append(create_locker(db, item))
        except HTTPException as exc:
            failed.append({"id": item.id, "detail": exc.detail})
        except Exception as exc:  # noqa: BLE001
            failed.append({"id": item.id, "detail": str(exc)})
    return created, failed


def list_lockers(db: Session, region: Optional[str] = None, active_only: bool = False) -> list[LockerOut]:
    q = db.query(Locker)
    if region:
        q = q.filter(Locker.region == region)
    if active_only:
        q = q.filter(Locker.active.is_(True))
    rows = q.order_by(Locker.id).all()
    return [locker_to_out(row) for row in rows]


def update_locker(db: Session, locker_id: str, body: LockerUpdateIn) -> LockerOut:
    locker = get_locker_or_404(db, locker_id)
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(locker, key, value)
    locker.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(locker)
    return locker_to_out(locker)


def delete_locker(db: Session, locker_id: str) -> None:
    locker = get_locker_or_404(db, locker_id)
    db.delete(locker)
    db.commit()
