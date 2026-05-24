from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.data.payment_domain_registry_catalog import PAYMENT_DOMAIN_REGISTRY
from app.models.domain_hub import (
    PaymentCrossDomainEvent,
    PaymentDomainObligation,
    PaymentDomainRegistry,
    PaymentExternalReference,
)
from app.models.cross_domain import PaymentOrderContext
from app.models.payments import Payment, PaymentSplit, PaymentTransaction
from app.schemas.domain_hub import (
    CrossDomainGapsOut,
    DomainGapItem,
    Order360DomainSection,
    PaymentOrder360Out,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def upsert_domain_registry(db: Session) -> int:
    n = 0
    for row in PAYMENT_DOMAIN_REGISTRY:
        if db.get(PaymentDomainRegistry, row["code"]):
            continue
        db.add(PaymentDomainRegistry(**row))
        n += 1
    db.commit()
    return n


def list_domain_registry(db: Session) -> list[PaymentDomainRegistry]:
    return (
        db.query(PaymentDomainRegistry)
        .filter(PaymentDomainRegistry.is_active.is_(True))
        .order_by(PaymentDomainRegistry.sort_order)
        .all()
    )


def list_external_references(
    db: Session,
    *,
    order_id: str | None = None,
    external_domain: str | None = None,
    limit: int = 200,
) -> list[PaymentExternalReference]:
    q = db.query(PaymentExternalReference)
    if order_id:
        q = q.filter(PaymentExternalReference.order_id == order_id)
    if external_domain:
        q = q.filter(PaymentExternalReference.external_domain == external_domain.upper())
    return q.order_by(PaymentExternalReference.external_domain).limit(limit).all()


def create_external_reference(db: Session, body) -> PaymentExternalReference:
    row = PaymentExternalReference(
        id=new_id(),
        order_id=body.order_id,
        payment_entity_type=body.payment_entity_type.upper(),
        payment_entity_id=body.payment_entity_id,
        external_domain=body.external_domain.upper(),
        external_entity_type=body.external_entity_type.upper(),
        external_entity_id=body.external_entity_id,
        link_role=body.link_role.upper(),
        sync_status=body.sync_status.upper(),
        last_synced_at=_utcnow(),
        metadata_json=body.metadata_json,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_external_reference(db: Session, ref_id: str) -> bool:
    row = db.get(PaymentExternalReference, ref_id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def list_obligations(
    db: Session,
    *,
    order_id: str | None = None,
    status: str | None = None,
    blocking_only: bool = False,
    limit: int = 200,
) -> list[PaymentDomainObligation]:
    q = db.query(PaymentDomainObligation)
    if order_id:
        q = q.filter(PaymentDomainObligation.order_id == order_id)
    if status:
        q = q.filter(PaymentDomainObligation.status == status.upper())
    if blocking_only:
        q = q.filter(PaymentDomainObligation.blocking_payment.is_(True))
    return q.order_by(PaymentDomainObligation.priority, PaymentDomainObligation.domain_code).limit(limit).all()


def create_obligation(db: Session, body) -> PaymentDomainObligation:
    row = PaymentDomainObligation(
        id=new_id(),
        order_id=body.order_id,
        domain_code=body.domain_code.upper(),
        obligation_type=body.obligation_type.upper(),
        status=body.status.upper(),
        priority=body.priority,
        blocking_payment=body.blocking_payment,
        due_at=body.due_at,
        external_ref_id=body.external_ref_id,
        notes=body.notes,
        metadata_json=body.metadata_json,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_obligation(db: Session, obligation_id: str, body) -> PaymentDomainObligation | None:
    row = db.get(PaymentDomainObligation, obligation_id)
    if not row:
        return None
    data = body.model_dump(exclude_unset=True)
    if data.get("status"):
        data["status"] = data["status"].upper()
        if data["status"] in ("DONE", "WAIVED") and not data.get("resolved_at"):
            data["resolved_at"] = _utcnow()
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def list_cross_domain_events(
    db: Session,
    *,
    order_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[PaymentCrossDomainEvent]:
    q = db.query(PaymentCrossDomainEvent)
    if order_id:
        q = q.filter(PaymentCrossDomainEvent.order_id == order_id)
    if status:
        q = q.filter(PaymentCrossDomainEvent.status == status.upper())
    return q.order_by(PaymentCrossDomainEvent.created_at.desc()).limit(limit).all()


def publish_cross_domain_event(
    db: Session,
    *,
    order_id: str | None,
    event_type: str,
    target_domains: list[str],
    payload: dict,
) -> PaymentCrossDomainEvent:
    row = PaymentCrossDomainEvent(
        id=new_id(),
        order_id=order_id,
        event_type=event_type.upper(),
        target_domains_json=[d.upper() for d in target_domains],
        payload_json=payload,
        status="PENDING",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def mark_event_published(db: Session, event_id: str) -> PaymentCrossDomainEvent | None:
    row = db.get(PaymentCrossDomainEvent, event_id)
    if not row:
        return None
    row.status = "PUBLISHED"
    row.published_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def scan_cross_domain_gaps(db: Session, *, limit: int = 50) -> CrossDomainGapsOut:
    gaps: list[DomainGapItem] = []
    contexts = db.query(PaymentOrderContext).limit(limit).all()

    for ctx in contexts:
        oid = ctx.order_id
        refs = list_external_references(db, order_id=oid)
        ref_domains = {r.external_domain for r in refs}

        if not db.query(PaymentTransaction).filter(PaymentTransaction.order_id == oid).first():
            gaps.append(
                DomainGapItem(
                    order_id=oid,
                    gap_type="MISSING_TRANSACTION",
                    domain_code="PAYMENT",
                    message="Pedido com contexto mas sem payment_transaction",
                    severity="HIGH",
                )
            )

        expected: list[tuple[str, str, bool]] = []
        if ctx.marketplace_partner_id:
            expected.append(("MARKETPLACE", "SELLER_ORDER", False))
        if ctx.locker_id:
            expected.append(("ORDER_PICKUP", "SHIPMENT", False))
            expected.append(("RUNTIME", "LOCKER_SLOT", False))
        if ctx.total_amount_cents > 0:
            expected.append(("FISCAL", "FISCAL_DOCUMENT", True))
            expected.append(("FINANCE", "SETTLEMENT_LINE", False))
        if ctx.currency != "BRL":
            expected.append(("MONEY_CAMBIO", "FX_QUOTE", False))

        for domain, entity_type, blocking in expected:
            if domain not in ref_domains:
                gaps.append(
                    DomainGapItem(
                        order_id=oid,
                        gap_type="MISSING_EXTERNAL_REF",
                        domain_code=domain,
                        message=f"Sem vínculo {domain}/{entity_type}",
                        severity="CRITICAL" if blocking else "MEDIUM",
                    )
                )

        blocking_obs = list_obligations(db, order_id=oid, status="PENDING", blocking_only=True)
        for ob in blocking_obs:
            if ob.status == "PENDING":
                gaps.append(
                    DomainGapItem(
                        order_id=oid,
                        gap_type="BLOCKING_OBLIGATION",
                        domain_code=ob.domain_code,
                        message=f"{ob.obligation_type} pendente",
                        severity="CRITICAL",
                    )
                )

    return CrossDomainGapsOut(items=gaps, total=len(gaps))


def build_order_360(db: Session, order_id: str) -> PaymentOrder360Out | None:
    from app.schemas.domain_hub import PaymentDomainObligationOut, PaymentExternalReferenceOut

    ctx = db.query(PaymentOrderContext).filter(PaymentOrderContext.order_id == order_id).first()
    txs = db.query(PaymentTransaction).filter(PaymentTransaction.order_id == order_id).all()
    splits = db.query(PaymentSplit).filter(PaymentSplit.order_id == order_id).all()
    pays = db.query(Payment).filter(Payment.order_id == order_id).all()
    refs = list_external_references(db, order_id=order_id)
    if not ctx and not txs and not refs:
        return None
    obligations = list_obligations(db, order_id=order_id)
    events_pending = (
        db.query(PaymentCrossDomainEvent)
        .filter(
            PaymentCrossDomainEvent.order_id == order_id,
            PaymentCrossDomainEvent.status == "PENDING",
        )
        .count()
    )

    registry = list_domain_registry(db) or []
    refs_by_domain: dict[str, list] = {r.code: [] for r in registry}
    for ref in refs:
        refs_by_domain.setdefault(ref.external_domain, []).append(
            PaymentExternalReferenceOut.model_validate(ref)
        )

    obs_by_domain: dict[str, list] = {r.code: [] for r in registry}
    pending = 0
    blocking = 0
    for ob in obligations:
        obs_by_domain.setdefault(ob.domain_code, []).append(
            PaymentDomainObligationOut.model_validate(ob)
        )
        if ob.status == "PENDING":
            pending += 1
            if ob.blocking_payment:
                blocking += 1

    domains = [
        Order360DomainSection(
            domain_code=r.code,
            domain_name=r.name,
            ops_path=r.ops_base_path,
            references=refs_by_domain.get(r.code, []),
            obligations=obs_by_domain.get(r.code, []),
        )
        for r in registry
        if refs_by_domain.get(r.code) or obs_by_domain.get(r.code)
    ]

    return PaymentOrder360Out(
        order_id=order_id,
        payment_summary={
            "has_context": ctx is not None,
            "context_status": ctx.status if ctx else None,
            "total_amount_cents": ctx.total_amount_cents if ctx else 0,
            "currency": ctx.currency if ctx else None,
            "transactions": len(txs),
            "splits": len(splits),
            "payments": len(pays),
            "locker_network": ctx.locker_network_code if ctx else None,
        },
        domains=domains,
        pending_obligations=pending,
        blocking_obligations=blocking,
        external_refs_total=len(refs),
        cross_domain_events_pending=events_pending,
    )
