from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.finance import PartnerB2bInvoice, PartnerBillingCycle, FinancePartnerAccount
from app.models.finance_advanced import (
    FinanceAuditLog,
    FinanceFxRate,
    PartnerCommercialTier,
    PartnerDunningCase,
    PartnerDunningPolicy,
    PartnerInvoiceDocument,
    PartnerPaymentTerms,
    PartnerTaxCorridor,
    PartnerTierAssignment,
    SettlementReconciliationMatch,
    SettlementReconciliationRun,
)
from app.models.finance_extended import PartnerSettlementBatch, PartnerSettlementItem
from app.models.finance import WalletTransaction
from app.schemas.finance_advanced import (
    CommercialTierIn,
    DunningPolicyIn,
    FxRateIn,
    InvoiceDocumentIn,
    PaymentTermsIn,
    TaxCorridorIn,
    TierAssignmentIn,
)
from app.services.crypto_util import new_id
from app.services.finance_audit_service import log_audit


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- Payment terms ---
def list_payment_terms(db: Session, partner_id: str | None = None) -> list[PartnerPaymentTerms]:
    q = db.query(PartnerPaymentTerms)
    if partner_id:
        q = q.filter(PartnerPaymentTerms.partner_id == partner_id)
    return q.all()


def create_payment_terms(db: Session, body: PaymentTermsIn) -> PartnerPaymentTerms:
    if body.is_default:
        db.query(PartnerPaymentTerms).filter(PartnerPaymentTerms.partner_id == body.partner_id).update(
            {"is_default": False}
        )
    row = PartnerPaymentTerms(id=new_id(), **body.model_dump())
    db.add(row)
    log_audit(db, action="CREATE", entity_type="payment_terms", entity_id=row.id, after=body.model_dump())
    db.commit()
    db.refresh(row)
    return row


def resolve_due_date(db: Session, partner_id: str, period_end: date) -> date:
    terms = (
        db.query(PartnerPaymentTerms)
        .filter(PartnerPaymentTerms.partner_id == partner_id, PartnerPaymentTerms.is_default.is_(True))
        .first()
    )
    net = terms.net_days if terms else 30
    grace = terms.grace_days if terms else 0
    return period_end + timedelta(days=net + grace)


# --- FX ---
def list_fx_rates(db: Session, base: str | None = None, quote: str | None = None) -> list[FinanceFxRate]:
    q = db.query(FinanceFxRate).order_by(FinanceFxRate.rate_date.desc())
    if base:
        q = q.filter(FinanceFxRate.base_currency == base.upper())
    if quote:
        q = q.filter(FinanceFxRate.quote_currency == quote.upper())
    return q.limit(100).all()


def upsert_fx_rate(db: Session, body: FxRateIn) -> FinanceFxRate:
    existing = (
        db.query(FinanceFxRate)
        .filter(
            FinanceFxRate.base_currency == body.base_currency.upper(),
            FinanceFxRate.quote_currency == body.quote_currency.upper(),
            FinanceFxRate.rate_date == body.rate_date,
        )
        .first()
    )
    if existing:
        existing.rate = body.rate
        existing.source = body.source
        row = existing
    else:
        row = FinanceFxRate(
            id=new_id(),
            base_currency=body.base_currency.upper(),
            quote_currency=body.quote_currency.upper(),
            rate_date=body.rate_date,
            rate=body.rate,
            source=body.source,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def convert_cents(db: Session, amount_cents: int, from_ccy: str, to_ccy: str, on_date: date | None = None) -> dict:
    from_ccy, to_ccy = from_ccy.upper(), to_ccy.upper()
    if from_ccy == to_ccy:
        return {
            "amount_cents": amount_cents,
            "from_currency": from_ccy,
            "to_currency": to_ccy,
            "converted_cents": amount_cents,
            "rate": Decimal("1"),
            "rate_date": on_date or date.today(),
        }
    ref_date = on_date or date.today()
    rate_row = (
        db.query(FinanceFxRate)
        .filter(
            FinanceFxRate.base_currency == from_ccy,
            FinanceFxRate.quote_currency == to_ccy,
            FinanceFxRate.rate_date <= ref_date,
        )
        .order_by(FinanceFxRate.rate_date.desc())
        .first()
    )
    if not rate_row:
        raise HTTPException(status_code=404, detail=f"FX rate {from_ccy}/{to_ccy} not found")
    converted = int(Decimal(amount_cents) * rate_row.rate)
    return {
        "amount_cents": amount_cents,
        "from_currency": from_ccy,
        "to_currency": to_ccy,
        "converted_cents": converted,
        "rate": rate_row.rate,
        "rate_date": rate_row.rate_date,
    }


# --- Tiers ---
def list_tiers(db: Session) -> list[PartnerCommercialTier]:
    return db.query(PartnerCommercialTier).order_by(PartnerCommercialTier.sort_order).all()


def upsert_tier(db: Session, body: CommercialTierIn) -> PartnerCommercialTier:
    row = db.get(PartnerCommercialTier, body.tier_code)
    if row:
        for k, v in body.model_dump().items():
            setattr(row, k, v)
    else:
        row = PartnerCommercialTier(**body.model_dump())
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_tier_assignments(db: Session, partner_id: str | None = None) -> list[PartnerTierAssignment]:
    q = db.query(PartnerTierAssignment).order_by(PartnerTierAssignment.effective_from.desc())
    if partner_id:
        q = q.filter(PartnerTierAssignment.partner_id == partner_id)
    return q.all()


def assign_tier(db: Session, body: TierAssignmentIn) -> PartnerTierAssignment:
    if not db.get(PartnerCommercialTier, body.tier_code):
        raise HTTPException(status_code=404, detail="Tier not found")
    row = PartnerTierAssignment(id=new_id(), **body.model_dump())
    db.add(row)
    log_audit(db, action="ASSIGN_TIER", entity_type="partner", entity_id=body.partner_id, after=body.model_dump())
    db.commit()
    db.refresh(row)
    return row


def resolve_tier_for_partner(db: Session, partner_id: str) -> PartnerCommercialTier | None:
    today = date.today()
    assign = (
        db.query(PartnerTierAssignment)
        .filter(
            PartnerTierAssignment.partner_id == partner_id,
            PartnerTierAssignment.effective_from <= today,
        )
        .order_by(PartnerTierAssignment.effective_from.desc())
        .first()
    )
    if not assign:
        return db.get(PartnerCommercialTier, "STANDARD")
    return db.get(PartnerCommercialTier, assign.tier_code)


# --- Dunning ---
def list_dunning_policies(db: Session) -> list[PartnerDunningPolicy]:
    return db.query(PartnerDunningPolicy).filter(PartnerDunningPolicy.active.is_(True)).order_by(PartnerDunningPolicy.stage).all()


def create_dunning_policy(db: Session, body: DunningPolicyIn) -> PartnerDunningPolicy:
    row = PartnerDunningPolicy(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_dunning_cases(db: Session, status: str | None = None) -> list[PartnerDunningCase]:
    q = db.query(PartnerDunningCase).order_by(PartnerDunningCase.created_at.desc())
    if status:
        q = q.filter(PartnerDunningCase.status == status)
    return q.all()


def scan_overdue_invoices(db: Session) -> dict[str, int]:
    today = date.today()
    opened = 0
    scanned = 0
    policies = list_dunning_policies(db)
    if not policies:
        return {"cases_opened": 0, "invoices_scanned": 0}

    invoices = (
        db.query(PartnerB2bInvoice)
        .filter(PartnerB2bInvoice.status.in_(("ISSUED", "OVERDUE")), PartnerB2bInvoice.paid_at.is_(None))
        .all()
    )
    for inv in invoices:
        scanned += 1
        if not inv.due_date or inv.due_date >= today:
            continue
        days_late = (today - inv.due_date).days
        stage = 1
        for p in sorted(policies, key=lambda x: x.days_overdue, reverse=True):
            if days_late >= p.days_overdue:
                stage = p.stage
                break
        existing = (
            db.query(PartnerDunningCase)
            .filter(PartnerDunningCase.invoice_id == inv.id, PartnerDunningCase.status == "OPEN")
            .first()
        )
        if existing:
            existing.stage = stage
            existing.amount_due_cents = inv.amount_cents
            continue
        db.add(
            PartnerDunningCase(
                id=new_id(),
                invoice_id=inv.id,
                partner_id=inv.partner_id,
                stage=stage,
                amount_due_cents=inv.amount_cents,
                status="OPEN",
                next_action_at=_utcnow() + timedelta(days=1),
            )
        )
        inv.status = "OVERDUE"
        opened += 1
    log_audit(db, action="DUNNING_SCAN", entity_type="system", entity_id="dunning", after={"opened": opened, "scanned": scanned})
    db.commit()
    return {"cases_opened": opened, "invoices_scanned": scanned}


# --- Tax corridors ---
def list_tax_corridors(db: Session, partner_id: str | None = None) -> list[PartnerTaxCorridor]:
    q = db.query(PartnerTaxCorridor).filter(PartnerTaxCorridor.active.is_(True))
    if partner_id:
        q = q.filter(PartnerTaxCorridor.partner_id == partner_id)
    return q.all()


def create_tax_corridor(db: Session, body: TaxCorridorIn) -> PartnerTaxCorridor:
    row = PartnerTaxCorridor(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def compute_tax_cents(db: Session, partner_id: str, amount_cents: int, origin: str, dest: str) -> int:
    corridor = (
        db.query(PartnerTaxCorridor)
        .filter(
            PartnerTaxCorridor.partner_id == partner_id,
            PartnerTaxCorridor.origin_country == origin,
            PartnerTaxCorridor.destination_country == dest,
            PartnerTaxCorridor.active.is_(True),
        )
        .first()
    )
    if not corridor or not corridor.withholding_pct:
        return 0
    return int(Decimal(amount_cents) * corridor.withholding_pct)


# --- Invoice documents ---
def list_invoice_documents(db: Session, invoice_id: str | None = None) -> list[PartnerInvoiceDocument]:
    q = db.query(PartnerInvoiceDocument)
    if invoice_id:
        q = q.filter(PartnerInvoiceDocument.invoice_id == invoice_id)
    return q.order_by(PartnerInvoiceDocument.created_at.desc()).all()


def create_invoice_document(db: Session, body: InvoiceDocumentIn) -> PartnerInvoiceDocument:
    row = PartnerInvoiceDocument(
        id=new_id(),
        **body.model_dump(),
        issued_at=body.issued_at or _utcnow(),
    )
    db.add(row)
    log_audit(db, action="ATTACH_DOCUMENT", entity_type="b2b_invoice", entity_id=body.invoice_id, after=body.model_dump())
    db.commit()
    db.refresh(row)
    return row


# --- Settlement reconciliation ---
def reconcile_settlement_batch(db: Session, batch_id: str) -> dict:
    batch = db.get(PartnerSettlementBatch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Settlement batch not found")
    items = db.query(PartnerSettlementItem).filter(PartnerSettlementItem.batch_id == batch_id).all()
    run = SettlementReconciliationRun(
        id=new_id(),
        batch_id=batch_id,
        run_at=_utcnow(),
        status="COMPLETED",
    )
    db.add(run)
    matched = 0
    unmatched = 0
    variance = 0
    matches_out: list[SettlementReconciliationMatch] = []

    for item in items:
        wallet = (
            db.query(WalletTransaction)
            .filter(WalletTransaction.order_id == item.order_id)
            .first()
        )
        if wallet:
            var = int(item.gross_cents) - int(wallet.amount_cents)
            status = "MATCHED" if var == 0 else "VARIANCE"
            matched += 1 if status == "MATCHED" else 0
            unmatched += 1 if status == "VARIANCE" else 0
            variance += abs(var)
        else:
            status = "UNMATCHED"
            unmatched += 1
            var = int(item.gross_cents)
            variance += var
        m = SettlementReconciliationMatch(
            run_id=run.id,
            settlement_item_id=item.id,
            order_id=item.order_id,
            wallet_tx_id=wallet.id if wallet else None,
            match_status=status,
            variance_cents=var if status != "MATCHED" else 0,
        )
        db.add(m)
        matches_out.append(m)

    run.matched_count = matched
    run.unmatched_count = unmatched
    run.variance_cents = variance
    batch.status = "SETTLED" if unmatched == 0 else "REVIEW"
    log_audit(
        db,
        action="SETTLEMENT_RECONCILE",
        entity_type="settlement_batch",
        entity_id=batch_id,
        after={"matched": matched, "unmatched": unmatched, "variance_cents": variance},
    )
    db.commit()
    db.refresh(run)
    return {"run": run, "matches": matches_out}


def seed_advanced_domain(db: Session) -> dict[str, int]:
    counts = {
        "tiers": 0,
        "fx_rates": 0,
        "payment_terms": 0,
        "dunning_policies": 0,
        "tax_corridors": 0,
        "tier_assignments": 0,
    }
    tier_defs = [
        ("STANDARD", "Standard", 0, 0, "0.0250", 10),
        ("GROWTH", "Growth", 500, 50000000, "0.0220", 20),
        ("ENTERPRISE", "Enterprise", 5000, 500000000, "0.0180", 30),
    ]
    for code, name, orders, gmv, share, sort in tier_defs:
        if not db.get(PartnerCommercialTier, code):
            db.add(
                PartnerCommercialTier(
                    tier_code=code,
                    name=name,
                    min_monthly_orders=orders,
                    min_gmv_cents=gmv,
                    default_revenue_share_pct=Decimal(share),
                    sort_order=sort,
                )
            )
            counts["tiers"] += 1

    fx_pairs = [
        ("BRL", "USD", "0.18000000"),
        ("EUR", "BRL", "5.45000000"),
        ("USD", "BRL", "5.55000000"),
        ("GBP", "EUR", "1.17000000"),
    ]
    today = date.today()
    for base, quote, rate in fx_pairs:
        if not (
            db.query(FinanceFxRate)
            .filter(
                FinanceFxRate.base_currency == base,
                FinanceFxRate.quote_currency == quote,
                FinanceFxRate.rate_date == today,
            )
            .first()
        ):
            db.add(
                FinanceFxRate(
                    id=new_id(),
                    base_currency=base,
                    quote_currency=quote,
                    rate_date=today,
                    rate=Decimal(rate),
                    source="SEED",
                )
            )
            counts["fx_rates"] += 1

    if not db.query(PartnerDunningPolicy).first():
        for stage, days, action in [(1, 7, "REMINDER"), (2, 15, "ESCALATE"), (3, 30, "HOLD")]:
            db.add(
                PartnerDunningPolicy(
                    id=new_id(),
                    partner_id=None,
                    stage=stage,
                    days_overdue=days,
                    action=action,
                    notify_channel="EMAIL",
                )
            )
            counts["dunning_policies"] += 1

    magalu = db.query(FinancePartnerAccount).filter(FinancePartnerAccount.code == "MAGALU").first()
    if magalu:
        if not db.query(PartnerPaymentTerms).filter(PartnerPaymentTerms.partner_id == magalu.id).first():
            db.add(
                PartnerPaymentTerms(
                    id=new_id(),
                    partner_id=magalu.id,
                    net_days=30,
                    grace_days=5,
                    early_payment_discount_pct=Decimal("0.0100"),
                    currency="BRL",
                )
            )
            counts["payment_terms"] += 1
        if not db.query(PartnerTierAssignment).filter(PartnerTierAssignment.partner_id == magalu.id).first():
            db.add(
                PartnerTierAssignment(
                    id=new_id(),
                    partner_id=magalu.id,
                    tier_code="ENTERPRISE",
                    effective_from=today.replace(day=1),
                    assigned_by="seed",
                )
            )
            counts["tier_assignments"] += 1
        if not db.query(PartnerTaxCorridor).filter(PartnerTaxCorridor.partner_id == magalu.id).first():
            db.add(
                PartnerTaxCorridor(
                    id=new_id(),
                    partner_id=magalu.id,
                    origin_country="BR",
                    destination_country="BR",
                    tax_regime="SIMPLES_NACIONAL",
                    withholding_pct=Decimal("0"),
                )
            )
            counts["tax_corridors"] += 1

    meli = db.query(FinancePartnerAccount).filter(FinancePartnerAccount.code == "MERCADOLIVRE").first()
    if meli and not db.query(PartnerTaxCorridor).filter(PartnerTaxCorridor.partner_id == meli.id).first():
        db.add(
            PartnerTaxCorridor(
                id=new_id(),
                partner_id=meli.id,
                origin_country="BR",
                destination_country="BR",
                tax_regime="LUCRO_PRESUMIDO",
                withholding_pct=Decimal("0.0150"),
            )
        )
        counts["tax_corridors"] += 1

    inv = None
    if magalu:
        inv = (
            db.query(PartnerB2bInvoice)
            .filter(PartnerB2bInvoice.partner_id == magalu.id)
            .order_by(PartnerB2bInvoice.created_at.desc())
            .first()
        )
    if not inv:
        inv = db.query(PartnerB2bInvoice).first()
    if inv and not db.query(PartnerInvoiceDocument).filter(PartnerInvoiceDocument.invoice_id == inv.id).first():
        db.add(
            PartnerInvoiceDocument(
                id=new_id(),
                invoice_id=inv.id,
                document_kind="PDF",
                storage_uri=f"s3://ellan-finance/b2b/{inv.id}.pdf",
                access_key="35260123456789012345678901234567890123456789",
                fiscal_invoice_id=inv.id,
                country="BR",
                issued_at=_utcnow(),
            )
        )

    db.commit()
    return counts
