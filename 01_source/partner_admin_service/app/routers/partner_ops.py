from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.partner_domain import PartnerDashboardOut, PartnerStoreCreateIn, PartnerStoreListOut, PartnerStoreOut
from app.services import partner_domain_service as svc

stores_router = APIRouter(prefix="/partner-stores", tags=["partner-stores"])
ops_router = APIRouter(prefix="/partners", tags=["partner-ops"])


@ops_router.get("/ops/dashboard", response_model=PartnerDashboardOut)
def ops_dashboard(
    partner_id: str | None = Query(None),
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = Query(None),
    include_sections: str | None = Query(None),
    db: Session = Depends(get_db),
) -> PartnerDashboardOut:
    del include_sections
    return svc.get_ops_dashboard(db, partner_id=partner_id, from_dt=from_, to_dt=to)


@stores_router.get("", response_model=PartnerStoreListOut)
def list_stores(active_only: bool = Query(False), db: Session = Depends(get_db)) -> PartnerStoreListOut:
    return svc.list_stores(db, active_only=active_only)


@stores_router.post("", response_model=PartnerStoreOut)
def create_store(body: PartnerStoreCreateIn, db: Session = Depends(get_db)) -> PartnerStoreOut:
    return svc.create_store(db, body)
