from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.finance import FinancePartnerAccount
from app.schemas.finance_catalog import (
    CapabilityListOut,
    CatalogSyncOut,
    LockerNetworkCatalogListOut,
    LockerNetworkCatalogOut,
    PlayerCapabilityOut,
    PlayerRelationOut,
    RelationListOut,
    SegmentListOut,
    EcosystemSegmentOut,
)
from app.services import finance_catalog_service as cat_svc

router = APIRouter(prefix="/locker-network-catalog", tags=["locker-network-catalog"])


def _enrich(db: Session, row) -> LockerNetworkCatalogOut:
    out = LockerNetworkCatalogOut.model_validate(row)
    if row.finance_partner_id:
        p = db.get(FinancePartnerAccount, row.finance_partner_id)
        if p:
            return out.model_copy(update={"finance_partner_code": p.code})
    return out


@router.get("", response_model=LockerNetworkCatalogListOut)
def list_locker_network_catalog(
    parent_group: str | None = Query(None),
    segment_code: str | None = Query(None),
    country_code: str | None = Query(None),
    linked_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> LockerNetworkCatalogListOut:
    rows = cat_svc.list_catalog(
        db,
        parent_group=parent_group,
        segment_code=segment_code,
        country_code=country_code,
        linked_only=linked_only,
    )
    items = [_enrich(db, r) for r in rows]
    return LockerNetworkCatalogListOut(
        items=items,
        total=len(items),
        by_parent_group=cat_svc.catalog_stats(db),
    )


@router.get("/segments", response_model=SegmentListOut)
def list_segments(db: Session = Depends(get_db)) -> SegmentListOut:
    rows = cat_svc.list_segments(db)
    items = [EcosystemSegmentOut.model_validate(r) for r in rows]
    return SegmentListOut(items=items, total=len(items))


@router.get("/relations", response_model=RelationListOut)
def list_relations(catalog_code: str | None = Query(None), db: Session = Depends(get_db)) -> RelationListOut:
    rows = cat_svc.list_relations(db, catalog_code)
    items = [PlayerRelationOut.model_validate(r) for r in rows]
    return RelationListOut(items=items, total=len(items))


@router.get("/capabilities", response_model=CapabilityListOut)
def list_capabilities(catalog_code: str | None = Query(None), db: Session = Depends(get_db)) -> CapabilityListOut:
    rows = cat_svc.list_capabilities(db, catalog_code)
    items = [PlayerCapabilityOut.model_validate(r) for r in rows]
    return CapabilityListOut(items=items, total=len(items))


@router.post("/sync", response_model=CatalogSyncOut)
def sync_locker_network_catalog(
    create_partners: bool = Query(True),
    create_plans: bool = Query(True),
    db: Session = Depends(get_db),
) -> CatalogSyncOut:
    result = cat_svc.sync_global_catalog(db, create_partners=create_partners, create_plans=create_plans)
    return CatalogSyncOut(**result)
