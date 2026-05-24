from __future__ import annotations

import json
import time
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.cross_domain import (
    PartnerPaymentHold,
    PaymentContextPlayerLink,
    PaymentOrderContext,
    PaymentReconciliationBatch,
    SavedPaymentMethod,
    WebhookDelivery,
)
from app.models.payments import (
    GatewayEvent,
    Payment,
    PaymentInstruction,
    PaymentSplit,
    PaymentTransaction,
    WebhookEndpoint,
)
from app.services.crypto_util import hash_secret, new_id
from app.services.ecosystem_seed_service import upsert_ecosystem_catalog
from app.services.domain_hub_seed_service import upsert_domain_hub_demo
from app.services.value_features_seed_service import upsert_value_features


def run_seed(db: Session) -> dict[str, int]:
    counts = {
        "transactions": 0,
        "instructions": 0,
        "splits": 0,
        "payments": 0,
        "webhooks": 0,
        "gateway_events": 0,
        "ecosystem_players": 0,
        "ecosystem_segments": 0,
        "country_coverage": 0,
        "player_integrations": 0,
        "integration_milestones": 0,
        "settlement_corridors": 0,
        "player_compliance": 0,
        "routing_rules": 0,
        "integration_incidents": 0,
        "domain_registry": 0,
        "external_references": 0,
        "domain_obligations": 0,
        "cross_domain_events": 0,
        "player_relations": 0,
        "order_context": 0,
        "player_links": 0,
        "reconciliation_batches": 0,
        "webhook_deliveries": 0,
        "partner_holds": 0,
        "saved_methods": 0,
    }
    epoch = int(time.time())
    demo_order = "ORD-DEMO-INPOST-001"

    eco = upsert_ecosystem_catalog(db)
    counts["ecosystem_players"] = eco["players_created"] + eco["players_updated"]
    counts["ecosystem_segments"] = eco.get("segments", 0)
    counts["country_coverage"] = eco.get("country_coverage", 0)
    counts["player_integrations"] = eco.get("integrations", 0)
    counts["player_relations"] = eco["relations_created"]

    vf = upsert_value_features(db)
    counts["integration_milestones"] = vf["milestones"]
    counts["settlement_corridors"] = vf["corridors"]
    counts["player_compliance"] = vf["compliance"]
    counts["routing_rules"] = vf["routing_rules"]
    counts["integration_incidents"] = vf["incidents"]

    dh = upsert_domain_hub_demo(db)
    counts["domain_registry"] = dh["domain_registry"]
    counts["external_references"] = dh["external_refs"]
    counts["domain_obligations"] = dh["obligations"]
    counts["cross_domain_events"] = dh["events"]

    if not db.get(PaymentTransaction, "pay-tx-demo-001"):
        db.add(
            PaymentTransaction(
                id="pay-tx-demo-001",
                order_id=demo_order,
                gateway="STRIPE",
                gateway_transaction_id="ch_demo_inpost_br",
                amount_cents=1590,
                currency="BRL",
                payment_method="PIX",
                status="APPROVED",
                reconciliation_status="PENDING",
                reconciliation_batch_id="RECON-BR-2026-05",
                gateway_fee_cents=13,
                net_amount_cents=1577,
            )
        )
        counts["transactions"] += 1

    if not db.get(PaymentInstruction, "pay-inst-demo-001"):
        db.add(
            PaymentInstruction(
                id="pay-inst-demo-001",
                order_id=demo_order,
                instruction_type="PIX_QR",
                amount_cents=1590,
                currency="BRL",
                status="CAPTURED",
                provider_name="Mercado Pago",
                qr_code_text="00020126580014BR.GOV.BCB.PIX",
            )
        )
        counts["instructions"] += 1

    if not db.get(PaymentSplit, "pay-split-demo-001"):
        db.add(
            PaymentSplit(
                id="pay-split-demo-001",
                order_id=demo_order,
                recipient_type="MARKETPLACE",
                recipient_id="partner-magalu-br",
                amount_cents=120,
                percentage=7.55,
                status="PENDING",
            )
        )
        counts["splits"] += 1

    if not db.get(Payment, "pay-ledger-demo-001"):
        db.add(
            Payment(
                id="pay-ledger-demo-001",
                order_id=demo_order,
                provider="inpost",
                method="card",
                status="confirmed",
                amount_cents=1590,
                currency="EUR",
                created_at=epoch - 7200,
                confirmed_at=epoch - 3600,
                raw_json={"carrier": "InPost", "marketplace": "Magalu"},
            )
        )
        counts["payments"] += 1

    if not db.get(WebhookEndpoint, "wh-demo-magalu-001"):
        db.add(
            WebhookEndpoint(
                id="wh-demo-magalu-001",
                partner_type="MARKETPLACE",
                partner_id="partner-magalu-br",
                url="https://hooks.magalu.example/ellan/payments",
                events='["payment.completed","payment.refunded"]',
                secret_ref=hash_secret("demo-magalu-wh"),
                active=True,
            )
        )
        counts["webhooks"] += 1

    if not db.get(WebhookEndpoint, "wh-demo-dpd-001"):
        db.add(
            WebhookEndpoint(
                id="wh-demo-dpd-001",
                partner_type="CARRIER",
                partner_id="carrier-dpd-de",
                url="https://hooks.dpd.example/locker-events",
                events='["payment.*","order.paid"]',
                secret_ref=hash_secret("demo-dpd-wh"),
                active=True,
            )
        )
        counts["webhooks"] += 1

    if not db.get(GatewayEvent, "gw-ev-demo-001"):
        db.add(
            GatewayEvent(
                id="gw-ev-demo-001",
                gateway_id="payment_gateway",
                region="BR",
                locker_id="LOCKER-DEMO-01",
                porta=3,
                event_type="PAYMENT_APPROVED",
                created_at=epoch,
                order_id=demo_order,
                request_id=new_id(),
                payload_json={"psp": "STRIPE-BR", "method": "PIX"},
            )
        )
        counts["gateway_events"] += 1

    if not db.query(PaymentOrderContext).filter(PaymentOrderContext.order_id == demo_order).first():
        ctx_id = "poc-demo-inpost-001"
        db.add(
            PaymentOrderContext(
                id=ctx_id,
                order_id=demo_order,
                tenant_id="tenant-demo-br",
                primary_transaction_id="pay-tx-demo-001",
                locker_id="LOCKER-DEMO-01",
                region_code="BR",
                sales_channel="MARKETPLACE_B2C",
                marketplace_partner_id="partner-magalu-br",
                carrier_partner_id="carrier-dpd-de",
                locker_network_code="INPOST",
                status="OPEN",
                total_amount_cents=1590,
                currency="BRL",
                metadata_json={
                    "collection_point": "Ponto Magalu",
                    "aggregator": "Melhor Envio",
                },
            )
        )
        counts["order_context"] += 1
        for role, pcode, amt in [
            ("MARKETPLACE", "MAGALU", 120),
            ("COLLECTION_POINT", "PONTO_MAGALU", 0),
            ("CARRIER", "CORREIOS", 80),
            ("CARRIER", "DPD", 0),
            ("LOCKER_NETWORK", "INPOST", 1390),
            ("LOGISTICS_PLATFORM", "MELHOR_ENVIO", 0),
        ]:
            db.add(
                PaymentContextPlayerLink(
                    id=new_id(),
                    order_context_id=ctx_id,
                    player_code=pcode,
                    role=role,
                    amount_cents=amt if amt else None,
                )
            )
            counts["player_links"] += 1

    # Demo PT: Worten × CTT × InPost
    demo_pt = "ORD-DEMO-WORTEN-PT-001"
    if not db.query(PaymentOrderContext).filter(PaymentOrderContext.order_id == demo_pt).first():
        ctx_pt = "poc-demo-worten-pt"
        db.add(
            PaymentOrderContext(
                id=ctx_pt,
                order_id=demo_pt,
                tenant_id="tenant-demo-pt",
                locker_id="LOCKER-PT-LIS-01",
                region_code="PT",
                sales_channel="RETAIL_CC",
                marketplace_partner_id="partner-worten-pt",
                carrier_partner_id="carrier-ctt-pt",
                locker_network_code="INPOST",
                status="OPEN",
                total_amount_cents=2490,
                currency="EUR",
                metadata_json={"collection_point": "WORTEN_STORES", "fiscal_corridor": "PT-WORTEN-CC"},
            )
        )
        counts["order_context"] += 1
        for role, pcode in [
            ("MARKETPLACE", "WORTEN"),
            ("COLLECTION_POINT", "WORTEN_STORES"),
            ("CARRIER", "CTT"),
            ("LOCKER_NETWORK", "INPOST"),
        ]:
            db.add(
                PaymentContextPlayerLink(
                    id=new_id(),
                    order_context_id=ctx_pt,
                    player_code=pcode,
                    role=role,
                )
            )
            counts["player_links"] += 1

    # Demo ES: El Corte Inglés × Amazon ES × Correos
    demo_es = "ORD-DEMO-ECI-ES-001"
    if not db.query(PaymentOrderContext).filter(PaymentOrderContext.order_id == demo_es).first():
        ctx_es = "poc-demo-eci-es"
        db.add(
            PaymentOrderContext(
                id=ctx_es,
                order_id=demo_es,
                tenant_id="tenant-demo-es",
                locker_id="LOCKER-ES-MAD-01",
                region_code="ES",
                sales_channel="MARKETPLACE_B2C",
                marketplace_partner_id="partner-eci-es",
                carrier_partner_id="carrier-correos-es",
                locker_network_code="INPOST",
                status="OPEN",
                total_amount_cents=3200,
                currency="EUR",
                metadata_json={"collection_point": "ECI_COLLECTION", "fiscal_corridor": "ES-ECI-COLLECTION"},
            )
        )
        counts["order_context"] += 1
        for role, pcode in [
            ("MARKETPLACE", "EL_CORTE_INGLES"),
            ("COLLECTION_POINT", "ECI_COLLECTION"),
            ("MARKETPLACE", "AMAZON_ES"),
            ("CARRIER", "CORREOS_ES"),
            ("LOCKER_NETWORK", "INPOST"),
        ]:
            db.add(
                PaymentContextPlayerLink(
                    id=new_id(),
                    order_context_id=ctx_es,
                    player_code=pcode,
                    role=role,
                )
            )
            counts["player_links"] += 1

    if not db.query(PaymentReconciliationBatch).filter(
        PaymentReconciliationBatch.batch_code == "RECON-BR-2026-05"
    ).first():
        db.add(
            PaymentReconciliationBatch(
                id="prb-br-2026-05",
                batch_code="RECON-BR-2026-05",
                region_code="BR",
                gateway="STRIPE",
                period_start=date(2026, 5, 1),
                period_end=date(2026, 5, 31),
                status="OPEN",
                expected_count=1,
                matched_count=0,
                mismatch_count=0,
                total_amount_cents=1590,
                currency="BRL",
                notes="Lote demo BR — Magalu × InPost",
            )
        )
        counts["reconciliation_batches"] += 1

    if not db.get(WebhookDelivery, "whd-demo-001"):
        db.add(
            WebhookDelivery(
                id="whd-demo-001",
                endpoint_id="wh-demo-magalu-001",
                event_name="payment.completed",
                aggregate_type="order",
                aggregate_id=demo_order,
                payload_json=json.dumps({"order_id": demo_order, "status": "APPROVED"}),
                status="DELIVERED",
                attempt_count=1,
                last_status_code=200,
                delivered_at=datetime.now(timezone.utc),
            )
        )
        counts["webhook_deliveries"] += 1

    if not db.get(WebhookDelivery, "whd-demo-002"):
        db.add(
            WebhookDelivery(
                id="whd-demo-002",
                endpoint_id="wh-demo-dpd-001",
                event_name="payment.completed",
                aggregate_type="order",
                aggregate_id=demo_order,
                payload_json=json.dumps({"order_id": demo_order}),
                status="PENDING",
                attempt_count=2,
                last_status_code=502,
                last_response_body="upstream timeout",
            )
        )
        counts["webhook_deliveries"] += 1

    if not db.get(PartnerPaymentHold, "pph-demo-001"):
        db.add(
            PartnerPaymentHold(
                id="pph-demo-001",
                partner_id="partner-magalu-br",
                invoice_id="inv-magalu-2026-05",
                order_id=demo_order,
                hold_amount_cents=120,
                release_schedule="AFTER_15_DAYS",
                status="HELD",
            )
        )
        counts["partner_holds"] += 1

    if not db.get(SavedPaymentMethod, "spm-demo-001"):
        db.add(
            SavedPaymentMethod(
                id="spm-demo-001",
                user_id="user-demo-br",
                method_code="CREDIT_CARD",
                gateway_token="tok_demo_visa",
                last4="4242",
                card_brand="VISA",
                is_default=True,
                is_active=True,
            )
        )
        counts["saved_methods"] += 1

    db.commit()
    return counts
