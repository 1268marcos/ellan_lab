from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finance import (
    BillingEventListOut,
    BillingEventOut,
    OpsInvoiceIn,
    OpsInvoiceListOut,
    OpsInvoiceOut,
    OpsInvoiceUpdate,
    WalletProviderIn,
    WalletProviderListOut,
    WalletProviderOut,
    WalletTransactionIn,
    WalletTransactionListOut,
    WalletTransactionOut,
)
from app.services import finance_service

router = APIRouter(tags=["wallet-ops"])


@router.get("/wallet-providers", response_model=WalletProviderListOut)
def list_providers(db: Session = Depends(get_db)) -> WalletProviderListOut:
    rows = finance_service.list_wallet_providers(db)
    items = [WalletProviderOut.model_validate(r) for r in rows]
    return WalletProviderListOut(items=items, total=len(items))


@router.post("/wallet-providers", response_model=WalletProviderOut, status_code=status.HTTP_201_CREATED)
def create_provider(body: WalletProviderIn, db: Session = Depends(get_db)) -> WalletProviderOut:
    return WalletProviderOut.model_validate(finance_service.create_wallet_provider(db, body))


@router.get("/wallet-transactions", response_model=WalletTransactionListOut)
def list_transactions(
    wallet_id: str | None = Query(None), db: Session = Depends(get_db)
) -> WalletTransactionListOut:
    rows = finance_service.list_wallet_transactions(db, wallet_id)
    items = [WalletTransactionOut.model_validate(r) for r in rows]
    return WalletTransactionListOut(items=items, total=len(items))


@router.post("/wallet-transactions", response_model=WalletTransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(body: WalletTransactionIn, db: Session = Depends(get_db)) -> WalletTransactionOut:
    return WalletTransactionOut.model_validate(finance_service.create_wallet_transaction(db, body))


@router.get("/ops-invoices", response_model=OpsInvoiceListOut)
def list_ops_invoices(order_id: str | None = Query(None), db: Session = Depends(get_db)) -> OpsInvoiceListOut:
    rows = finance_service.list_ops_invoices(db, order_id)
    items = [OpsInvoiceOut.model_validate(r) for r in rows]
    return OpsInvoiceListOut(items=items, total=len(items))


@router.post("/ops-invoices", response_model=OpsInvoiceOut, status_code=status.HTTP_201_CREATED)
def create_ops_invoice(body: OpsInvoiceIn, db: Session = Depends(get_db)) -> OpsInvoiceOut:
    return OpsInvoiceOut.model_validate(finance_service.create_ops_invoice(db, body))


@router.patch("/ops-invoices/{invoice_id}", response_model=OpsInvoiceOut)
def update_ops_invoice(
    invoice_id: str, body: OpsInvoiceUpdate, db: Session = Depends(get_db)
) -> OpsInvoiceOut:
    return OpsInvoiceOut.model_validate(finance_service.update_ops_invoice(db, invoice_id, body))


@router.get("/billing-processed-events", response_model=BillingEventListOut)
def list_events(db: Session = Depends(get_db)) -> BillingEventListOut:
    rows = finance_service.list_billing_events(db)
    items = [BillingEventOut.model_validate(r) for r in rows]
    return BillingEventListOut(items=items, total=len(items))
