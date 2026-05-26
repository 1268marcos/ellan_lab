from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.data.seller_operations_seed import NOTIFICATION_DEMO, ONBOARDING_TASK_TEMPLATE, SKU_MAP_DEMO
from app.models.marketplace import SellerProduct
from app.models.marketplace_extended import MarketplaceChannelPartner
from app.models.marketplace_seller_operations import (
    SellerChannelSkuMap,
    SellerFulfillmentPreference,
    SellerInventoryAllocation,
    SellerNotificationSubscription,
    SellerOnboardingTask,
    SellerPricingRule,
    SellerReturnPolicy,
)
from app.schemas.marketplace_seller_operations import (
    ChannelSkuMapCreateIn,
    FulfillmentPreferenceUpsertIn,
    InventoryAllocationUpsertIn,
    NotificationSubCreateIn,
    OnboardingTaskCompleteIn,
    PricingRuleCreateIn,
    ReturnPolicyCreateIn,
)
from app.services.crypto_util import new_id
from app.services.seller_service import get_seller_or_404


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _partner_codes(db: Session) -> dict[str, str]:
    return {p.id: p.code for p in db.query(MarketplaceChannelPartner).all()}


def seed_seller_operations(db: Session, seller_id: str = "mk-seller-demo-001") -> dict[str, int]:
    counts = {
        "onboarding": 0,
        "sku_maps": 0,
        "pricing_rules": 0,
        "return_policies": 0,
        "notifications": 0,
        "allocations": 0,
        "fulfillment": 0,
    }
    get_seller_or_404(db, seller_id)
    now = _utcnow()
    completed_codes = {"KYC_APPROVED", "PAYOUT_VERIFIED", "WEBHOOK_CONFIGURED", "LOCKER_NETWORK", "CHANNEL_MELI"}

    for spec in ONBOARDING_TASK_TEMPLATE:
        tid = f"mk-onb-{seller_id[-3:]}-{spec['task_code'].lower()}"
        if db.get(SellerOnboardingTask, tid):
            continue
        st = "COMPLETED" if spec["task_code"] in completed_codes else "PENDING"
        db.add(
            SellerOnboardingTask(
                id=tid,
                seller_id=seller_id,
                task_code=spec["task_code"],
                title=spec["title"],
                category=spec["category"],
                status=st,
                required=spec["required"],
                sort_order=spec["sort_order"],
                completed_at=now if st == "COMPLETED" else None,
                completed_by="seed" if st == "COMPLETED" else None,
            )
        )
        counts["onboarding"] += 1

    for mid, cpid, internal, channel, prod in SKU_MAP_DEMO:
        if not db.get(MarketplaceChannelPartner, cpid):
            continue
        if db.get(SellerChannelSkuMap, mid):
            continue
        db.add(
            SellerChannelSkuMap(
                id=mid,
                seller_id=seller_id,
                channel_partner_id=cpid,
                internal_sku=internal,
                channel_sku=channel,
                seller_product_id=prod,
                last_synced_at=now,
            )
        )
        counts["sku_maps"] += 1

    if not db.query(SellerPricingRule).filter(SellerPricingRule.seller_id == seller_id).first():
        db.add(
            SellerPricingRule(
                id="mk-price-floor",
                seller_id=seller_id,
                channel_partner_id=None,
                rule_type="MIN_PRICE",
                name="Piso global DEMO-001",
                min_price_cents=4500,
                currency="BRL",
                priority=10,
            )
        )
        db.add(
            SellerPricingRule(
                id="mk-price-meli",
                seller_id=seller_id,
                channel_partner_id="mcp-meli",
                rule_type="CHANNEL_MARKUP",
                name="Markup Mercado Livre",
                markup_pct=Decimal("3.50"),
                max_discount_pct=Decimal("15.00"),
                currency="BRL",
                priority=20,
            )
        )
        counts["pricing_rules"] = 2

    if not db.query(SellerReturnPolicy).filter(SellerReturnPolicy.seller_id == seller_id).first():
        db.add(
            SellerReturnPolicy(
                id="mk-ret-default",
                seller_id=seller_id,
                channel_partner_id=None,
                policy_code="DEFAULT_BR",
                return_window_days=7,
                restocking_fee_pct=Decimal("5.00"),
                accepts_locker_return=True,
                rma_required=True,
            )
        )
        db.add(
            SellerReturnPolicy(
                id="mk-ret-meli",
                seller_id=seller_id,
                channel_partner_id="mcp-meli",
                policy_code="MELI_FLEX",
                return_window_days=30,
                restocking_fee_pct=Decimal("0"),
                accepts_locker_return=True,
            )
        )
        counts["return_policies"] = 2

    for i, (evt, ch, dest) in enumerate(NOTIFICATION_DEMO):
        nid = f"mk-notif-{i}"
        if db.get(SellerNotificationSubscription, nid):
            continue
        db.add(
            SellerNotificationSubscription(
                id=nid,
                seller_id=seller_id,
                event_type=evt,
                channel=ch,
                destination=dest,
            )
        )
        counts["notifications"] += 1

    prod = db.get(SellerProduct, "mk-prod-demo-001")
    if prod:
        for aid, cpid, locker, alloc, res in [
            ("mk-alloc-meli", "mcp-meli", None, 15, 3),
            ("mk-alloc-magalu", "mcp-magalu", "PUDO-MAGALU-001", 10, 2),
        ]:
            if db.get(SellerInventoryAllocation, aid) or not db.get(MarketplaceChannelPartner, cpid):
                continue
            db.add(
                SellerInventoryAllocation(
                    id=aid,
                    seller_id=seller_id,
                    seller_product_id=prod.id,
                    channel_partner_id=cpid,
                    locker_id=locker,
                    allocated_qty=alloc,
                    reserved_qty=res,
                    available_qty=max(0, alloc - res),
                )
            )
            counts["allocations"] += 1

    if not db.query(SellerFulfillmentPreference).filter(SellerFulfillmentPreference.seller_id == seller_id).first():
        db.add(
            SellerFulfillmentPreference(
                id="mk-fulfill-pref",
                seller_id=seller_id,
                default_locker_id="LOCKER-DEMO-01",
                split_shipments_allowed=False,
                max_packages_per_order=2,
                prefer_nearest_locker=True,
                handoff_mode="LOCKER_FIRST",
                packaging_notes="Embalagem reforçada para locker.",
            )
        )
        counts["fulfillment"] = 1

    db.commit()
    return counts


def seller_operations_summary(db: Session, seller_id: str) -> dict:
    get_seller_or_404(db, seller_id)
    tasks = db.query(SellerOnboardingTask).filter(SellerOnboardingTask.seller_id == seller_id).all()
    required = [t for t in tasks if t.required]
    done = [t for t in required if t.status == "COMPLETED"]
    pct = round(100.0 * len(done) / len(required), 1) if required else 100.0
    pending = sum(1 for t in tasks if t.status != "COMPLETED")
    return {
        "seller_id": seller_id,
        "onboarding_progress_pct": pct,
        "onboarding_pending": pending,
        "sku_maps": db.query(SellerChannelSkuMap).filter(SellerChannelSkuMap.seller_id == seller_id).count(),
        "pricing_rules": db.query(SellerPricingRule).filter(SellerPricingRule.seller_id == seller_id).count(),
        "return_policies": db.query(SellerReturnPolicy).filter(SellerReturnPolicy.seller_id == seller_id).count(),
        "notification_subs": db.query(SellerNotificationSubscription)
        .filter(SellerNotificationSubscription.seller_id == seller_id)
        .count(),
        "inventory_allocations": db.query(SellerInventoryAllocation)
        .filter(SellerInventoryAllocation.seller_id == seller_id)
        .count(),
        "has_fulfillment_prefs": db.query(SellerFulfillmentPreference)
        .filter(SellerFulfillmentPreference.seller_id == seller_id)
        .first()
        is not None,
    }


def list_onboarding(db: Session, seller_id: str) -> dict:
    rows = (
        db.query(SellerOnboardingTask)
        .filter(SellerOnboardingTask.seller_id == seller_id)
        .order_by(SellerOnboardingTask.sort_order)
        .all()
    )
    required = [t for t in rows if t.required]
    done = [t for t in required if t.status == "COMPLETED"]
    pct = round(100.0 * len(done) / len(required), 1) if required else 100.0
    return {"tasks": rows, "total": len(rows), "completed_count": len(done), "progress_pct": pct}


def complete_onboarding_task(db: Session, task_id: str, body: OnboardingTaskCompleteIn) -> SellerOnboardingTask:
    row = db.get(SellerOnboardingTask, task_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="onboarding_task_not_found")
    row.status = "COMPLETED"
    row.completed_at = _utcnow()
    row.completed_by = body.completed_by
    if body.notes:
        row.notes = body.notes
    db.commit()
    db.refresh(row)
    return row


def list_sku_maps(db: Session, seller_id: str) -> list[dict]:
    codes = _partner_codes(db)
    rows = db.query(SellerChannelSkuMap).filter(SellerChannelSkuMap.seller_id == seller_id).all()
    return [
        {**{c.name: getattr(r, c.name) for c in r.__table__.columns}, "partner_code": codes.get(r.channel_partner_id)}
        for r in rows
    ]


def create_sku_map(db: Session, body: ChannelSkuMapCreateIn) -> SellerChannelSkuMap:
    get_seller_or_404(db, body.seller_id)
    if not db.get(MarketplaceChannelPartner, body.channel_partner_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="channel_partner_not_found")
    exists = (
        db.query(SellerChannelSkuMap)
        .filter(
            SellerChannelSkuMap.seller_id == body.seller_id,
            SellerChannelSkuMap.channel_partner_id == body.channel_partner_id,
            SellerChannelSkuMap.internal_sku == body.internal_sku,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="sku_map_exists")
    row = SellerChannelSkuMap(id=new_id(), created_at=_utcnow(), updated_at=_utcnow(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_pricing_rules(db: Session, seller_id: str) -> list[dict]:
    codes = _partner_codes(db)
    rows = (
        db.query(SellerPricingRule)
        .filter(SellerPricingRule.seller_id == seller_id)
        .order_by(SellerPricingRule.priority)
        .all()
    )
    return [
        {**{c.name: getattr(r, c.name) for c in r.__table__.columns}, "partner_code": codes.get(r.channel_partner_id)}
        for r in rows
    ]


def create_pricing_rule(db: Session, body: PricingRuleCreateIn) -> SellerPricingRule:
    get_seller_or_404(db, body.seller_id)
    if body.channel_partner_id and not db.get(MarketplaceChannelPartner, body.channel_partner_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="channel_partner_not_found")
    data = body.model_dump()
    if data.get("max_discount_pct") is not None:
        data["max_discount_pct"] = Decimal(str(data["max_discount_pct"]))
    if data.get("markup_pct") is not None:
        data["markup_pct"] = Decimal(str(data["markup_pct"]))
    row = SellerPricingRule(id=new_id(), **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def apply_pricing_preview(db: Session, seller_id: str, internal_sku: str, base_price_cents: int, channel_partner_id: str | None = None) -> dict:
    rules = (
        db.query(SellerPricingRule)
        .filter(SellerPricingRule.seller_id == seller_id, SellerPricingRule.active.is_(True))
        .order_by(SellerPricingRule.priority)
        .all()
    )
    price = base_price_cents
    applied: list[str] = []
    for rule in rules:
        if rule.channel_partner_id and rule.channel_partner_id != channel_partner_id:
            continue
        if rule.rule_type == "MIN_PRICE" and rule.min_price_cents and price < rule.min_price_cents:
            price = rule.min_price_cents
            applied.append(rule.name)
        elif rule.rule_type == "CHANNEL_MARKUP" and rule.markup_pct:
            price = int(round(price * (1 + float(rule.markup_pct) / 100)))
            applied.append(rule.name)
    return {
        "seller_id": seller_id,
        "internal_sku": internal_sku,
        "base_price_cents": base_price_cents,
        "final_price_cents": price,
        "rules_applied": applied,
    }


def list_return_policies(db: Session, seller_id: str) -> list[SellerReturnPolicy]:
    get_seller_or_404(db, seller_id)
    return db.query(SellerReturnPolicy).filter(SellerReturnPolicy.seller_id == seller_id).all()


def create_return_policy(db: Session, body: ReturnPolicyCreateIn) -> SellerReturnPolicy:
    get_seller_or_404(db, body.seller_id)
    exists = (
        db.query(SellerReturnPolicy)
        .filter(SellerReturnPolicy.seller_id == body.seller_id, SellerReturnPolicy.policy_code == body.policy_code)
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="return_policy_exists")
    data = body.model_dump()
    data["restocking_fee_pct"] = Decimal(str(data["restocking_fee_pct"]))
    row = SellerReturnPolicy(id=new_id(), **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_notifications(db: Session, seller_id: str) -> list[SellerNotificationSubscription]:
    get_seller_or_404(db, seller_id)
    return db.query(SellerNotificationSubscription).filter(SellerNotificationSubscription.seller_id == seller_id).all()


def create_notification(db: Session, body: NotificationSubCreateIn) -> SellerNotificationSubscription:
    get_seller_or_404(db, body.seller_id)
    exists = (
        db.query(SellerNotificationSubscription)
        .filter(
            SellerNotificationSubscription.seller_id == body.seller_id,
            SellerNotificationSubscription.event_type == body.event_type,
            SellerNotificationSubscription.channel == body.channel,
            SellerNotificationSubscription.destination == body.destination,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="notification_sub_exists")
    row = SellerNotificationSubscription(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_allocations(db: Session, seller_id: str) -> list[dict]:
    codes = _partner_codes(db)
    rows = db.query(SellerInventoryAllocation).filter(SellerInventoryAllocation.seller_id == seller_id).all()
    return [
        {**{c.name: getattr(r, c.name) for c in r.__table__.columns}, "partner_code": codes.get(r.channel_partner_id)}
        for r in rows
    ]


def upsert_allocation(db: Session, body: InventoryAllocationUpsertIn) -> SellerInventoryAllocation:
    get_seller_or_404(db, body.seller_id)
    if not db.get(SellerProduct, body.seller_product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="seller_product_not_found")
    row = (
        db.query(SellerInventoryAllocation)
        .filter(
            SellerInventoryAllocation.seller_id == body.seller_id,
            SellerInventoryAllocation.seller_product_id == body.seller_product_id,
            SellerInventoryAllocation.channel_partner_id == body.channel_partner_id,
            SellerInventoryAllocation.locker_id == body.locker_id,
        )
        .first()
    )
    avail = max(0, body.allocated_qty - body.reserved_qty)
    if row:
        row.allocated_qty = body.allocated_qty
        row.reserved_qty = body.reserved_qty
        row.available_qty = avail
        row.updated_at = _utcnow()
    else:
        row = SellerInventoryAllocation(
            id=new_id(),
            seller_id=body.seller_id,
            seller_product_id=body.seller_product_id,
            channel_partner_id=body.channel_partner_id,
            locker_id=body.locker_id,
            allocated_qty=body.allocated_qty,
            reserved_qty=body.reserved_qty,
            available_qty=avail,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_fulfillment_prefs(db: Session, seller_id: str) -> SellerFulfillmentPreference | None:
    get_seller_or_404(db, seller_id)
    return db.query(SellerFulfillmentPreference).filter(SellerFulfillmentPreference.seller_id == seller_id).first()


def upsert_fulfillment_prefs(db: Session, body: FulfillmentPreferenceUpsertIn) -> SellerFulfillmentPreference:
    get_seller_or_404(db, body.seller_id)
    row = db.query(SellerFulfillmentPreference).filter(SellerFulfillmentPreference.seller_id == body.seller_id).first()
    if row:
        for k, v in body.model_dump().items():
            setattr(row, k, v)
        row.updated_at = _utcnow()
    else:
        row = SellerFulfillmentPreference(id=new_id(), **body.model_dump())
        db.add(row)
    db.commit()
    db.refresh(row)
    return row
