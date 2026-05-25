from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import (
    ManifestCreateIn,
    ManifestItemCreateIn,
    ManifestItemListOut,
    ManifestItemOut,
    ManifestListOut,
    ManifestOut,
    ManifestUpdateIn,
)
from app.services import orders_domain_service

router = APIRouter(prefix="/logistics-manifests", tags=["logistics-manifests"])


@router.get("", response_model=ManifestListOut)
def list_manifests(
    status: str | None = Query(default=None),
    partner_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ManifestListOut:
    items, total = orders_domain_service.list_manifests(
        db, status=status, partner_id=partner_id, limit=limit, offset=offset
    )
    return ManifestListOut(items=items, total=total)


@router.post("", response_model=ManifestOut, status_code=status.HTTP_201_CREATED)
def create_manifest(body: ManifestCreateIn, db: Session = Depends(get_db)) -> ManifestOut:
    return orders_domain_service.create_manifest(db, body)


@router.patch("/{manifest_id}", response_model=ManifestOut)
def update_manifest(manifest_id: str, body: ManifestUpdateIn, db: Session = Depends(get_db)) -> ManifestOut:
    return orders_domain_service.update_manifest(db, manifest_id, body)


@router.get("/items", response_model=ManifestItemListOut)
def list_manifest_items(
    manifest_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ManifestItemListOut:
    items, total = orders_domain_service.list_manifest_items(db, manifest_id=manifest_id, limit=limit, offset=offset)
    return ManifestItemListOut(items=items, total=total)


@router.post("/items", response_model=ManifestItemOut, status_code=status.HTTP_201_CREATED)
def add_manifest_item(body: ManifestItemCreateIn, db: Session = Depends(get_db)) -> ManifestItemOut:
    return orders_domain_service.add_manifest_item(db, body)
