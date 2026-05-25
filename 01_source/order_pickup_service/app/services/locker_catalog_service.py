from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.locker import Locker


def get_locker_or_404(db: Session, locker_id: str) -> Locker:
    locker = (
        db.query(Locker)
        .options(
            joinedload(Locker.slot_configs),
            joinedload(Locker.product_configs),
        )
        .filter(Locker.id == locker_id)
        .first()
    )
    if not locker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "LOCKER_NOT_FOUND",
                "message": f"Locker {locker_id} não encontrado",
                "locker_id": locker_id,
            },
        )
    return locker


def get_available_lockers_by_region(
    db: Session,
    *,
    region: str,
    active_only: bool = True,
    product_category: Optional[str] = None,
) -> List[Locker]:
    query = (
        db.query(Locker)
        .options(
            joinedload(Locker.slot_configs),
            joinedload(Locker.product_configs),
        )
        .filter(Locker.region == region)
    )
    if active_only:
        query = query.filter(Locker.active.is_(True))
    lockers = query.all()
    if not product_category:
        return lockers
    return [locker for locker in lockers if locker.supports_product(product_category)[0]]


def get_compatible_lockers_for_product(
    db: Session,
    *,
    region: str,
    product_category: str,
    product_value: Optional[float] = None,
    product_weight_kg: Optional[float] = None,
) -> List[Locker]:
    lockers = get_available_lockers_by_region(
        db,
        region=region,
        active_only=True,
        product_category=product_category,
    )
    if product_value is None and product_weight_kg is None:
        return lockers

    filtered: List[Locker] = []
    for locker in lockers:
        configs = [
            cfg
            for cfg in locker.product_configs
            if cfg.category == product_category and cfg.allowed
        ]
        if not configs:
            continue
        cfg = configs[0]
        if product_weight_kg is not None and cfg.max_weight_g is not None:
            if int(round(product_weight_kg * 1000)) > cfg.max_weight_g:
                continue
        if product_value is not None and cfg.min_value is not None:
            if int(product_value) < cfg.min_value:
                continue
        filtered.append(locker)
    return filtered
