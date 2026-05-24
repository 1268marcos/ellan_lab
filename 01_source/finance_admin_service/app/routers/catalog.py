from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.finance import FinancePartnerAccount
from app.schemas.finance_catalog import (
    CapabilityListOut,
    CatalogSyncOut,
    CountryCoverageOut,
    IntegrationBlueprintOut,
    IntegrationGuideOut,
    LockerNetworkCatalogListOut,
    LockerNetworkCatalogOut,
    PlayerAliasOut,
    PlayerCapabilityOut,
    PlayerRelationOut,
    RelationListOut,
    SegmentListOut,
    EcosystemSegmentOut,
)
from app.data.global_locker_finance_catalog import LOCKER_WORLD_PRIORITY_INDEX
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


@router.get("/aliases")
def list_aliases(
    catalog_code: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    rows = cat_svc.list_aliases(db, catalog_code)
    return {"items": [PlayerAliasOut.model_validate(r) for r in rows], "total": len(rows)}


@router.get("/resolve/{code_or_alias}")
def resolve_player_code(code_or_alias: str, db: Session = Depends(get_db)) -> dict:
    resolved = cat_svc.resolve_catalog_code(db, code_or_alias.upper())
    return {"input": code_or_alias, "catalog_code": resolved}


@router.get("/country-coverage")
def list_country_coverage(
    catalog_code: str | None = Query(None),
    country_code: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    rows = cat_svc.list_country_coverage(db, catalog_code=catalog_code, country_code=country_code)
    items = [CountryCoverageOut.model_validate(r) for r in rows]
    return {"items": items, "total": len(items)}


@router.get("/integration-blueprints")
def list_integration_blueprints(db: Session = Depends(get_db)) -> dict:
    rows = cat_svc.list_integration_blueprints(db)
    items = [IntegrationBlueprintOut.model_validate(r) for r in rows]
    return {"items": items, "total": len(items)}


@router.get("/ecosystem-matrix")
def ecosystem_matrix(db: Session = Depends(get_db)) -> dict:
    return cat_svc.ecosystem_matrix(db)


@router.get("/players/{catalog_code}/integration-guide", response_model=IntegrationGuideOut)
def player_integration_guide(catalog_code: str, db: Session = Depends(get_db)) -> IntegrationGuideOut:
    guide = cat_svc.build_integration_guide(db, catalog_code)
    if not guide:
        raise HTTPException(status_code=404, detail="catalog_player_not_found")
    guide = cat_svc.enrich_guide_finance_partner(db, guide)
    return IntegrationGuideOut.model_validate(guide)


@router.get("/world-priority-index")
def world_priority_index() -> dict:
    """Players locker mundiais prioritários (InPost, DHL, Magalu, ML, Amazon, DPD, Correios, CTT, Worten, ECI…)."""
    return {"items": LOCKER_WORLD_PRIORITY_INDEX, "total": len(LOCKER_WORLD_PRIORITY_INDEX)}


@router.post("/sync", response_model=CatalogSyncOut)
def sync_locker_network_catalog(
    create_partners: bool = Query(True),
    create_plans: bool = Query(True),
    db: Session = Depends(get_db),
) -> CatalogSyncOut:
    result = cat_svc.sync_global_catalog(db, create_partners=create_partners, create_plans=create_plans)
    return CatalogSyncOut(**result)
