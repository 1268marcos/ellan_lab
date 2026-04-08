# 01_source/backend/runtime/app/routers/catalog.py
# 08/04/2026

from __future__ import annotations

from fastapi import APIRouter, Header, Request
from typing import List

from app.services.slot_projection_service import project_slots
from app.schemas.catalog import CatalogSkuOut, CatalogSlotOut
from app.services.catalog_service import (
    list_catalog_skus,
    get_catalog_sku,
    list_catalog_slots,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/slots-projected")
def list_slots_projected(
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
):
    return project_slots(
        x_locker_id=x_locker_id,
    )


@router.get("/skus", response_model=List[CatalogSkuOut])
def list_skus(
    request: Request,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
):
    return list_catalog_skus(x_locker_id=x_locker_id)


@router.get("/skus/{sku_id}", response_model=CatalogSkuOut)
def get_sku(
    sku_id: str,
    request: Request,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
):
    return get_catalog_sku(
        x_locker_id=x_locker_id,
        sku_id=sku_id,
    )


@router.get("/slots", response_model=List[CatalogSlotOut])
def list_slots(
    request: Request,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
):
    return list_catalog_slots(x_locker_id=x_locker_id)

