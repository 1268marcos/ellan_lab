from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finance_extended import (
    CommissionIn,
    CommissionListOut,
    CommissionOut,
    CostCenterIn,
    CostCenterListOut,
    CostCenterMonthlyIn,
    CostCenterMonthlyListOut,
    CostCenterMonthlyOut,
    CostCenterOut,
    CreditNoteIn,
    CreditNoteListOut,
    CreditNoteOut,
    CreditNoteUpdate,
    FiscalGapIn,
    FiscalGapListOut,
    FiscalGapOut,
    FiscalGapUpdate,
    LineItemIn,
    LineItemListOut,
    LineItemOut,
    PaymentHoldIn,
    PaymentHoldListOut,
    PaymentHoldOut,
    PaymentHoldUpdate,
    SettlementBatchIn,
    SettlementBatchListOut,
    SettlementBatchOut,
    SettlementBatchUpdate,
    SettlementItemIn,
    SettlementItemListOut,
    SettlementItemOut,
    WebhookDeliveryListOut,
    WebhookDeliveryOut,
)
from app.schemas.finance_professional import WebhookReplayOut
from app.services import finance_extended_service as svc
from app.services import finance_professional_service as pro_svc

router = APIRouter(tags=["finance-extended"])


@router.get("/billing-line-items", response_model=LineItemListOut)
def list_line_items(
    cycle_id: str | None = Query(None),
    partner_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> LineItemListOut:
    rows = svc.list_line_items(db, cycle_id, partner_id)
    items = [LineItemOut.model_validate(r) for r in rows]
    return LineItemListOut(items=items, total=len(items))


@router.post("/billing-line-items", response_model=LineItemOut, status_code=status.HTTP_201_CREATED)
def create_line_item(body: LineItemIn, db: Session = Depends(get_db)) -> LineItemOut:
    return LineItemOut.model_validate(svc.create_line_item(db, body))


@router.delete("/billing-line-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_line_item(item_id: int, db: Session = Depends(get_db)) -> None:
    svc.delete_line_item(db, item_id)


@router.get("/settlement-batches", response_model=SettlementBatchListOut)
def list_settlements(partner_id: str | None = Query(None), db: Session = Depends(get_db)) -> SettlementBatchListOut:
    rows = svc.list_settlement_batches(db, partner_id)
    items = [SettlementBatchOut.model_validate(r) for r in rows]
    return SettlementBatchListOut(items=items, total=len(items))


@router.post("/settlement-batches", response_model=SettlementBatchOut, status_code=status.HTTP_201_CREATED)
def create_settlement(body: SettlementBatchIn, db: Session = Depends(get_db)) -> SettlementBatchOut:
    return SettlementBatchOut.model_validate(svc.create_settlement_batch(db, body))


@router.patch("/settlement-batches/{batch_id}", response_model=SettlementBatchOut)
def update_settlement(batch_id: str, body: SettlementBatchUpdate, db: Session = Depends(get_db)) -> SettlementBatchOut:
    return SettlementBatchOut.model_validate(svc.update_settlement_batch(db, batch_id, body))


@router.get("/settlement-batches/{batch_id}/items", response_model=SettlementItemListOut)
def list_settlement_items(batch_id: str, db: Session = Depends(get_db)) -> SettlementItemListOut:
    rows = svc.list_settlement_items(db, batch_id)
    items = [SettlementItemOut.model_validate(r) for r in rows]
    return SettlementItemListOut(items=items, total=len(items))


@router.post("/settlement-items", response_model=SettlementItemOut, status_code=status.HTTP_201_CREATED)
def create_settlement_item(body: SettlementItemIn, db: Session = Depends(get_db)) -> SettlementItemOut:
    return SettlementItemOut.model_validate(svc.create_settlement_item(db, body))


@router.get("/credit-notes", response_model=CreditNoteListOut)
def list_credit_notes(partner_id: str | None = Query(None), db: Session = Depends(get_db)) -> CreditNoteListOut:
    rows = svc.list_credit_notes(db, partner_id)
    items = [CreditNoteOut.model_validate(r) for r in rows]
    return CreditNoteListOut(items=items, total=len(items))


@router.post("/credit-notes", response_model=CreditNoteOut, status_code=status.HTTP_201_CREATED)
def create_credit_note(body: CreditNoteIn, db: Session = Depends(get_db)) -> CreditNoteOut:
    return CreditNoteOut.model_validate(svc.create_credit_note(db, body))


@router.patch("/credit-notes/{note_id}", response_model=CreditNoteOut)
def update_credit_note(note_id: str, body: CreditNoteUpdate, db: Session = Depends(get_db)) -> CreditNoteOut:
    return CreditNoteOut.model_validate(svc.update_credit_note(db, note_id, body))


@router.get("/payment-holds", response_model=PaymentHoldListOut)
def list_holds(partner_id: str | None = Query(None), db: Session = Depends(get_db)) -> PaymentHoldListOut:
    rows = svc.list_payment_holds(db, partner_id)
    items = [PaymentHoldOut.model_validate(r) for r in rows]
    return PaymentHoldListOut(items=items, total=len(items))


@router.post("/payment-holds", response_model=PaymentHoldOut, status_code=status.HTTP_201_CREATED)
def create_hold(body: PaymentHoldIn, db: Session = Depends(get_db)) -> PaymentHoldOut:
    return PaymentHoldOut.model_validate(svc.create_payment_hold(db, body))


@router.patch("/payment-holds/{hold_id}", response_model=PaymentHoldOut)
def update_hold(hold_id: str, body: PaymentHoldUpdate, db: Session = Depends(get_db)) -> PaymentHoldOut:
    return PaymentHoldOut.model_validate(svc.update_payment_hold(db, hold_id, body))


@router.get("/commission-structures", response_model=CommissionListOut)
def list_commissions(partner_id: str | None = Query(None), db: Session = Depends(get_db)) -> CommissionListOut:
    rows = svc.list_commissions(db, partner_id)
    items = [CommissionOut.model_validate(r) for r in rows]
    return CommissionListOut(items=items, total=len(items))


@router.post("/commission-structures", response_model=CommissionOut, status_code=status.HTTP_201_CREATED)
def create_commission(body: CommissionIn, db: Session = Depends(get_db)) -> CommissionOut:
    return CommissionOut.model_validate(svc.create_commission(db, body))


@router.get("/cost-centers", response_model=CostCenterListOut)
def list_cost_centers(db: Session = Depends(get_db)) -> CostCenterListOut:
    rows = svc.list_cost_centers(db)
    items = [CostCenterOut.model_validate(r) for r in rows]
    return CostCenterListOut(items=items, total=len(items))


@router.post("/cost-centers", response_model=CostCenterOut, status_code=status.HTTP_201_CREATED)
def create_cost_center(body: CostCenterIn, db: Session = Depends(get_db)) -> CostCenterOut:
    return CostCenterOut.model_validate(svc.create_cost_center(db, body))


@router.get("/cost-center-monthly", response_model=CostCenterMonthlyListOut)
def list_ccm(locker_id: str | None = Query(None), db: Session = Depends(get_db)) -> CostCenterMonthlyListOut:
    rows = svc.list_cost_center_monthly(db, locker_id)
    items = [CostCenterMonthlyOut.model_validate(r) for r in rows]
    return CostCenterMonthlyListOut(items=items, total=len(items))


@router.post("/cost-center-monthly", response_model=CostCenterMonthlyOut, status_code=status.HTTP_201_CREATED)
def create_ccm(body: CostCenterMonthlyIn, db: Session = Depends(get_db)) -> CostCenterMonthlyOut:
    return CostCenterMonthlyOut.model_validate(svc.create_cost_center_monthly(db, body))


@router.get("/fiscal-reconciliation-gaps", response_model=FiscalGapListOut)
def list_gaps(status_filter: str | None = Query(None, alias="status"), db: Session = Depends(get_db)) -> FiscalGapListOut:
    rows = svc.list_fiscal_gaps(db, status_filter)
    items = [FiscalGapOut.model_validate(r) for r in rows]
    return FiscalGapListOut(items=items, total=len(items))


@router.post("/fiscal-reconciliation-gaps", response_model=FiscalGapOut, status_code=status.HTTP_201_CREATED)
def create_gap(body: FiscalGapIn, db: Session = Depends(get_db)) -> FiscalGapOut:
    return FiscalGapOut.model_validate(svc.create_fiscal_gap(db, body))


@router.patch("/fiscal-reconciliation-gaps/{gap_id}", response_model=FiscalGapOut)
def update_gap(gap_id: str, body: FiscalGapUpdate, db: Session = Depends(get_db)) -> FiscalGapOut:
    return FiscalGapOut.model_validate(svc.update_fiscal_gap(db, gap_id, body))


@router.get("/webhook-deliveries", response_model=WebhookDeliveryListOut)
def list_deliveries(
    endpoint_id: str | None = Query(None),
    failed_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> WebhookDeliveryListOut:
    rows = svc.list_webhook_deliveries(db, endpoint_id, failed_only)
    items = [WebhookDeliveryOut.model_validate(r) for r in rows]
    return WebhookDeliveryListOut(items=items, total=len(items))


@router.post("/webhook-deliveries/{delivery_id}/replay", response_model=WebhookReplayOut)
def replay_webhook_delivery(delivery_id: str, db: Session = Depends(get_db)) -> WebhookReplayOut:
    row = pro_svc.replay_webhook_delivery(db, delivery_id)
    return WebhookReplayOut(
        delivery_id=row.id,
        status=row.status,
        attempt_count=row.attempt_count,
        http_status=row.http_status,
    )
