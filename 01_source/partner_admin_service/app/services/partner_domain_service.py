from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.partner import EcommercePartner, LogisticsPartner
from app.models.partner_domain import (
    PartnerBillingCycle,
    PartnerBillingPlan,
    PartnerPerformanceMetric,
    PartnerServiceArea,
    PartnerSettlementBatch,
    PartnerSettlementItem,
    PartnerSlaAgreement,
    PartnerStatusHistory,
    PartnerStore,
)
from app.schemas.partner_domain import (
    BillingCycleListOut,
    BillingCycleOut,
    BillingPlanListOut,
    BillingPlanOut,
    PartnerDashboardOut,
    PartnerStoreCreateIn,
    PartnerStoreListOut,
    PartnerStoreOut,
    PerformanceListOut,
    PerformanceMetricOut,
    ServiceAreaCreateIn,
    ServiceAreaListOut,
    ServiceAreaOut,
    SettlementApproveIn,
    SettlementBatchListOut,
    SettlementBatchOut,
    SettlementGenerateIn,
    SettlementItemListOut,
    SettlementItemOut,
    SlaAgreementCreateIn,
    SlaAgreementListOut,
    SlaAgreementOut,
    StatusHistoryListOut,
    StatusHistoryOut,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_partner(db: Session, partner_id: str) -> tuple[str, str]:
    if db.get(EcommercePartner, partner_id):
        return partner_id, "ECOMMERCE"
    if db.get(LogisticsPartner, partner_id):
        return partner_id, "LOGISTICS"
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="partner_not_found")


def list_settlements(
    db: Session,
    partner_id: str,
    *,
    status_filter: str | None = None,
    from_period_start: date | None = None,
    to_period_end: date | None = None,
    limit: int = 100,
) -> SettlementBatchListOut:
    _resolve_partner(db, partner_id)
    q = db.query(PartnerSettlementBatch).filter(PartnerSettlementBatch.partner_id == partner_id)
    if status_filter:
        q = q.filter(PartnerSettlementBatch.status == status_filter.upper())
    if from_period_start:
        q = q.filter(PartnerSettlementBatch.period_start >= from_period_start)
    if to_period_end:
        q = q.filter(PartnerSettlementBatch.period_end <= to_period_end)
    rows = q.order_by(PartnerSettlementBatch.period_start.desc()).limit(limit).all()
    items = [SettlementBatchOut.model_validate(r) for r in rows]
    return SettlementBatchListOut(partner_id=partner_id, items=items, total=len(items))


def generate_settlement(db: Session, partner_id: str, body: SettlementGenerateIn) -> SettlementBatchOut:
    pid, default_pt = _resolve_partner(db, partner_id)
    pt = body.partner_type.upper() if body.partner_type else default_pt
    share_pct = Decimal(str(body.revenue_share_pct))
    gross = body.gross_revenue_cents
    share_cents = int(gross * float(share_pct))
    net = share_cents - body.fees_cents
    now = _utcnow()
    batch_id = new_id()
    row = PartnerSettlementBatch(
        id=batch_id,
        partner_id=pid,
        partner_type=pt,
        period_start=body.period_start,
        period_end=body.period_end,
        currency=body.currency,
        total_orders=body.total_orders,
        gross_revenue_cents=gross,
        revenue_share_pct=share_pct,
        revenue_share_cents=share_cents,
        fees_cents=body.fees_cents,
        net_amount_cents=net,
        status="DRAFT",
        notes=body.notes,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    if body.total_orders > 0 and gross > 0:
        per_order_gross = gross // max(body.total_orders, 1)
        per_share = share_cents // max(body.total_orders, 1)
        for i in range(min(body.total_orders, 5)):
            db.add(
                PartnerSettlementItem(
                    batch_id=batch_id,
                    order_id=f"ord-{batch_id[:8]}-{i + 1}",
                    order_date=now,
                    gross_cents=per_order_gross,
                    share_pct=share_pct,
                    share_cents=per_share,
                    currency=body.currency,
                )
            )
    db.commit()
    db.refresh(row)
    return SettlementBatchOut.model_validate(row)


def approve_settlement(
    db: Session, partner_id: str, batch_id: str, body: SettlementApproveIn
) -> SettlementBatchOut:
    _resolve_partner(db, partner_id)
    row = db.get(PartnerSettlementBatch, batch_id)
    if not row or row.partner_id != partner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="settlement_batch_not_found")
    if row.status not in ("DRAFT", "DISPUTED"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="invalid_status_transition")
    row.status = "APPROVED"
    row.settlement_ref = body.settlement_ref or row.settlement_ref
    if body.notes:
        row.notes = body.notes
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return SettlementBatchOut.model_validate(row)


def pay_settlement(db: Session, partner_id: str, batch_id: str) -> SettlementBatchOut:
    _resolve_partner(db, partner_id)
    row = db.get(PartnerSettlementBatch, batch_id)
    if not row or row.partner_id != partner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="settlement_batch_not_found")
    if row.status != "APPROVED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="batch_must_be_approved")
    now = _utcnow()
    row.status = "PAID"
    row.settled_at = now
    row.updated_at = now
    db.commit()
    db.refresh(row)
    return SettlementBatchOut.model_validate(row)


def list_settlement_items(
    db: Session, partner_id: str, batch_id: str, *, limit: int = 500, offset: int = 0
) -> SettlementItemListOut:
    _resolve_partner(db, partner_id)
    batch = db.get(PartnerSettlementBatch, batch_id)
    if not batch or batch.partner_id != partner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="settlement_batch_not_found")
    rows = (
        db.query(PartnerSettlementItem)
        .filter(PartnerSettlementItem.batch_id == batch_id)
        .order_by(PartnerSettlementItem.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    items = [SettlementItemOut.model_validate(r) for r in rows]
    return SettlementItemListOut(batch_id=batch_id, partner_id=partner_id, items=items, total=len(items))


def list_performance(db: Session, partner_id: str, *, limit: int = 6) -> PerformanceListOut:
    _resolve_partner(db, partner_id)
    rows = (
        db.query(PartnerPerformanceMetric)
        .filter(PartnerPerformanceMetric.partner_id == partner_id)
        .order_by(PartnerPerformanceMetric.period_month.desc())
        .limit(limit)
        .all()
    )
    items = [PerformanceMetricOut.model_validate(r) for r in rows]
    return PerformanceListOut(partner_id=partner_id, items=items, total=len(items))


def list_service_areas(
    db: Session, partner_id: str, *, only_active: bool = True, limit: int = 200
) -> ServiceAreaListOut:
    _resolve_partner(db, partner_id)
    q = db.query(PartnerServiceArea).filter(PartnerServiceArea.partner_id == partner_id)
    if only_active:
        q = q.filter(PartnerServiceArea.is_active.is_(True))
    rows = q.order_by(PartnerServiceArea.priority).limit(limit).all()
    items = [ServiceAreaOut.model_validate(r) for r in rows]
    return ServiceAreaListOut(partner_id=partner_id, items=items, total=len(items))


def create_service_area(db: Session, partner_id: str, body: ServiceAreaCreateIn) -> ServiceAreaOut:
    pid, default_pt = _resolve_partner(db, partner_id)
    pt = body.partner_type.upper() if body.partner_type else default_pt
    now = _utcnow()
    row = PartnerServiceArea(
        id=new_id(),
        partner_id=pid,
        partner_type=pt,
        locker_id=body.locker_id,
        priority=body.priority,
        exclusive=body.exclusive,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
        is_active=body.is_active,
        created_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ServiceAreaOut.model_validate(row)


def list_billing_plans(db: Session, partner_id: str) -> BillingPlanListOut:
    _resolve_partner(db, partner_id)
    rows = (
        db.query(PartnerBillingPlan)
        .filter(PartnerBillingPlan.partner_id == partner_id)
        .order_by(PartnerBillingPlan.valid_from.desc())
        .all()
    )
    items = [BillingPlanOut.model_validate(r) for r in rows]
    return BillingPlanListOut(partner_id=partner_id, items=items, total=len(items))


def list_billing_cycles(db: Session, partner_id: str, *, status_filter: str | None = None) -> BillingCycleListOut:
    _resolve_partner(db, partner_id)
    q = db.query(PartnerBillingCycle).filter(PartnerBillingCycle.partner_id == partner_id)
    if status_filter:
        q = q.filter(PartnerBillingCycle.status == status_filter.upper())
    rows = q.order_by(PartnerBillingCycle.period_start.desc()).all()
    items = [BillingCycleOut.model_validate(r) for r in rows]
    return BillingCycleListOut(partner_id=partner_id, items=items, total=len(items))


def list_stores(db: Session, *, active_only: bool = False) -> PartnerStoreListOut:
    q = db.query(PartnerStore)
    if active_only:
        q = q.filter(PartnerStore.active.is_(True))
    rows = q.order_by(PartnerStore.name).all()
    items = [PartnerStoreOut.model_validate(r) for r in rows]
    return PartnerStoreListOut(items=items, total=len(items))


def create_store(db: Session, body: PartnerStoreCreateIn) -> PartnerStoreOut:
    now = _utcnow()
    row = PartnerStore(
        id=body.id or new_id(),
        name=body.name,
        legal_name=body.legal_name,
        tax_id=body.tax_id,
        address_line=body.address_line,
        city=body.city,
        state=body.state,
        postal_code=body.postal_code,
        phone=body.phone,
        email=body.email,
        commission_pct=body.commission_pct,
        active=body.active,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return PartnerStoreOut.model_validate(row)


def list_sla_agreements(db: Session, partner_id: str) -> SlaAgreementListOut:
    _resolve_partner(db, partner_id)
    rows = (
        db.query(PartnerSlaAgreement)
        .filter(PartnerSlaAgreement.partner_id == partner_id)
        .order_by(PartnerSlaAgreement.valid_from.desc())
        .all()
    )
    items = [SlaAgreementOut.model_validate(r) for r in rows]
    return SlaAgreementListOut(partner_id=partner_id, items=items, total=len(items))


def create_sla_agreement(db: Session, partner_id: str, body: SlaAgreementCreateIn) -> SlaAgreementOut:
    pid, default_pt = _resolve_partner(db, partner_id)
    pt = body.partner_type.upper() if body.partner_type else default_pt
    row = PartnerSlaAgreement(
        id=new_id(),
        partner_id=pid,
        partner_type=pt,
        country=body.country,
        sla_pickup_hours=body.sla_pickup_hours,
        sla_return_hours=body.sla_return_hours,
        penalty_pct=body.penalty_pct,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
        is_active=True,
        created_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return SlaAgreementOut.model_validate(row)


def list_status_history(db: Session, partner_id: str, *, limit: int = 50) -> StatusHistoryListOut:
    _resolve_partner(db, partner_id)
    rows = (
        db.query(PartnerStatusHistory)
        .filter(PartnerStatusHistory.partner_id == partner_id)
        .order_by(PartnerStatusHistory.changed_at.desc())
        .limit(limit)
        .all()
    )
    items = [StatusHistoryOut.model_validate(r) for r in rows]
    return StatusHistoryListOut(partner_id=partner_id, items=items, total=len(items))


def get_ops_dashboard(
    db: Session,
    *,
    partner_id: str | None = None,
    from_dt: datetime | None = None,
    to_dt: datetime | None = None,
) -> PartnerDashboardOut:
    q_batches = db.query(PartnerSettlementBatch)
    if partner_id:
        q_batches = q_batches.filter(PartnerSettlementBatch.partner_id == partner_id)
    if from_dt:
        q_batches = q_batches.filter(PartnerSettlementBatch.created_at >= from_dt)
    if to_dt:
        q_batches = q_batches.filter(PartnerSettlementBatch.created_at <= to_dt)
    total_batches = q_batches.count()
    paid = q_batches.filter(PartnerSettlementBatch.status == "PAID").count()
    disputed = q_batches.filter(PartnerSettlementBatch.status == "DISPUTED").count()
    error_rate = round((disputed / total_batches * 100) if total_batches else 0, 2)
    prev = max(0, total_batches - 2)
    delta = total_batches - prev
    delta_pct = round((delta / prev * 100) if prev else 0, 2)
    return PartnerDashboardOut(
        from_=from_dt,
        to=to_dt,
        partner_id=partner_id,
        kpis={"total_events": total_batches, "error_rate_pct": error_rate, "paid_batches": paid},
        compare={
            "total_previous": prev,
            "total_delta_count": delta,
            "total_delta_pct": delta_pct,
            "confidence_level": "HIGH" if total_batches >= 1 else "LOW",
            "data_quality_flags": [] if total_batches else ["NO_DATA"],
        },
        changes_series=[{"label": "settlements", "value": total_batches}],
    )
