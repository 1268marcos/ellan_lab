from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finance import (
    B2bInvoiceIn,
    B2bInvoiceListOut,
    B2bInvoiceOut,
    B2bInvoiceUpdate,
    BillingCycleIn,
    BillingCycleListOut,
    BillingCycleOut,
    BillingCycleUpdate,
    BillingPlanIn,
    BillingPlanListOut,
    BillingPlanOut,
    BillingPlanUpdate,
)
from app.schemas.finance_professional import CycleCloseOut
from app.schemas.finance_revenue import FiscalEmitOut
from app.services import finance_service
from app.services import finance_professional_service as pro_svc
from app.services.finance_fiscal_emit_service import emit_b2b_invoice_fiscal
from app.services import finance_revenue_service as rev_svc

router = APIRouter(tags=["billing"])


@router.get("/billing-plans", response_model=BillingPlanListOut)
def list_plans(partner_id: str | None = Query(None), db: Session = Depends(get_db)) -> BillingPlanListOut:
    rows = finance_service.list_plans(db, partner_id)
    items = [BillingPlanOut.model_validate(r) for r in rows]
    return BillingPlanListOut(items=items, total=len(items))


@router.post("/billing-plans", response_model=BillingPlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(body: BillingPlanIn, db: Session = Depends(get_db)) -> BillingPlanOut:
    return BillingPlanOut.model_validate(finance_service.create_plan(db, body))


@router.patch("/billing-plans/{plan_id}", response_model=BillingPlanOut)
def update_plan(plan_id: str, body: BillingPlanUpdate, db: Session = Depends(get_db)) -> BillingPlanOut:
    return BillingPlanOut.model_validate(finance_service.update_plan(db, plan_id, body))


@router.delete("/billing-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan_id: str, db: Session = Depends(get_db)) -> None:
    finance_service.delete_plan(db, plan_id)


@router.get("/billing-cycles", response_model=BillingCycleListOut)
def list_cycles(partner_id: str | None = Query(None), db: Session = Depends(get_db)) -> BillingCycleListOut:
    rows = finance_service.list_cycles(db, partner_id)
    items = [BillingCycleOut.model_validate(r) for r in rows]
    return BillingCycleListOut(items=items, total=len(items))


@router.post("/billing-cycles", response_model=BillingCycleOut, status_code=status.HTTP_201_CREATED)
def create_cycle(body: BillingCycleIn, db: Session = Depends(get_db)) -> BillingCycleOut:
    return BillingCycleOut.model_validate(finance_service.create_cycle(db, body))


@router.patch("/billing-cycles/{cycle_id}", response_model=BillingCycleOut)
def update_cycle(cycle_id: str, body: BillingCycleUpdate, db: Session = Depends(get_db)) -> BillingCycleOut:
    return BillingCycleOut.model_validate(finance_service.update_cycle(db, cycle_id, body))


@router.delete("/billing-cycles/{cycle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cycle(cycle_id: str, db: Session = Depends(get_db)) -> None:
    finance_service.delete_cycle(db, cycle_id)


@router.post("/billing-cycles/{cycle_id}/close", response_model=CycleCloseOut)
def close_cycle(
    cycle_id: str,
    create_revenue_schedule: bool = Query(True),
    emit_fiscal: bool = Query(False),
    db: Session = Depends(get_db),
) -> CycleCloseOut:
    result = pro_svc.close_billing_cycle(db, cycle_id)
    if create_revenue_schedule:
        rev_svc.create_schedule_from_cycle(db, cycle_id)
    if emit_fiscal and result.get("invoice_id"):
        emit_b2b_invoice_fiscal(db, result["invoice_id"])
    return CycleCloseOut(**result)


@router.post("/b2b-invoices/{invoice_id}/emit-fiscal", response_model=FiscalEmitOut)
def emit_fiscal_for_invoice(invoice_id: str, db: Session = Depends(get_db)) -> FiscalEmitOut:
    return FiscalEmitOut(**emit_b2b_invoice_fiscal(db, invoice_id))


@router.get("/b2b-invoices", response_model=B2bInvoiceListOut)
def list_b2b(partner_id: str | None = Query(None), db: Session = Depends(get_db)) -> B2bInvoiceListOut:
    rows = finance_service.list_b2b_invoices(db, partner_id)
    items = [B2bInvoiceOut.model_validate(r) for r in rows]
    return B2bInvoiceListOut(items=items, total=len(items))


@router.post("/b2b-invoices", response_model=B2bInvoiceOut, status_code=status.HTTP_201_CREATED)
def create_b2b(body: B2bInvoiceIn, db: Session = Depends(get_db)) -> B2bInvoiceOut:
    return B2bInvoiceOut.model_validate(finance_service.create_b2b_invoice(db, body))


@router.patch("/b2b-invoices/{invoice_id}", response_model=B2bInvoiceOut)
def update_b2b(invoice_id: str, body: B2bInvoiceUpdate, db: Session = Depends(get_db)) -> B2bInvoiceOut:
    return B2bInvoiceOut.model_validate(finance_service.update_b2b_invoice(db, invoice_id, body))


@router.delete("/b2b-invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_b2b(invoice_id: str, db: Session = Depends(get_db)) -> None:
    finance_service.delete_b2b_invoice(db, invoice_id)
