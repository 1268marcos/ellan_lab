from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.fiscal_global import FiscalAutoClassificationLog
from app.schemas.fiscal import (
    ApprovalIn,
    ApprovalListOut,
    ApprovalOut,
    CallbackListOut,
    CallbackOut,
    GapIn,
    GapListOut,
    GapOut,
    GapUpdate,
    GapWorkbenchOut,
    UnifiedGapOut,
    ProductFiscalIn,
    ProductFiscalListOut,
    ProductFiscalOut,
    ProviderHealthIn,
    ProviderHealthListOut,
    ProviderHealthOut,
    TenantFiscalIn,
    TenantFiscalListOut,
    TenantFiscalOut,
)
from app.services import billing_fiscal_client, fiscal_core_service, fiscal_gap_workbench_service

router = APIRouter(prefix="/fiscal-ops", tags=["fiscal-ops"])


@router.get("/reconciliation-gaps", response_model=GapListOut)
def list_gaps(status: str | None = Query(None), limit: int = Query(100, le=500), db: Session = Depends(get_db)):
    items = fiscal_core_service.list_gaps(db, status=status, limit=limit)
    return GapListOut(items=[GapOut.model_validate(i) for i in items], total=len(items))


@router.post("/reconciliation-gaps", response_model=GapOut, status_code=status.HTTP_201_CREATED)
def create_gap(body: GapIn, db: Session = Depends(get_db)):
    return GapOut.model_validate(fiscal_core_service.create_gap(db, body))


@router.patch("/reconciliation-gaps/{gap_id}", response_model=GapOut)
def patch_gap(gap_id: str, body: GapUpdate, db: Session = Depends(get_db)):
    return GapOut.model_validate(fiscal_core_service.patch_gap(db, gap_id, body))


@router.get("/reconciliation-gaps/workbench", response_model=GapWorkbenchOut)
def list_gaps_workbench(
    status: str | None = Query("OPEN"),
    date: str | None = Query(None, description="YYYY-MM-DD filter for billing gaps"),
    refresh_billing: bool = Query(False, description="Run billing scan before listing"),
    include_snapshot: bool = Query(False, description="Include billing conciliation snapshot"),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
):
    payload = fiscal_gap_workbench_service.list_gaps_workbench(
        db,
        status=status,
        date=date,
        refresh_billing=refresh_billing,
        include_snapshot=include_snapshot,
        limit=limit,
    )
    return GapWorkbenchOut(
        items=[UnifiedGapOut.model_validate(i) for i in payload["items"]],
        total=payload["total"],
        summary=payload["summary"],
        billing_available=payload["billing_available"],
        billing_error=payload["billing_error"],
        billing_scan=payload.get("billing_scan"),
        snapshot=payload.get("snapshot"),
    )


@router.patch("/reconciliation-gaps/workbench/{gap_id}", response_model=UnifiedGapOut)
def patch_gap_workbench(
    gap_id: str,
    body: GapUpdate,
    source: str = Query(..., pattern="^(admin|billing)$"),
    db: Session = Depends(get_db),
):
    try:
        item = fiscal_gap_workbench_service.resolve_gap_workbench(db, gap_id=gap_id, source=source, body=body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except billing_fiscal_client.BillingFiscalClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return UnifiedGapOut.model_validate(item)


@router.get("/provider-health", response_model=ProviderHealthListOut)
def list_health(db: Session = Depends(get_db)):
    items = fiscal_core_service.list_provider_health(db)
    return ProviderHealthListOut(items=[ProviderHealthOut.model_validate(i) for i in items], total=len(items))


@router.put("/provider-health", response_model=ProviderHealthOut)
def upsert_health(body: ProviderHealthIn, db: Session = Depends(get_db)):
    return ProviderHealthOut.model_validate(fiscal_core_service.upsert_provider_health(db, body))


@router.get("/tenant-config", response_model=TenantFiscalListOut)
def list_tenants(limit: int = Query(100, le=500), db: Session = Depends(get_db)):
    items = fiscal_core_service.list_tenants(db, limit=limit)
    return TenantFiscalListOut(items=[TenantFiscalOut.model_validate(i) for i in items], total=len(items))


@router.put("/tenant-config", response_model=TenantFiscalOut)
def upsert_tenant(body: TenantFiscalIn, db: Session = Depends(get_db)):
    return TenantFiscalOut.model_validate(fiscal_core_service.upsert_tenant(db, body))


@router.get("/product-fiscal-config", response_model=ProductFiscalListOut)
def list_products(limit: int = Query(100, le=500), db: Session = Depends(get_db)):
    items = fiscal_core_service.list_products(db, limit=limit)
    return ProductFiscalListOut(items=[ProductFiscalOut.model_validate(i) for i in items], total=len(items))


@router.put("/product-fiscal-config", response_model=ProductFiscalOut)
def upsert_product(body: ProductFiscalIn, db: Session = Depends(get_db)):
    return ProductFiscalOut.model_validate(fiscal_core_service.upsert_product(db, body))


@router.get("/accounting-approvals", response_model=ApprovalListOut)
def list_approvals(limit: int = Query(100, le=500), db: Session = Depends(get_db)):
    items = fiscal_core_service.list_approvals(db, limit=limit)
    return ApprovalListOut(items=[ApprovalOut.model_validate(i) for i in items], total=len(items))


@router.post("/accounting-approvals", response_model=ApprovalOut, status_code=status.HTTP_201_CREATED)
def create_approval(body: ApprovalIn, db: Session = Depends(get_db)):
    return ApprovalOut.model_validate(fiscal_core_service.create_approval(db, body))


@router.get("/authority-callbacks", response_model=CallbackListOut)
def list_callbacks(limit: int = Query(100, le=500), db: Session = Depends(get_db)):
    items = fiscal_core_service.list_callbacks(db, limit=limit)
    return CallbackListOut(items=[CallbackOut.model_validate(i) for i in items], total=len(items))


class ClassificationLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: str
    sku_id: str
    ncm_applied: str | None
    cfop_applied: str | None
    source: str
    classified_at: datetime


class ClassificationLogListOut(BaseModel):
    items: list[ClassificationLogOut]
    total: int


@router.get("/classification-logs", response_model=ClassificationLogListOut)
def list_classification_logs(
    order_id: str | None = Query(None), limit: int = Query(100, le=500), db: Session = Depends(get_db)
):
    q = db.query(FiscalAutoClassificationLog)
    if order_id:
        q = q.filter(FiscalAutoClassificationLog.order_id == order_id)
    items = q.order_by(FiscalAutoClassificationLog.classified_at.desc()).limit(limit).all()
    out = [ClassificationLogOut.model_validate(i) for i in items]
    return ClassificationLogListOut(items=out, total=len(out))
