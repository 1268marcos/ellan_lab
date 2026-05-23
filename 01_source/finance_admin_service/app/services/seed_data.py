from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.finance import (
    BillingProcessedEvent,
    FinanceOpsInvoice,
    FinancePartnerAccount,
    PartnerApiKey,
    PartnerB2bInvoice,
    PartnerBillingCycle,
    PartnerBillingPlan,
    PartnerWebhookEndpoint,
    WalletProviderCatalog,
    WalletTransaction,
)
from app.models.finance_advanced import PartnerInvoiceDocument
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
from app.services.crypto_util import generate_partner_api_key, hash_secret, new_id
from app.services.finance_catalog_service import sync_global_catalog
from app.services.finance_advanced_service import seed_advanced_domain
from app.services.finance_professional_service import seed_professional_demo


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _month_bounds(ref: date) -> tuple[date, date]:
    start = ref.replace(day=1)
    if ref.month == 12:
        end = date(ref.year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(ref.year, ref.month + 1, 1) - timedelta(days=1)
    return start, end


def run_seed(db: Session) -> dict[str, int]:
    counts: dict[str, int] = {
        "partners": 0,
        "plans": 0,
        "cycles": 0,
        "b2b_invoices": 0,
        "api_keys": 0,
        "webhooks": 0,
        "wallet_providers": 0,
        "wallet_transactions": 0,
        "ops_invoices": 0,
        "billing_events": 0,
        "line_items": 0,
        "settlement_batches": 0,
        "settlement_items": 0,
        "credit_notes": 0,
        "payment_holds": 0,
        "commissions": 0,
        "cost_centers": 0,
        "cost_center_monthly": 0,
        "fiscal_gaps": 0,
        "webhook_deliveries": 0,
        "catalog_upserted": 0,
        "catalog_partners_created": 0,
        "commercial_contracts": 0,
        "integration_milestones": 0,
        "sla_definitions": 0,
        "readiness_recomputed": 0,
        "commercial_tiers": 0,
        "fx_rates": 0,
        "payment_terms": 0,
        "dunning_policies": 0,
        "tax_corridors": 0,
        "revenue_schedules": 0,
    }
    now = _utcnow()
    period_start, period_end = _month_bounds(date.today())

    catalog_sync = sync_global_catalog(db, create_partners=True, create_plans=True)
    counts["catalog_upserted"] = catalog_sync["catalog_upserted"]
    counts["catalog_partners_created"] = catalog_sync["partners_created"]
    counts["partners"] = catalog_sync["partners_created"]
    counts["plans"] += catalog_sync["plans_created"]

    partner_ids: dict[str, str] = {}
    for row in db.query(FinancePartnerAccount).all():
        partner_ids[row.code] = row.id

    db.flush()

    if not db.query(WalletProviderCatalog).filter(WalletProviderCatalog.code == "PICPAY").first():
        for code, name in [
            ("PICPAY", "PicPay"),
            ("MERCADOPAGO", "Mercado Pago Wallet"),
            ("PAYPAL", "PayPal"),
            ("APPLE_PAY", "Apple Pay"),
        ]:
            db.add(WalletProviderCatalog(code=code, name=name, is_active=True, created_at=now, updated_at=now))
            counts["wallet_providers"] += 1

    magalu_id = partner_ids.get("MAGALU")
    magalu_cycle_id: str | None = None
    magalu_b2b_id: str | None = None
    magalu_has_demo = (
        magalu_id
        and db.query(PartnerB2bInvoice).filter(PartnerB2bInvoice.partner_id == magalu_id).first()
    )
    if magalu_id and not magalu_has_demo and not db.query(PartnerBillingPlan).filter(
        PartnerBillingPlan.partner_id == magalu_id
    ).first():
        plan_id = new_id()
        db.add(
            PartnerBillingPlan(
                id=plan_id,
                partner_id=magalu_id,
                partner_type="ECOMMERCE",
                plan_name="Magalu Hybrid 2026",
                billing_model="HYBRID",
                currency="BRL",
                country_code="BR",
                monthly_fee_cents=150000,
                fee_per_delivery_cents=350,
                fee_per_pickup_cents=250,
                fee_per_day_stored_cents=120,
                revenue_share_pct=Decimal("0.0250"),
                valid_from=period_start,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )
        counts["plans"] += 1
        cycle_id = new_id()
        db.add(
            PartnerBillingCycle(
                id=cycle_id,
                partner_id=magalu_id,
                partner_type="ECOMMERCE",
                billing_plan_id=plan_id,
                currency="BRL",
                period_start=period_start,
                period_end=period_end,
                total_amount_cents=287500,
                status="REVIEW",
                notes="Seed ciclo Magalu",
                created_at=now,
                updated_at=now,
            )
        )
        counts["cycles"] += 1
        magalu_cycle_id = cycle_id
        b2b_id = new_id()
        magalu_b2b_id = b2b_id
        db.add(
            PartnerB2bInvoice(
                id=b2b_id,
                cycle_id=cycle_id,
                partner_id=magalu_id,
                invoice_number="NF-B2B-MAG-2026-001",
                document_type="NFS_E",
                amount_cents=287500,
                tax_cents=17250,
                currency="BRL",
                status="ISSUED",
                due_date=period_end + timedelta(days=15),
                issued_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        counts["b2b_invoices"] += 1
        if not db.query(PartnerInvoiceDocument).filter(PartnerInvoiceDocument.invoice_id == b2b_id).first():
            db.add(
                PartnerInvoiceDocument(
                    id=new_id(),
                    invoice_id=b2b_id,
                    document_kind="PDF",
                    storage_uri=f"s3://ellan-finance/b2b/{b2b_id}.pdf",
                    access_key="35260123456789012345678901234567890123456789",
                    fiscal_invoice_id=b2b_id,
                    country="BR",
                    issued_at=now,
                )
            )
        db.add(
            PartnerBillingLineItem(
                cycle_id=cycle_id,
                partner_id=magalu_id,
                locker_id="LOCKER-DEMO-SP-01",
                line_type="BASE_FEE",
                description="Mensalidade Magalu Hybrid",
                quantity=Decimal("1"),
                unit_price_cents=150000,
                total_cents=150000,
                currency="BRL",
                created_at=now,
            )
        )
        db.add(
            PartnerBillingLineItem(
                cycle_id=cycle_id,
                partner_id=magalu_id,
                locker_id="LOCKER-DEMO-SP-01",
                line_type="DELIVERY_FEE",
                description="Entregas locker SP (820 un)",
                quantity=Decimal("820"),
                unit_price_cents=350,
                total_cents=287000,
                currency="BRL",
                created_at=now,
            )
        )
        counts["line_items"] += 2

    if magalu_id and not magalu_cycle_id:
        cy = (
            db.query(PartnerBillingCycle)
            .filter(PartnerBillingCycle.partner_id == magalu_id)
            .order_by(PartnerBillingCycle.created_at.desc())
            .first()
        )
        if cy:
            magalu_cycle_id = cy.id
        inv = (
            db.query(PartnerB2bInvoice)
            .filter(PartnerB2bInvoice.partner_id == magalu_id)
            .first()
        )
        if inv:
            magalu_b2b_id = inv.id

    if magalu_id and not db.query(PartnerB2bInvoice).filter(PartnerB2bInvoice.partner_id == magalu_id).first():
        plan = (
            db.query(PartnerBillingPlan)
            .filter(PartnerBillingPlan.partner_id == magalu_id, PartnerBillingPlan.is_active.is_(True))
            .first()
        )
        if plan:
            cycle_id = new_id()
            magalu_cycle_id = cycle_id
            db.add(
                PartnerBillingCycle(
                    id=cycle_id,
                    partner_id=magalu_id,
                    partner_type="ECOMMERCE",
                    billing_plan_id=plan.id,
                    currency="BRL",
                    period_start=period_start,
                    period_end=period_end,
                    total_amount_cents=287500,
                    status="REVIEW",
                    created_at=now,
                    updated_at=now,
                )
            )
            counts["cycles"] += 1
            b2b_id = new_id()
            magalu_b2b_id = b2b_id
            db.add(
                PartnerB2bInvoice(
                    id=b2b_id,
                    cycle_id=cycle_id,
                    partner_id=magalu_id,
                    invoice_number="NF-B2B-MAG-2026-001",
                    document_type="NFS_E",
                    amount_cents=287500,
                    tax_cents=17250,
                    currency="BRL",
                    status="ISSUED",
                    due_date=period_end + timedelta(days=15),
                    issued_at=now,
                    created_at=now,
                    updated_at=now,
                )
            )
            counts["b2b_invoices"] += 1

    if magalu_id:
        inv_doc = (
            db.query(PartnerB2bInvoice)
            .filter(PartnerB2bInvoice.partner_id == magalu_id)
            .order_by(PartnerB2bInvoice.created_at.desc())
            .first()
        )
        if inv_doc and not db.query(PartnerInvoiceDocument).filter(
            PartnerInvoiceDocument.invoice_id == inv_doc.id
        ).first():
            db.add(
                PartnerInvoiceDocument(
                    id=new_id(),
                    invoice_id=inv_doc.id,
                    document_kind="PDF",
                    storage_uri=f"s3://ellan-finance/b2b/{inv_doc.id}.pdf",
                    access_key="35260123456789012345678901234567890123456789",
                    fiscal_invoice_id=inv_doc.id,
                    country="BR",
                    issued_at=now,
                )
            )

    for code, pid in partner_ids.items():
        if db.query(PartnerWebhookEndpoint).filter(PartnerWebhookEndpoint.partner_id == pid).first():
            continue
        secret = f"whsec_{code.lower()}_demo"
        db.add(
            PartnerWebhookEndpoint(
                id=new_id(),
                partner_id=pid,
                partner_type="ECOMMERCE" if code in ("MAGALU", "MELI", "WORTEN") else "CARRIER",
                url=f"https://hooks.ellanlab.example/{code.lower()}/billing",
                secret_hash=hash_secret(secret),
                secret_key=secret,
                events_json='["billing.cycle.closed","invoice.issued"]',
                created_at=now,
                updated_at=now,
            )
        )
        counts["webhooks"] += 1
        if not db.query(PartnerApiKey).filter(PartnerApiKey.partner_id == pid).first():
            full, prefix, key_hash = generate_partner_api_key(code)
            db.add(
                PartnerApiKey(
                    id=new_id(),
                    partner_id=pid,
                    partner_type="ECOMMERCE",
                    key_prefix=prefix,
                    key_hash=key_hash,
                    label="seed",
                    scopes_json='["billing:read"]',
                    created_at=now,
                )
            )
            counts["api_keys"] += 1

    if not db.query(WalletTransaction).first():
        db.add(
            WalletTransaction(
                id=new_id(),
                wallet_id="wallet-demo-magalu",
                order_id="ord-seed-001",
                type="CREDIT",
                amount_cents=4990,
                balance_after_cents=4990,
                status="SETTLED",
                description="Seed credit Magalu pickup",
                created_at=now,
            )
        )
        counts["wallet_transactions"] += 1

    if not db.query(FinanceOpsInvoice).first():
        db.add(
            FinanceOpsInvoice(
                id="inv-seed-nfce-001",
                order_id="ord-seed-001",
                country="BR",
                invoice_type="NFC_E",
                status="AUTHORIZED",
                amount_cents=4990,
                currency="BRL",
                locker_id="LOCKER-DEMO-SP-01",
                created_at=now,
                updated_at=now,
            )
        )
        counts["ops_invoices"] += 1

    if not db.query(BillingProcessedEvent).first():
        db.add(
            BillingProcessedEvent(
                id=new_id(),
                event_id="evt-seed-payment-captured-001",
                order_id="ord-seed-001",
                event_type="payment.captured",
                processed_at=now,
                payload_json='{"source":"seed"}',
            )
        )
        counts["billing_events"] += 1

    meli_id = partner_ids.get("MERCADOLIVRE")
    if meli_id and not db.query(PartnerSettlementBatch).filter(PartnerSettlementBatch.partner_id == meli_id).first():
        batch_id = new_id()
        db.add(
            PartnerSettlementBatch(
                id=batch_id,
                partner_id=meli_id,
                partner_type="ECOMMERCE",
                period_start=period_start,
                period_end=period_end,
                currency="BRL",
                total_orders=1240,
                gross_revenue_cents=6200000,
                revenue_share_pct=Decimal("0.0300"),
                revenue_share_cents=186000,
                fees_cents=45000,
                net_amount_cents=5971000,
                status="APPROVED",
                settlement_ref="STL-MELI-2026-05",
                created_at=now,
                updated_at=now,
            )
        )
        counts["settlement_batches"] += 1
        db.add(
            PartnerSettlementItem(
                batch_id=batch_id,
                order_id="ord-meli-seed-001",
                order_date=now,
                gross_cents=4990,
                share_pct=Decimal("0.03"),
                share_cents=150,
                currency="BRL",
            )
        )
        counts["settlement_items"] += 1

    if magalu_id and magalu_b2b_id and not db.query(PartnerCreditNote).filter(PartnerCreditNote.partner_id == magalu_id).first():
        db.add(
            PartnerCreditNote(
                id=new_id(),
                partner_id=magalu_id,
                original_invoice_id=magalu_b2b_id,
                cycle_id=magalu_cycle_id,
                reason_code="SLA_BREACH",
                description="Crédito SLA pickup > 72h — rede SwipBox SP",
                amount_cents=12500,
                currency="BRL",
                status="APPROVED",
                created_at=now,
                updated_at=now,
            )
        )
        counts["credit_notes"] += 1
        db.add(
            PartnerPaymentHold(
                id=new_id(),
                partner_id=magalu_id,
                invoice_id=magalu_b2b_id,
                hold_amount_cents=50000,
                release_schedule="AFTER_15_DAYS",
                status="HELD",
                created_at=now,
            )
        )
        counts["payment_holds"] += 1

    if magalu_id and not db.query(PartnerCommissionStructure).filter(PartnerCommissionStructure.partner_id == magalu_id).first():
        db.add(
            PartnerCommissionStructure(
                id=new_id(),
                partner_id=magalu_id,
                commission_percentage=Decimal("2.50"),
                revenue_threshold_cents=1000000,
                effective_from=period_start,
                created_at=now,
            )
        )
        counts["commissions"] += 1

    if not db.query(CostCenter).filter(CostCenter.locker_id == "LOCKER-DEMO-SP-01").first():
        db.add(
            CostCenter(
                id=new_id(),
                locker_id="LOCKER-DEMO-SP-01",
                region_code="BR-SP",
                network_code="SWIPBOX",
                operational_cost_monthly_cents=185000,
                created_at=now,
                updated_at=now,
            )
        )
        counts["cost_centers"] += 1
        db.add(
            CostCenterMonthly(
                id=new_id(),
                locker_id="LOCKER-DEMO-SP-01",
                month=period_start,
                rent_cents=45000,
                maintenance_preventive_cents=35000,
                connectivity_cents=30000,
                energy_cents=22000,
                insurance_cents=50000,
                payment_gateway_fee_cents=18000,
                depreciation_cents=25000,
                created_at=now,
                updated_at=now,
            )
        )
        counts["cost_center_monthly"] += 1

    if not db.query(FiscalReconciliationGap).first():
        db.add(
            FiscalReconciliationGap(
                id="gap-seed-nfce-missing-001",
                dedupe_key="ord-seed-001|nfce|missing",
                gap_type="INVOICE_NOT_FOUND",
                severity="HIGH",
                status="OPEN",
                order_id="ord-seed-001",
                invoice_id="inv-seed-nfce-001",
                details_json='{"corridor":"BR","provider":"sefaz-sp"}',
                first_detected_at=now,
                last_detected_at=now,
            )
        )
        counts["fiscal_gaps"] += 1

    wh = db.query(PartnerWebhookEndpoint).filter(PartnerWebhookEndpoint.partner_id == magalu_id).first() if magalu_id else None
    if wh and not db.query(PartnerWebhookDelivery).filter(PartnerWebhookDelivery.endpoint_id == wh.id).first():
        db.add(
            PartnerWebhookDelivery(
                id=new_id(),
                endpoint_id=wh.id,
                event_id="evt-wh-001",
                event_type="billing.cycle.closed",
                payload_json='{"cycle_status":"REVIEW"}',
                http_status=500,
                attempt_count=3,
                status="FAILED",
                last_error="Connection timeout to partner endpoint",
                created_at=now,
            )
        )
        db.add(
            PartnerWebhookDelivery(
                id=new_id(),
                endpoint_id=wh.id,
                event_id="evt-wh-002",
                event_type="invoice.issued",
                payload_json='{"invoice_number":"NF-B2B-MAG-2026-001"}',
                http_status=200,
                attempt_count=1,
                status="DELIVERED",
                delivered_at=now,
                created_at=now,
            )
        )
        counts["webhook_deliveries"] += 2

    pro = seed_professional_demo(db)
    counts["commercial_contracts"] = pro.get("contracts", 0)
    counts["integration_milestones"] = pro.get("milestones", 0)
    counts["sla_definitions"] = pro.get("slas", 0)
    counts["readiness_recomputed"] = pro.get("readiness", 0)

    if magalu_cycle_id:
        cy_row = db.get(PartnerBillingCycle, magalu_cycle_id)
        if cy_row and cy_row.status != "CLOSED":
            cy_row.status = "CLOSED"
            cy_row.updated_at = now
        from app.services.finance_revenue_service import create_schedule_from_cycle, run_straight_line_recognition

        try:
            create_schedule_from_cycle(db, magalu_cycle_id)
            run_straight_line_recognition(db, through_date=period_end)
            counts["revenue_schedules"] = 1
        except Exception:
            pass

    adv = seed_advanced_domain(db)
    counts["commercial_tiers"] = adv.get("tiers", 0)
    counts["fx_rates"] = adv.get("fx_rates", 0)
    counts["payment_terms"] = adv.get("payment_terms", 0)
    counts["dunning_policies"] = adv.get("dunning_policies", 0)
    counts["tax_corridors"] = adv.get("tax_corridors", 0)

    db.commit()
    return counts
