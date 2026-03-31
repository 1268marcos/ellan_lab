# 01_source/backend/runtime/app/routers/catalog.py

from __future__ import annotations

"""
Objetivo

Transformar em camada transitória:

manter catálogo mock se precisar
mas parar de assumir 24 slots fixos
slot plan deve ser coerente com a topologia do locker
idealmente, depois, migrar SKU e disponibilidade para fonte central/configurável

No início pode continuar mockado, mas:

não deve assumir 24 slots fixos
deve respeitar topologia por locker
depois pode evoluir para catálogo real por locker
"""


from fastapi import APIRouter, Header, Request
from typing import List

from app.schemas.catalog import CatalogSkuOut, CatalogSlotOut
from app.services.catalog_service import (
    list_catalog_skus,
    get_catalog_sku,
    list_catalog_slots,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])


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