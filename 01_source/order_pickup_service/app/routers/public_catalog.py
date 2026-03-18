from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/public/catalog", tags=["public-catalog"])


@router.get("")
def public_catalog_stub():
    return {
        "items": [],
        "message": "public_catalog_not_implemented_yet",
    }