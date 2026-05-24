from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.domain_hub import (
    PaymentCrossDomainEvent,
    PaymentDomainObligation,
    PaymentExternalReference,
)
from app.services.crypto_util import new_id
from app.services.domain_hub_service import upsert_domain_registry


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _seed_order_links(
    db: Session,
    order_id: str,
    links: list[tuple[str, str, str, str, str, str]],
) -> int:
    n = 0
    for pet, peid, domain, eet, eeid, role in links:
        exists = (
            db.query(PaymentExternalReference)
            .filter(
                PaymentExternalReference.payment_entity_type == pet,
                PaymentExternalReference.payment_entity_id == peid,
                PaymentExternalReference.external_domain == domain,
                PaymentExternalReference.external_entity_id == eeid,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            PaymentExternalReference(
                id=new_id(),
                order_id=order_id,
                payment_entity_type=pet,
                payment_entity_id=peid,
                external_domain=domain,
                external_entity_type=eet,
                external_entity_id=eeid,
                link_role=role,
                sync_status="LINKED",
                last_synced_at=_utcnow(),
                metadata_json={"seed": True},
            )
        )
        n += 1
    return n


def upsert_domain_hub_demo(db: Session) -> dict[str, int]:
    counts = {
        "domain_registry": upsert_domain_registry(db),
        "external_refs": 0,
        "obligations": 0,
        "events": 0,
    }

    br = "ORD-DEMO-INPOST-001"
    counts["external_refs"] += _seed_order_links(
        db,
        br,
        [
            ("ORDER", br, "ORDER_PICKUP", "SHIPMENT", "ship-br-inpost-001", "PRIMARY"),
            ("TRANSACTION", "pay-tx-demo-001", "PAYMENT_GATEWAY", "GATEWAY_SESSION", "gw-sess-stripe-br-01", "PRIMARY"),
            ("TRANSACTION", "pay-tx-demo-001", "FINANCE", "SETTLEMENT_LINE", "fin-settle-magalu-001", "PRIMARY"),
            ("ORDER", br, "MARKETPLACE", "SELLER_ORDER", "mkt-seller-magalu-8821", "PRIMARY"),
            ("ORDER", br, "FISCAL", "FISCAL_DOCUMENT", "nf-e-demo-44521", "PRIMARY"),
            ("ORDER", br, "MONEY_CAMBIO", "FX_QUOTE", "fx-brl-usd-demo-01", "REFERENCE"),
            ("ORDER", br, "PARTNERS", "PARTNER_CONTRACT", "partner-magalu-br", "PRIMARY"),
            ("SPLIT", "pay-split-demo-001", "MARKETPLACE", "COMMISSION", "mkt-comm-demo-001", "PRIMARY"),
        ],
    )

    pt = "ORD-DEMO-WORTEN-PT-001"
    counts["external_refs"] += _seed_order_links(
        db,
        pt,
        [
            ("ORDER", pt, "ORDER_PICKUP", "SHIPMENT", "ship-pt-worten-001", "PRIMARY"),
            ("ORDER", pt, "MARKETPLACE", "SELLER_ORDER", "mkt-worten-pt-991", "PRIMARY"),
            ("ORDER", pt, "FISCAL", "FISCAL_DOCUMENT", "nf-pt-demo-12001", "PRIMARY"),
            ("ORDER", pt, "MONEY_CAMBIO", "FX_QUOTE", "fx-eur-pt-demo-01", "REFERENCE"),
        ],
    )

    es = "ORD-DEMO-ECI-ES-001"
    counts["external_refs"] += _seed_order_links(
        db,
        es,
        [
            ("ORDER", es, "ORDER_PICKUP", "SHIPMENT", "ship-es-eci-001", "PRIMARY"),
            ("ORDER", es, "MARKETPLACE", "SELLER_ORDER", "mkt-eci-es-441", "PRIMARY"),
            ("ORDER", es, "FISCAL", "FISCAL_DOCUMENT", "nf-es-demo-7788", "PRIMARY"),
        ],
    )

    obligations_spec = [
        (br, "FISCAL", "EMIT_NFE_BEFORE_RELEASE", "DONE", False, None),
        (br, "FINANCE", "MARKETPLACE_HOLD_15D", "PENDING", True, "fin-settle-magalu-001"),
        (br, "MARKETPLACE", "CONFIRM_SELLER_PAYOUT", "PENDING", False, "mkt-seller-magalu-8821"),
        (br, "ORDER_PICKUP", "CONFIRM_PICKUP", "PENDING", False, "ship-br-inpost-001"),
        (br, "PAYMENT_GATEWAY", "CAPTURE_CONFIRMED", "DONE", False, "gw-sess-stripe-br-01"),
        (pt, "FISCAL", "EMIT_NFE_BEFORE_RELEASE", "PENDING", True, "nf-pt-demo-12001"),
        (pt, "MONEY_CAMBIO", "FX_LOCK_SETTLEMENT", "PENDING", False, "fx-eur-pt-demo-01"),
        (es, "FISCAL", "EMIT_NFE_BEFORE_RELEASE", "PENDING", True, "nf-es-demo-7788"),
    ]
    for oid, domain, ob_type, status, blocking, ext_ref in obligations_spec:
        exists = (
            db.query(PaymentDomainObligation)
            .filter(
                PaymentDomainObligation.order_id == oid,
                PaymentDomainObligation.domain_code == domain,
                PaymentDomainObligation.obligation_type == ob_type,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            PaymentDomainObligation(
                id=new_id(),
                order_id=oid,
                domain_code=domain,
                obligation_type=ob_type,
                status=status,
                priority=10 if blocking else 50,
                blocking_payment=blocking,
                due_at=_utcnow() + timedelta(days=2) if status == "PENDING" else None,
                resolved_at=_utcnow() if status == "DONE" else None,
                external_ref_id=ext_ref,
                notes=f"Obrigação demo {domain}",
            )
        )
        counts["obligations"] += 1

    if not db.query(PaymentCrossDomainEvent).first():
        for oid, etype, targets, payload in [
            (
                br,
                "PAYMENT_CAPTURED",
                ["FINANCE", "MARKETPLACE", "FISCAL"],
                {"order_id": br, "amount_cents": 1590},
            ),
            (
                br,
                "HOLD_CREATED",
                ["FINANCE"],
                {"partner_id": "partner-magalu-br", "hold_cents": 12000},
            ),
            (
                pt,
                "PAYMENT_CAPTURED",
                ["FISCAL", "MONEY_CAMBIO"],
                {"order_id": pt, "currency": "EUR"},
            ),
        ]:
            db.add(
                PaymentCrossDomainEvent(
                    id=new_id(),
                    order_id=oid,
                    event_type=etype,
                    target_domains_json=targets,
                    payload_json=payload,
                    status="PENDING",
                )
            )
            counts["events"] += 1

    db.commit()
    return counts
