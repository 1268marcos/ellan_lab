from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.finance import PartnerB2bInvoice, PartnerBillingCycle, PartnerBillingPlan
from app.models.finance_catalog import FinanceLockerNetworkCatalog
from app.models.finance_ecosystem import FinancePlayerCapability, FinancePlayerRelation
from app.models.finance_extended import PartnerBillingLineItem, PartnerCreditNote, PartnerWebhookDelivery
from app.models.finance_professional import (
    FinanceIntegrationMilestone,
    FinancePartnerReadiness,
    PartnerCommercialContract,
    PartnerSlaBreach,
    PartnerSlaDefinition,
)
from app.schemas.finance_professional import (
    CommercialContractIn,
    IntegrationMilestoneIn,
    IntegrationMilestoneUpdate,
    SlaBreachIn,
    SlaDefinitionIn,
)
from app.services.crypto_util import new_id
from app.services.finance_readiness_service import list_readiness, recompute_all_readiness


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- Contracts ---
def list_contracts(db: Session, partner_id: str | None = None) -> list[PartnerCommercialContract]:
    q = db.query(PartnerCommercialContract).order_by(PartnerCommercialContract.effective_from.desc())
    if partner_id:
        q = q.filter(PartnerCommercialContract.partner_id == partner_id)
    return q.all()


def create_contract(db: Session, body: CommercialContractIn) -> PartnerCommercialContract:
    row = PartnerCommercialContract(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# --- Milestones ---
def list_milestones(db: Session, catalog_code: str | None = None) -> list[FinanceIntegrationMilestone]:
    q = db.query(FinanceIntegrationMilestone).order_by(
        FinanceIntegrationMilestone.catalog_code,
        FinanceIntegrationMilestone.sort_order,
    )
    if catalog_code:
        q = q.filter(FinanceIntegrationMilestone.catalog_code == catalog_code)
    return q.all()


def create_milestone(db: Session, body: IntegrationMilestoneIn) -> FinanceIntegrationMilestone:
    row = FinanceIntegrationMilestone(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_milestone(db: Session, milestone_id: str, body: IntegrationMilestoneUpdate) -> FinanceIntegrationMilestone:
    row = db.get(FinanceIntegrationMilestone, milestone_id)
    if not row:
        raise HTTPException(status_code=404, detail="Milestone not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    if body.status == "DONE" and not row.completed_at:
        row.completed_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


# --- SLA ---
def list_sla_definitions(db: Session, partner_id: str | None = None) -> list[PartnerSlaDefinition]:
    q = db.query(PartnerSlaDefinition).order_by(PartnerSlaDefinition.metric_code)
    if partner_id:
        q = q.filter(PartnerSlaDefinition.partner_id == partner_id)
    return q.all()


def create_sla_definition(db: Session, body: SlaDefinitionIn) -> PartnerSlaDefinition:
    row = PartnerSlaDefinition(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_sla_breaches(db: Session, partner_id: str | None = None, status: str | None = None) -> list[PartnerSlaBreach]:
    q = db.query(PartnerSlaBreach).order_by(PartnerSlaBreach.breach_at.desc())
    if partner_id:
        q = q.filter(PartnerSlaBreach.partner_id == partner_id)
    if status:
        q = q.filter(PartnerSlaBreach.status == status)
    return q.all()


def record_sla_breach(db: Session, body: SlaBreachIn) -> PartnerSlaBreach:
    sla = db.get(PartnerSlaDefinition, body.sla_id)
    if not sla:
        raise HTTPException(status_code=404, detail="SLA definition not found")
    breach_at = body.breach_at or _utcnow()
    credit_note_id: str | None = None
    if body.auto_credit_note and sla.penalty_credit_pct:
        plan = (
            db.query(PartnerBillingPlan)
            .filter(PartnerBillingPlan.partner_id == body.partner_id, PartnerBillingPlan.is_active.is_(True))
            .first()
        )
        base_cents = int(plan.monthly_fee_cents or 100000) if plan else 100000
        amount = int(base_cents * float(sla.penalty_credit_pct))
        credit_note_id = new_id()
        db.add(
            PartnerCreditNote(
                id=credit_note_id,
                partner_id=body.partner_id,
                reason_code="SLA_BREACH",
                description=f"SLA breach {sla.metric_code}: observed {body.observed_value}",
                amount_cents=amount,
                currency=plan.currency if plan else "BRL",
                status="PENDING",
                created_at=_utcnow(),
                updated_at=_utcnow(),
            )
        )
    row = PartnerSlaBreach(
        id=new_id(),
        sla_id=body.sla_id,
        partner_id=body.partner_id,
        observed_value=body.observed_value,
        breach_at=breach_at,
        status="OPEN",
        credit_note_id=credit_note_id,
        notes=body.notes,
        created_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def ecosystem_summary(db: Session) -> dict:
    players = db.query(FinanceLockerNetworkCatalog).filter(FinanceLockerNetworkCatalog.active.is_(True)).all()
    by_segment: Counter[str] = Counter()
    by_status: Counter[str] = Counter()
    linked = 0
    for p in players:
        by_segment[p.segment_code or p.parent_group] += 1
        by_status[p.integration_status] += 1
        if p.finance_partner_id:
            linked += 1
    rel_total = db.query(func.count(FinancePlayerRelation.id)).scalar() or 0
    cap_total = db.query(func.count(FinancePlayerCapability.id)).scalar() or 0
    readiness_rows = list_readiness(db)
    avg = sum(r.readiness_score for r in readiness_rows) / len(readiness_rows) if readiness_rows else 0.0
    top = readiness_rows[:5]
    return {
        "total_players": len(players),
        "live_count": by_status.get("LIVE", 0),
        "pilot_count": by_status.get("PILOT", 0),
        "planned_count": by_status.get("PLANNED", 0) + by_status.get("IN_PROGRESS", 0),
        "linked_partners": linked,
        "total_relations": rel_total,
        "total_capabilities": cap_total,
        "by_segment": dict(by_segment),
        "by_integration_status": dict(by_status),
        "readiness_average": round(avg, 2),
        "top_ready": top,
    }


def close_billing_cycle(db: Session, cycle_id: str) -> dict:
    from app.models.finance import FinancePartnerAccount
    from app.services.finance_advanced_service import compute_tax_cents, resolve_due_date
    from app.services.finance_audit_service import log_audit

    cycle = db.get(PartnerBillingCycle, cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Billing cycle not found")
    if cycle.status == "CLOSED":
        raise HTTPException(status_code=409, detail="Cycle already closed")

    items = db.query(PartnerBillingLineItem).filter(PartnerBillingLineItem.cycle_id == cycle_id).all()
    total = sum(int(i.total_cents) for i in items)
    if total == 0 and cycle.total_amount_cents:
        total = int(cycle.total_amount_cents)

    partner = db.get(FinancePartnerAccount, cycle.partner_id)
    origin = partner.country_code if partner else "BR"
    tax_cents = compute_tax_cents(db, cycle.partner_id, total, origin, origin)

    cycle.total_amount_cents = total
    cycle.status = "CLOSED"
    cycle.updated_at = _utcnow()

    due = resolve_due_date(db, cycle.partner_id, cycle.period_end)
    invoice = (
        db.query(PartnerB2bInvoice).filter(PartnerB2bInvoice.cycle_id == cycle_id).first()
    )
    invoice_id: str | None = None
    if not invoice:
        invoice_id = new_id()
        db.add(
            PartnerB2bInvoice(
                id=invoice_id,
                cycle_id=cycle_id,
                partner_id=cycle.partner_id,
                invoice_number=f"NF-B2B-{cycle.partner_id[:8]}-{cycle.period_end:%Y%m}",
                amount_cents=total,
                tax_cents=tax_cents,
                currency=cycle.currency,
                status="ISSUED",
                issued_at=_utcnow(),
                due_date=due,
            )
        )
    else:
        invoice_id = invoice.id
        invoice.amount_cents = total
        invoice.tax_cents = tax_cents
        invoice.status = "ISSUED"
        invoice.issued_at = _utcnow()
        invoice.due_date = due

    log_audit(
        db,
        action="CLOSE_CYCLE",
        entity_type="billing_cycle",
        entity_id=cycle_id,
        after={"total_amount_cents": total, "tax_cents": tax_cents, "invoice_id": invoice_id, "due_date": str(due)},
    )
    db.commit()
    return {
        "cycle_id": cycle_id,
        "status": "CLOSED",
        "total_amount_cents": total,
        "tax_cents": tax_cents,
        "due_date": str(due),
        "invoice_id": invoice_id,
        "line_items_summed": len(items),
    }


def replay_webhook_delivery(db: Session, delivery_id: str) -> PartnerWebhookDelivery:
    row = db.get(PartnerWebhookDelivery, delivery_id)
    if not row:
        raise HTTPException(status_code=404, detail="Webhook delivery not found")
    row.attempt_count = int(row.attempt_count or 0) + 1
    row.status = "RETRYING"
    row.last_error = None
    # Simula entrega bem-sucedida no replay (ops pode ligar HTTP real depois)
    row.http_status = 200
    row.status = "DELIVERED"
    row.delivered_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def seed_professional_demo(db: Session) -> dict[str, int]:
    """Idempotente: contratos, milestones, SLAs para players prioritários."""
    from app.data.global_locker_finance_catalog import FINANCE_DEMO_PRIORITY_CODES
    from app.models.finance import FinancePartnerAccount

    counts = {"contracts": 0, "milestones": 0, "slas": 0, "breaches": 0}
    today = date.today()

    phase_templates = [
        ("DISCOVERY", "Due diligence técnica e fiscal", 10),
        ("PILOT", "Piloto em 3 lockers", 30),
        ("UAT", "UAT billing + webhooks", 45),
        ("LIVE", "Go-live produção", 60),
    ]

    for code in FINANCE_DEMO_PRIORITY_CODES:
        partner = db.query(FinancePartnerAccount).filter(FinancePartnerAccount.code == code).first()
        if partner and not db.query(PartnerCommercialContract).filter(
            PartnerCommercialContract.partner_id == partner.id,
            PartnerCommercialContract.title.like(f"%{code}%"),
        ).first():
            db.add(
                PartnerCommercialContract(
                    id=new_id(),
                    partner_id=partner.id,
                    catalog_code=code,
                    contract_type="MSA",
                    title=f"MSA {code} Global 2026",
                    effective_from=today.replace(day=1),
                    currency=partner.currency,
                    status="ACTIVE",
                    metadata_json=json.dumps({"corridor": partner.country_code or "BR"}),
                )
            )
            counts["contracts"] += 1

        for phase, title, days in phase_templates:
            exists = (
                db.query(FinanceIntegrationMilestone)
                .filter(
                    FinanceIntegrationMilestone.catalog_code == code,
                    FinanceIntegrationMilestone.phase == phase,
                )
                .first()
            )
            if not exists:
                target = today.replace(day=min(days, 28))
                status = "DONE" if phase == "DISCOVERY" and code in ("MAGALU", "INPOST", "MERCADOLIVRE") else "PENDING"
                db.add(
                    FinanceIntegrationMilestone(
                        id=new_id(),
                        catalog_code=code,
                        phase=phase,
                        title=title,
                        target_date=target,
                        status=status,
                        owner="finance-ops",
                        completed_at=_utcnow() if status == "DONE" else None,
                        sort_order=days,
                    )
                )
                counts["milestones"] += 1

        if partner and not db.query(PartnerSlaDefinition).filter(
            PartnerSlaDefinition.partner_id == partner.id,
            PartnerSlaDefinition.metric_code == "WEBHOOK_SUCCESS_RATE",
        ).first():
            db.add(
                PartnerSlaDefinition(
                    id=new_id(),
                    partner_id=partner.id,
                    catalog_code=code,
                    metric_code="WEBHOOK_SUCCESS_RATE",
                    metric_name="Taxa sucesso webhooks billing",
                    target_value=Decimal("99.5000"),
                    target_unit="PCT",
                    window_days=30,
                    penalty_credit_pct=Decimal("0.0100"),
                    active=True,
                )
            )
            counts["slas"] += 1

    n, _avg = recompute_all_readiness(db)
    counts["readiness"] = n
    db.commit()
    return counts
