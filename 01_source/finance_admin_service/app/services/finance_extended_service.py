from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.finance import FinancePartnerAccount, PartnerB2bInvoice, PartnerBillingCycle, PartnerWebhookEndpoint
from app.models.finance_extended import (
    CostCenter,
    CostCenterMonthly,
    FiscalReconciliationGap,
    PartnerBillingLineItem,
    PartnerCommissionStructure,
    PartnerCreditNote,
    PartnerPaymentHold,
    PartnerSettlementBatch,
    PartnerSettlementItem,
    PartnerWebhookDelivery,
)
from app.schemas.finance_extended import (
    CommissionIn,
    CostCenterIn,
    CostCenterMonthlyIn,
    CreditNoteIn,
    CreditNoteUpdate,
    FiscalGapIn,
    FiscalGapUpdate,
    LineItemIn,
    PaymentHoldIn,
    PaymentHoldUpdate,
    SettlementBatchIn,
    SettlementBatchUpdate,
    SettlementItemIn,
)
from app.services.crypto_util import new_id
from app.services.finance_service import get_partner_or_404


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- Line items ---


def list_line_items(db: Session, cycle_id: str | None = None, partner_id: str | None = None) -> list[PartnerBillingLineItem]:
    q = db.query(PartnerBillingLineItem)
    if cycle_id:
        q = q.filter(PartnerBillingLineItem.cycle_id == cycle_id)
    if partner_id:
        q = q.filter(PartnerBillingLineItem.partner_id == partner_id)
    return q.order_by(PartnerBillingLineItem.id.desc()).limit(500).all()


def create_line_item(db: Session, body: LineItemIn) -> PartnerBillingLineItem:
    get_partner_or_404(db, body.partner_id)
    if not db.get(PartnerBillingCycle, body.cycle_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="cycle_not_found")
    total = body.total_cents if body.total_cents is not None else int(body.quantity * body.unit_price_cents)
    row = PartnerBillingLineItem(
        cycle_id=body.cycle_id,
        partner_id=body.partner_id,
        locker_id=body.locker_id,
        line_type=body.line_type,
        description=body.description,
        quantity=body.quantity,
        unit_price_cents=body.unit_price_cents,
        total_cents=total,
        currency=body.currency,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_line_item(db: Session, item_id: int) -> None:
    row = db.get(PartnerBillingLineItem, item_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="line_item_not_found")
    db.delete(row)
    db.commit()


# --- Settlements ---


def list_settlement_batches(db: Session, partner_id: str | None = None) -> list[PartnerSettlementBatch]:
    q = db.query(PartnerSettlementBatch)
    if partner_id:
        q = q.filter(PartnerSettlementBatch.partner_id == partner_id)
    return q.order_by(PartnerSettlementBatch.period_start.desc()).all()


def create_settlement_batch(db: Session, body: SettlementBatchIn) -> PartnerSettlementBatch:
    partner = get_partner_or_404(db, body.partner_id)
    share_cents = body.revenue_share_cents or int(body.gross_revenue_cents * float(body.revenue_share_pct))
    net = body.net_amount_cents
    if net is None:
        net = body.gross_revenue_cents - share_cents - body.fees_cents
    row = PartnerSettlementBatch(
        id=new_id(),
        partner_id=body.partner_id,
        partner_type=body.partner_type or partner.partner_type,
        period_start=body.period_start,
        period_end=body.period_end,
        currency=body.currency,
        total_orders=body.total_orders,
        gross_revenue_cents=body.gross_revenue_cents,
        revenue_share_pct=body.revenue_share_pct,
        revenue_share_cents=share_cents,
        fees_cents=body.fees_cents,
        net_amount_cents=net,
        status=body.status,
        notes=body.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_settlement_batch(db: Session, batch_id: str, body: SettlementBatchUpdate) -> PartnerSettlementBatch:
    row = db.get(PartnerSettlementBatch, batch_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="settlement_batch_not_found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def list_settlement_items(db: Session, batch_id: str) -> list[PartnerSettlementItem]:
    return (
        db.query(PartnerSettlementItem)
        .filter(PartnerSettlementItem.batch_id == batch_id)
        .order_by(PartnerSettlementItem.id.desc())
        .all()
    )


def create_settlement_item(db: Session, body: SettlementItemIn) -> PartnerSettlementItem:
    if not db.get(PartnerSettlementBatch, body.batch_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="settlement_batch_not_found")
    share = body.share_cents if body.share_cents is not None else int(body.gross_cents * float(body.share_pct))
    row = PartnerSettlementItem(
        batch_id=body.batch_id,
        order_id=body.order_id,
        order_date=body.order_date,
        gross_cents=body.gross_cents,
        share_pct=body.share_pct,
        share_cents=share,
        currency=body.currency,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# --- Treasury ---


def list_credit_notes(db: Session, partner_id: str | None = None) -> list[PartnerCreditNote]:
    q = db.query(PartnerCreditNote)
    if partner_id:
        q = q.filter(PartnerCreditNote.partner_id == partner_id)
    return q.order_by(PartnerCreditNote.created_at.desc()).all()


def create_credit_note(db: Session, body: CreditNoteIn) -> PartnerCreditNote:
    get_partner_or_404(db, body.partner_id)
    row = PartnerCreditNote(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_credit_note(db: Session, note_id: str, body: CreditNoteUpdate) -> PartnerCreditNote:
    row = db.get(PartnerCreditNote, note_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="credit_note_not_found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def list_payment_holds(db: Session, partner_id: str | None = None) -> list[PartnerPaymentHold]:
    q = db.query(PartnerPaymentHold)
    if partner_id:
        q = q.filter(PartnerPaymentHold.partner_id == partner_id)
    return q.order_by(PartnerPaymentHold.created_at.desc()).all()


def create_payment_hold(db: Session, body: PaymentHoldIn) -> PartnerPaymentHold:
    get_partner_or_404(db, body.partner_id)
    row = PartnerPaymentHold(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_payment_hold(db: Session, hold_id: str, body: PaymentHoldUpdate) -> PartnerPaymentHold:
    row = db.get(PartnerPaymentHold, hold_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="payment_hold_not_found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


def list_commissions(db: Session, partner_id: str | None = None) -> list[PartnerCommissionStructure]:
    q = db.query(PartnerCommissionStructure)
    if partner_id:
        q = q.filter(PartnerCommissionStructure.partner_id == partner_id)
    return q.order_by(PartnerCommissionStructure.effective_from.desc()).all()


def create_commission(db: Session, body: CommissionIn) -> PartnerCommissionStructure:
    get_partner_or_404(db, body.partner_id)
    row = PartnerCommissionStructure(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# --- Cost centers ---


def list_cost_centers(db: Session) -> list[CostCenter]:
    return db.query(CostCenter).order_by(CostCenter.locker_id).all()


def create_cost_center(db: Session, body: CostCenterIn) -> CostCenter:
    if db.query(CostCenter).filter(CostCenter.locker_id == body.locker_id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="cost_center_exists")
    row = CostCenter(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_cost_center_monthly(db: Session, locker_id: str | None = None) -> list[CostCenterMonthly]:
    q = db.query(CostCenterMonthly)
    if locker_id:
        q = q.filter(CostCenterMonthly.locker_id == locker_id)
    return q.order_by(CostCenterMonthly.month.desc()).limit(500).all()


def create_cost_center_monthly(db: Session, body: CostCenterMonthlyIn) -> CostCenterMonthly:
    existing = (
        db.query(CostCenterMonthly)
        .filter(CostCenterMonthly.locker_id == body.locker_id, CostCenterMonthly.month == body.month)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="cost_center_month_exists")
    row = CostCenterMonthly(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# --- Fiscal gaps ---


def list_fiscal_gaps(db: Session, status_filter: str | None = None) -> list[FiscalReconciliationGap]:
    q = db.query(FiscalReconciliationGap)
    if status_filter:
        q = q.filter(FiscalReconciliationGap.status == status_filter)
    return q.order_by(FiscalReconciliationGap.last_detected_at.desc()).limit(500).all()


def create_fiscal_gap(db: Session, body: FiscalGapIn) -> FiscalReconciliationGap:
    if db.query(FiscalReconciliationGap).filter(FiscalReconciliationGap.dedupe_key == body.dedupe_key).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="gap_dedupe_exists")
    now = _utcnow()
    row = FiscalReconciliationGap(
        id=f"gap-{new_id()[:20]}",
        dedupe_key=body.dedupe_key,
        gap_type=body.gap_type,
        severity=body.severity,
        status=body.status,
        order_id=body.order_id,
        invoice_id=body.invoice_id,
        details_json=body.details_json,
        first_detected_at=now,
        last_detected_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_fiscal_gap(db: Session, gap_id: str, body: FiscalGapUpdate) -> FiscalReconciliationGap:
    row = db.get(FiscalReconciliationGap, gap_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="fiscal_gap_not_found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.last_detected_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


# --- Webhook deliveries ---


def list_webhook_deliveries(db: Session, endpoint_id: str | None = None, failed_only: bool = False) -> list[PartnerWebhookDelivery]:
    q = db.query(PartnerWebhookDelivery)
    if endpoint_id:
        q = q.filter(PartnerWebhookDelivery.endpoint_id == endpoint_id)
    if failed_only:
        q = q.filter(PartnerWebhookDelivery.status.in_(["FAILED", "PENDING", "DEAD_LETTER"]))
    return q.order_by(PartnerWebhookDelivery.created_at.desc()).limit(300).all()
