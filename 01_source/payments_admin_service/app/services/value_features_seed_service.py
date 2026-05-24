from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.value_features import (
    PaymentIntegrationIncident,
    PaymentIntegrationMilestone,
    PaymentPlayerCompliance,
    PaymentRoutingRule,
    PaymentSettlementCorridor,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def upsert_value_features(db: Session) -> dict[str, int]:
    counts = {
        "milestones": 0,
        "corridors": 0,
        "compliance": 0,
        "routing_rules": 0,
        "incidents": 0,
    }

    milestones = [
        ("INPOST", "SANDBOX", "API locker events + webhook HMAC", "DONE", "platform-integrations"),
        ("INPOST", "CERTIFICATION", "Certificação PCI SAQ-A totem", "DONE", "security"),
        ("INPOST", "PRODUCTION", "Go-live BR rede Magalu", "IN_PROGRESS", "platform-integrations"),
        ("MAGALU", "PILOT", "Split settlement marketplace", "IN_PROGRESS", "finance"),
        ("MERCADOLIVRE", "PRODUCTION", "Mercado Pago settlement LATAM", "DONE", "finance"),
        ("MERCADOPAGO", "CERTIFICATION", "OAuth + split rules BR", "DONE", "finance"),
        ("WORTEN", "PILOT", "CTT × InPost PT corridor", "IN_PROGRESS", "ops-pt"),
        ("EL_CORTE_INGLES", "DISCOVERY", "Correos + Amazon ES handoff", "PLANNED", "ops-es"),
        ("CAINIAO", "SANDBOX", "Cross-border CN→BR labels", "IN_PROGRESS", "logistics"),
        ("IFOOD", "DISCOVERY", "Food locker payment totem", "PLANNED", "food-innovation"),
    ]
    for player, phase, title, status, owner in milestones:
        exists = (
            db.query(PaymentIntegrationMilestone)
            .filter(
                PaymentIntegrationMilestone.player_code == player,
                PaymentIntegrationMilestone.title == title,
            )
            .first()
        )
        if exists:
            continue
        blockers = ["Aguardando credenciais sandbox"] if status == "BLOCKED" else []
        db.add(
            PaymentIntegrationMilestone(
                id=new_id(),
                player_code=player,
                phase=phase,
                title=title,
                status=status,
                target_date=date.today() + timedelta(days=30),
                completed_at=_utcnow() if status == "DONE" else None,
                owner_team=owner,
                blockers_json=blockers,
            )
        )
        counts["milestones"] += 1

    corridors = [
        ("BR-PT-BRL-EUR", "BR", "PT", "MAGALU", "CTT", "BRL", "EUR", "MONEY_CAMBIO", 85, 3),
        ("BR-BR-PIX-SETTLE", "BR", "BR", "MERCADOLIVRE", "MERCADOPAGO", "BRL", "BRL", None, 25, 1),
        ("US-BR-USD-BRL", "US", "BR", "AMAZON_US", "STRIPE_CONNECT", "USD", "BRL", "MONEY_CAMBIO", 120, 5),
        ("EU-ES-EUR-EUR", "ES", "ES", "EL_CORTE_INGLES", "AMAZON_ES", "EUR", "EUR", None, 15, 2),
        ("CN-BR-USD-BRL", "CN", "BR", "CAINIAO", "MELHOR_ENVIO", "USD", "BRL", "MONEY_CAMBIO", 95, 4),
        ("GB-GB-GBP-GBP", "GB", "GB", "INPOST", "STRIPE_CONNECT", "GBP", "GBP", None, 20, 1),
    ]
    for code, oc, dc, src, settle, sc, stc, fx, fee, delay in corridors:
        if db.query(PaymentSettlementCorridor).filter(PaymentSettlementCorridor.corridor_code == code).first():
            continue
        db.add(
            PaymentSettlementCorridor(
                id=new_id(),
                corridor_code=code,
                origin_country=oc,
                destination_country=dc,
                source_player_code=src,
                settlement_player_code=settle,
                source_currency=sc,
                settlement_currency=stc,
                fx_provider_code=fx,
                fee_basis_points=fee,
                settlement_delay_days=delay,
            )
        )
        counts["corridors"] += 1

    compliance_rows = [
        ("INPOST", "BR", "LGPD", "ENHANCED", "SAQ_A", False, "APPROVED", "LOW"),
        ("INPOST", "PL", "GDPR", "STANDARD", "SAQ_A", True, "APPROVED", "LOW"),
        ("MERCADOPAGO", "BR", "BACEN_PIX", "ENHANCED", "LEVEL_1", False, "APPROVED", "LOW"),
        ("STRIPE_CONNECT", "US", "PCI_DSS", "STANDARD", "LEVEL_1", False, "APPROVED", "LOW"),
        ("STRIPE_CONNECT", "EU", "GDPR", "STANDARD", "LEVEL_1", True, "APPROVED", "LOW"),
        ("MAGALU", "BR", "LGPD", "STANDARD", "SAQ_A", False, "APPROVED", "MEDIUM"),
        ("CAINIAO", "BR", "LGPD", "STANDARD", "SAQ_A", False, "PENDING", "HIGH"),
        ("IFOOD", "BR", "LGPD", "BASIC", "SAQ_A", False, "PENDING", "MEDIUM"),
    ]
    for player, country, framework, kyc, pci, gdpr, audit, risk in compliance_rows:
        exists = (
            db.query(PaymentPlayerCompliance)
            .filter(
                PaymentPlayerCompliance.player_code == player,
                PaymentPlayerCompliance.country_code == country,
                PaymentPlayerCompliance.regulatory_framework == framework,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            PaymentPlayerCompliance(
                id=new_id(),
                player_code=player,
                country_code=country,
                regulatory_framework=framework,
                kyc_level=kyc,
                pci_scope=pci,
                gdpr_ready=gdpr,
                audit_status=audit,
                last_audit_at=date.today() - timedelta(days=90) if audit == "APPROVED" else None,
                risk_tier=risk,
            )
        )
        counts["compliance"] += 1

    rules = [
        ("BR-PIX-MARKETPLACE", "BR", "PIX", "MARKETPLACE", "MERCADOPAGO", "STRIPE_CONNECT", 10, "PIX LATAM via Mercado Pago"),
        ("BR-CARD-LOCKER", "BR", "CREDIT_CARD", "LOCKER", "STRIPE_CONNECT", "MERCADOPAGO", 20, "Totem locker BR"),
        ("BR-BOLETO-ECOM", "BR", "BOLETO", "ECOMMERCE", "MERCADOPAGO", None, 30, "Boleto e-commerce"),
        ("PT-MBWAY-LOCKER", "PT", "MBWAY", "LOCKER", "CTT", "STRIPE_CONNECT", 10, "PT lockers Worten"),
        ("ES-CARD-MARKETPLACE", "ES", "CREDIT_CARD", "MARKETPLACE", "AMAZON_ES", "STRIPE_CONNECT", 10, "ECI + Amazon ES"),
        ("US-CARD-LOCKER", "US", "CREDIT_CARD", "LOCKER", "STRIPE_CONNECT", None, 10, "US access point"),
        ("GLOBAL-WALLET-CROSS", None, "DIGITAL_WALLET", None, "STRIPE_CONNECT", "ADYEN_MARKETPLACE", 50, "Cross-border wallet fallback"),
    ]
    for code, country, method, channel, primary, fallback, prio, rationale in rules:
        if db.query(PaymentRoutingRule).filter(PaymentRoutingRule.rule_code == code).first():
            continue
        db.add(
            PaymentRoutingRule(
                id=new_id(),
                rule_code=code,
                country_code=country or "XX",
                payment_method=method,
                sales_channel=channel,
                primary_player_code=primary,
                fallback_player_code=fallback,
                priority=prio,
                rationale=rationale,
            )
        )
        counts["routing_rules"] += 1

    if not db.query(PaymentIntegrationIncident).first():
        db.add(
            PaymentIntegrationIncident(
                id=new_id(),
                player_code="CAINIAO",
                severity="MEDIUM",
                incident_type="WEBHOOK_LATENCY",
                title="Latência webhook tracking CN→BR",
                status="OPEN",
                started_at=_utcnow() - timedelta(hours=6),
                impact_pct=12.5,
                affected_orders_estimate=340,
                root_cause="Timeout upstream Cainiao API",
            )
        )
        db.add(
            PaymentIntegrationIncident(
                id=new_id(),
                player_code="MELHOR_ENVIO",
                severity="LOW",
                incident_type="RATE_LIMIT",
                title="Rate limit labels API",
                status="RESOLVED",
                started_at=_utcnow() - timedelta(days=2),
                resolved_at=_utcnow() - timedelta(days=1),
                impact_pct=2.0,
                affected_orders_estimate=45,
            )
        )
        counts["incidents"] = 2

    db.commit()
    return counts
