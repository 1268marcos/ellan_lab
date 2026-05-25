from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.partner import EcommercePartner, LogisticsPartner
from app.models.webhook import PartnerWebhookEndpoint
from app.models.partner_extended import (
    PartnerB2bInvoice,
    PartnerBillingLineItem,
    PartnerCommissionStructure,
    PartnerCreditNote,
    PartnerIntegrationHealth,
    PartnerOrderEventOutbox,
    PartnerPaymentHold,
    PartnerWebhookDelivery,
)
from app.services.crypto_util import hash_secret
from app.services.partner_extended_service import ensure_onboarding
from app.services.security_service import seed_security_domain
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
from app.models.tenant import CustomDomain, TenantFiscalConfig, TenantPartnerLink
from app.models.user import User, UserRole
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def run_seed(db: Session) -> dict[str, int]:
    counts = {
        "users": 0,
        "user_roles": 0,
        "ecommerce": 0,
        "logistics": 0,
        "tenants": 0,
        "domains": 0,
        "tenant_links": 0,
        "settlements": 0,
        "service_areas": 0,
        "performance": 0,
        "billing_plans": 0,
        "billing_cycles": 0,
        "stores": 0,
        "sla": 0,
        "status_history": 0,
        "webhook_deliveries": 0,
        "integration_health": 0,
        "outbox": 0,
        "invoices": 0,
        "line_items": 0,
        "credit_notes": 0,
        "payment_holds": 0,
        "commissions": 0,
        "ecosystem_players": 0,
        "ecosystem_links": 0,
        "player_capabilities": 0,
        "player_relations": 0,
        "market_presence": 0,
        "capability_webhooks": 0,
        "capability_webhooks_mirrored": 0,
        "security": {},
    }
    now = _utcnow()

    users_seed = [
        ("usr-admin-ops", "Admin Operacao", "admin.operacao@ellanlab.com"),
        ("usr-suporte", "Suporte Ellan", "suporte@ellanlab.com"),
        ("usr-auditoria", "Auditoria Ellan", "auditoria@ellanlab.com"),
    ]
    for uid, name, email in users_seed:
        if not db.get(User, uid):
            db.add(
                User(
                    id=uid,
                    full_name=name,
                    email=email,
                    password_hash="!",
                    is_active=True,
                    email_verified=True,
                    phone_verified=False,
                    created_at=now,
                    updated_at=now,
                )
            )
            counts["users"] += 1

    roles_seed = [
        ("usr-admin-ops", "admin_operacao", "GLOBAL", None),
        ("usr-suporte", "suporte", "GLOBAL", None),
        ("usr-auditoria", "auditoria", "GLOBAL", None),
    ]
    for user_id, role, scope_type, scope_id in roles_seed:
        exists = (
            db.query(UserRole)
            .filter(
                UserRole.user_id == user_id,
                UserRole.role == role,
                UserRole.scope_type == scope_type,
                UserRole.revoked_at.is_(None),
            )
            .first()
        )
        if not exists:
            db.add(
                UserRole(
                    id=new_id(),
                    user_id=user_id,
                    role=role,
                    scope_type=scope_type,
                    scope_id=scope_id,
                    is_active=True,
                    granted_at=now,
                )
            )
            counts["user_roles"] += 1

    if not db.query(EcommercePartner).filter(EcommercePartner.code == "DEMO-EC").first():
        db.add(
            EcommercePartner(
                id="ec-demo-001",
                name="Demo E-commerce",
                code="DEMO-EC",
                integration_type="REST",
                api_base_url="https://api.demo-partner.example/v1",
                sla_pickup_hours=72,
                active=True,
                country="BR",
                status="ACTIVE",
                tier="STANDARD",
                support_email="ops@demo.example",
                created_at=now,
                updated_at=now,
            )
        )
        counts["ecommerce"] += 1

    if not db.query(LogisticsPartner).filter(LogisticsPartner.code == "DEMO-LG").first():
        db.add(
            LogisticsPartner(
                id="lg-demo-001",
                name="Demo Logistica",
                code="DEMO-LG",
                integration_type="REST",
                api_base_url="https://logistics.demo.example",
                tracking_url_template="https://track.demo.example/{code}",
                default_sla_hours=48,
                active=True,
                country="BR",
                created_at=now,
                updated_at=now,
            )
        )
        counts["logistics"] += 1

    if not db.get(EcommercePartner, "partner_demo_001"):
        db.add(
            EcommercePartner(
                id="partner_demo_001",
                name="Partner Demo OPS",
                code="DEMO-OPS",
                integration_type="REST",
                api_base_url="https://api.demo-ops.example/v1",
                revenue_share_pct=Decimal("0.15"),
                sla_pickup_hours=72,
                active=True,
                country="BR",
                status="ACTIVE",
                tier="STANDARD",
                support_email="ops-demo@ellanlab.com",
                created_at=now,
                updated_at=now,
            )
        )
        counts["ecommerce"] += 1

    demo_pid = "partner_demo_001"
    if not db.query(PartnerSettlementBatch).filter(PartnerSettlementBatch.id == "batch-demo-001").first():
        db.add(
            PartnerSettlementBatch(
                id="batch-demo-001",
                partner_id=demo_pid,
                partner_type="ECOMMERCE",
                period_start=date(2026, 4, 1),
                period_end=date(2026, 4, 15),
                currency="BRL",
                total_orders=12,
                gross_revenue_cents=120000,
                revenue_share_pct=Decimal("0.15"),
                revenue_share_cents=18000,
                fees_cents=2500,
                net_amount_cents=15500,
                status="DRAFT",
                notes="Seed quinzena abril",
                created_at=now,
                updated_at=now,
            )
        )
        db.add(
            PartnerSettlementItem(
                batch_id="batch-demo-001",
                order_id="ord-demo-001",
                order_date=now,
                gross_cents=10000,
                share_pct=Decimal("0.15"),
                share_cents=1500,
                currency="BRL",
            )
        )
        counts["settlements"] += 1

    if not db.query(PartnerServiceArea).filter(PartnerServiceArea.partner_id == demo_pid).first():
        db.add(
            PartnerServiceArea(
                id=new_id(),
                partner_id=demo_pid,
                partner_type="ECOMMERCE",
                locker_id="locker_sp_001",
                priority=50,
                exclusive=False,
                valid_from=date(2026, 4, 1),
                valid_until=date(2026, 12, 31),
                is_active=True,
                created_at=now,
            )
        )
        counts["service_areas"] += 1

    if not db.query(PartnerPerformanceMetric).filter(
        PartnerPerformanceMetric.partner_id == demo_pid,
        PartnerPerformanceMetric.period_month == "2026-04",
    ).first():
        db.add(
            PartnerPerformanceMetric(
                id=new_id(),
                partner_id=demo_pid,
                period_month="2026-04",
                total_orders=240,
                on_time_pickup_pct=Decimal("94.50"),
                return_rate_pct=Decimal("2.10"),
                avg_pickup_hours=Decimal("18.50"),
                sla_compliance_pct=Decimal("96.00"),
                webhook_success_rate=Decimal("99.10"),
                generated_at=now,
            )
        )
        counts["performance"] += 1

    if not db.query(PartnerBillingPlan).filter(PartnerBillingPlan.partner_id == demo_pid).first():
        plan_id = "plan-demo-001"
        db.add(
            PartnerBillingPlan(
                id=plan_id,
                partner_id=demo_pid,
                partner_type="ECOMMERCE",
                plan_name="Híbrido Demo",
                billing_model="HYBRID",
                currency="BRL",
                monthly_fee_cents=9900,
                fee_per_delivery_cents=150,
                valid_from=date(2026, 1, 1),
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )
        db.add(
            PartnerBillingCycle(
                id="cycle-demo-001",
                partner_id=demo_pid,
                partner_type="ECOMMERCE",
                billing_plan_id=plan_id,
                period_start=date(2026, 4, 1),
                period_end=date(2026, 4, 30),
                total_amount_cents=45000,
                status="OPEN",
                currency="BRL",
                created_at=now,
                updated_at=now,
            )
        )
        counts["billing_plans"] += 1
        counts["billing_cycles"] += 1

    if not db.query(PartnerStore).filter(PartnerStore.name == "Loja Demo C&C").first():
        db.add(
            PartnerStore(
                id=new_id(),
                name="Loja Demo C&C",
                legal_name="Demo Retail LTDA",
                tax_id="12.345.678/0001-99",
                address_line="Av. Paulista, 1000",
                city="São Paulo",
                state="SP",
                postal_code="01310-100",
                phone="+5511999990000",
                email="loja@demo.example",
                commission_pct=Decimal("5.00"),
                active=True,
                created_at=now,
                updated_at=now,
            )
        )
        counts["stores"] += 1

    if not db.query(PartnerSlaAgreement).filter(PartnerSlaAgreement.partner_id == demo_pid).first():
        db.add(
            PartnerSlaAgreement(
                id=new_id(),
                partner_id=demo_pid,
                partner_type="ECOMMERCE",
                country="BR",
                sla_pickup_hours=72,
                sla_return_hours=24,
                penalty_pct=Decimal("1.50"),
                valid_from=date(2026, 1, 1),
                is_active=True,
                created_at=now,
            )
        )
        counts["sla"] += 1

    if not db.query(PartnerStatusHistory).filter(PartnerStatusHistory.partner_id == demo_pid).first():
        db.add(
            PartnerStatusHistory(
                id=new_id(),
                partner_id=demo_pid,
                partner_type="ECOMMERCE",
                from_status="DRAFT",
                to_status="ACTIVE",
                reason="Ativação seed OPS",
                changed_by="usr-admin-ops",
                changed_at=now,
            )
        )
        counts["status_history"] += 1

    wh_id = "wh-endpoint-demo-001"
    if not db.get(PartnerWebhookEndpoint, wh_id):
        db.add(
            PartnerWebhookEndpoint(
                id=wh_id,
                partner_id=demo_pid,
                partner_type="ECOMMERCE",
                url="https://hooks.demo-ops.example/v1/events",
                secret_hash=hash_secret("demo-webhook-secret"),
                secret_key="demo-webhook-secret",
                events_json='["order.created","order.updated"]',
                active=True,
                created_at=now,
                updated_at=now,
            )
        )
    if not db.query(PartnerWebhookDelivery).filter(PartnerWebhookDelivery.id == "wd-demo-001").first():
        db.add(
            PartnerWebhookDelivery(
                id="wd-demo-001",
                endpoint_id=wh_id,
                event_id="evt-demo-001",
                event_type="order.created",
                status="DELIVERED",
                http_status=200,
                attempt_count=1,
                delivered_at=now,
                created_at=now,
            )
        )
        db.add(
            PartnerWebhookDelivery(
                id="wd-demo-002",
                endpoint_id=wh_id,
                event_id="evt-demo-002",
                event_type="order.updated",
                status="FAILED",
                http_status=503,
                attempt_count=3,
                last_error="upstream timeout",
                created_at=now,
            )
        )
        counts["webhook_deliveries"] += 2

    if not db.query(PartnerIntegrationHealth).filter(PartnerIntegrationHealth.partner_id == demo_pid).first():
        db.add(
            PartnerIntegrationHealth(
                partner_id=demo_pid,
                partner_type="ECOMMERCE",
                endpoint_url="https://hooks.demo-ops.example/v1/events",
                status="UP",
                latency_ms=38,
                http_status=200,
                checked_at=now,
            )
        )
        counts["integration_health"] += 1

    if not db.query(PartnerOrderEventOutbox).filter(PartnerOrderEventOutbox.id == "outbox-demo-001").first():
        db.add(
            PartnerOrderEventOutbox(
                id="outbox-demo-001",
                partner_id=demo_pid,
                order_id="ord-demo-001",
                event_type="ORDER_CREATED",
                payload_json={"order_id": "ord-demo-001"},
                status="PENDING",
                attempt_count=0,
                created_at=now,
                updated_at=now,
            )
        )
        counts["outbox"] += 1

    if not db.get(PartnerB2bInvoice, "inv-demo-001"):
        db.add(
            PartnerB2bInvoice(
                id="inv-demo-001",
                cycle_id="cycle-demo-001",
                partner_id=demo_pid,
                invoice_number="NF-2026-00042",
                amount_cents=45000,
                tax_cents=8100,
                status="ISSUED",
                due_date=date(2026, 5, 10),
                taker_name="Partner Demo OPS",
                taker_email="ops-demo@ellanlab.com",
                issued_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        counts["invoices"] += 1

    if not db.query(PartnerBillingLineItem).filter(PartnerBillingLineItem.cycle_id == "cycle-demo-001").first():
        db.add(
            PartnerBillingLineItem(
                cycle_id="cycle-demo-001",
                partner_id=demo_pid,
                line_type="BASE_FEE",
                description="Mensalidade abril",
                unit_price_cents=9900,
                total_cents=9900,
            )
        )
        db.add(
            PartnerBillingLineItem(
                cycle_id="cycle-demo-001",
                partner_id=demo_pid,
                line_type="DELIVERY_FEE",
                description="Entregas locker",
                quantity=Decimal("120"),
                unit_price_cents=150,
                total_cents=18000,
            )
        )
        counts["line_items"] += 2

    if not db.get(PartnerCreditNote, "cn-demo-001"):
        db.add(
            PartnerCreditNote(
                id="cn-demo-001",
                partner_id=demo_pid,
                cycle_id="cycle-demo-001",
                reason_code="SLA_BREACH",
                description="Crédito por SLA pickup",
                amount_cents=2500,
                status="APPROVED",
                approved_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        counts["credit_notes"] += 1

    if not db.get(PartnerPaymentHold, "hold-demo-001"):
        db.add(
            PartnerPaymentHold(
                id="hold-demo-001",
                partner_id=demo_pid,
                invoice_id="inv-demo-001",
                hold_amount_cents=15000,
                status="HELD",
                created_at=now,
            )
        )
        counts["payment_holds"] += 1

    if not db.query(PartnerCommissionStructure).filter(PartnerCommissionStructure.partner_id == demo_pid).first():
        db.add(
            PartnerCommissionStructure(
                id=new_id(),
                partner_id=demo_pid,
                commission_percentage=Decimal("15.00"),
                revenue_threshold_cents=100000,
                effective_from=date(2026, 1, 1),
            )
        )
        counts["commissions"] += 1

    db.flush()
    ensure_onboarding(db, demo_pid, "ECOMMERCE")

    if not db.get(TenantFiscalConfig, "tenant-demo"):
        db.add(
            TenantFiscalConfig(
                tenant_id="tenant-demo",
                cnpj="12.345.678/0001-90",
                razao_social="Ellan Lab Demo Tenant",
                ie="123456789",
                regime="SIMPLES",
                crt="1",
                is_active=True,
                created_at=now,
                brand_config={
                    "logo_url": None,
                    "accent_color": "#38A169",
                    "company_name": "Ellan Demo",
                    "custom_domain": "demo.ellanlab.local",
                    "primary_color": "#1A365D",
                    "support_email": "suporte@ellanlab.com",
                    "support_phone": None,
                    "secondary_color": "#2D3748",
                },
            )
        )
        counts["tenants"] += 1

    if not db.query(CustomDomain).filter(CustomDomain.domain == "ops.demo.ellanlab.local").first():
        db.add(
            CustomDomain(
                id=new_id(),
                tenant_id="tenant-demo",
                domain="ops.demo.ellanlab.local",
                verified=True,
                created_at=now,
                verified_at=now,
            )
        )
        counts["domains"] += 1

    ec = db.query(EcommercePartner).filter(EcommercePartner.code == "DEMO-EC").first()
    if ec and not db.query(TenantPartnerLink).filter(TenantPartnerLink.tenant_id == "tenant-demo", TenantPartnerLink.partner_id == ec.id).first():
        db.add(
            TenantPartnerLink(
                id=new_id(),
                tenant_id="tenant-demo",
                partner_id=ec.id,
                partner_type="ECOMMERCE",
                is_default=True,
                created_at=now,
            )
        )
        counts["tenant_links"] += 1

    from app.models.partner_ecosystem import PartnerEcosystemPlayer
    from app.services.partner_ecosystem_professional_service import seed_professional_ecosystem
    from app.services.partner_ecosystem_service import (
        seed_demo_links,
        seed_priority_partner_records,
    )

    pro = seed_professional_ecosystem(db)
    counts["player_capabilities"] = pro.get("player_capabilities", 0)
    counts["player_relations"] = pro.get("player_relations", 0)
    counts["market_presence"] = pro.get("market_presence", 0)

    priority = seed_priority_partner_records(db)
    counts["ecommerce"] += priority["ecommerce"]
    counts["logistics"] += priority["logistics"]
    counts["ecosystem_players"] = db.query(PartnerEcosystemPlayer).count()
    counts["ecosystem_links"] = priority["ecosystem_links"] + seed_demo_links(db, demo_pid)

    from app.services.partner_capability_webhook_service import mirror_webhooks_from_capabilities

    wh = mirror_webhooks_from_capabilities(db)
    counts["capability_webhooks"] = wh.get("total", 0)
    counts["capability_webhooks_mirrored"] = wh.get("mirrored_from_marketplace", 0)

    counts["security"] = seed_security_domain(db)

    db.commit()
    return counts
