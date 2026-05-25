from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.data.prompt4_player_catalog import PROMPT4_PLAYER_CODES
from app.data.world_player_catalog import ALL_PLAYER_CATALOG, PROMPT3_PLAYER_CODES
from app.models.order_ops import (
    AllocationRecord,
    LifecycleDeadlineRecord,
    LogisticsManifest,
    LogisticsManifestItem,
    FoodDeliveryOrder,
    OrderChannelPartnerLink,
    OrderIntegrationChannel,
    OrderItemRecord,
    OrderMarketplaceCommission,
    OrderOpsAudit,
)
from app.models.partner import EcommercePartner, LogisticsPartner
from app.schemas.order_ops import (
    AllocationCreateIn,
    AllocationOut,
    AllocationUpdateIn,
    ChannelCreateIn,
    ChannelOut,
    ChannelPartnerLinkOut,
    ChannelUpdateIn,
    CommissionCreateIn,
    CommissionOut,
    FoodDeliveryOrderCreateIn,
    FoodDeliveryOrderOut,
    FoodDeliveryOrderUpdateIn,
    LifecycleDeadlineOut,
    ManifestCreateIn,
    ManifestItemCreateIn,
    ManifestItemOut,
    ManifestOut,
    ManifestUpdateIn,
    OrderItemCreateIn,
    OrderItemOut,
    OrderItemUpdateIn,
    OrderOpsAuditOut,
)
from app.services.crypto_util import new_id

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _player_metadata(spec: dict) -> dict:
    code = spec["code"]
    return {
        "review_status": spec.get("review_status", "PLANNED"),
        "pickup_modes": spec.get("pickup_modes", []),
        "markets": spec.get("markets", []),
        "default_sla_hours": spec.get("default_sla_hours"),
        "webhook_events": spec.get("webhook_events", []),
        "catalog_version": "prompt4_v1",
        "prompt_group": "P3" if code in PROMPT3_PLAYER_CODES else "P4",
    }


def _parse_channel_metadata(row: OrderIntegrationChannel) -> dict:
    try:
        return json.loads(row.metadata_json or "{}")
    except json.JSONDecodeError:
        return {}


def channel_to_out(row: OrderIntegrationChannel, db: Session | None = None) -> ChannelOut:
    meta = _parse_channel_metadata(row)
    linked: list[dict] = []
    if db is not None:
        links = db.query(OrderChannelPartnerLink).filter(OrderChannelPartnerLink.channel_id == row.id).all()
        for link in links:
            if link.partner_kind == "ECOMMERCE":
                p = db.get(EcommercePartner, link.partner_id)
                if p:
                    linked.append({"kind": "ECOMMERCE", "code": p.code, "name": p.name, "role": link.link_role})
            else:
                p = db.get(LogisticsPartner, link.partner_id)
                if p:
                    linked.append({"kind": "LOGISTICS", "code": p.code, "name": p.name, "role": link.link_role})
    return ChannelOut(
        id=row.id,
        code=row.code,
        name=row.name,
        player_type=row.player_type,
        country=row.country,
        region_scope=row.region_scope,
        api_profile=row.api_profile,
        active=row.active,
        created_at=row.created_at,
        updated_at=row.updated_at,
        review_status=meta.get("review_status"),
        pickup_modes=meta.get("pickup_modes"),
        markets=meta.get("markets"),
        linked_partners=[ChannelPartnerLinkOut.model_validate(x) for x in linked],
    )


def _upsert_link(db: Session, *, channel_id: str, partner_id: str, partner_kind: str, role: str, now: datetime) -> None:
    existing = (
        db.query(OrderChannelPartnerLink)
        .filter(
            OrderChannelPartnerLink.channel_id == channel_id,
            OrderChannelPartnerLink.partner_id == partner_id,
            OrderChannelPartnerLink.partner_kind == partner_kind,
        )
        .first()
    )
    if existing:
        existing.link_role = role
        existing.active = True
        existing.updated_at = now
        return
    db.add(
        OrderChannelPartnerLink(
            id=new_id(),
            channel_id=channel_id,
            partner_id=partner_id,
            partner_kind=partner_kind,
            link_role=role,
            created_at=now,
            updated_at=now,
        )
    )


def _upsert_ecommerce(db: Session, spec: dict, now: datetime) -> EcommercePartner:
    row = db.query(EcommercePartner).filter(EcommercePartner.code == spec["code"]).first()
    if row:
        row.name = spec["name"]
        row.api_base_url = spec.get("api_base_url")
        row.sla_pickup_hours = spec.get("sla_pickup_hours", row.sla_pickup_hours)
        row.country = spec.get("country", row.country)
        row.currency = spec.get("currency", row.currency)
        row.status = "ACTIVE"
        row.active = True
        row.updated_at = now
        return row
    row = EcommercePartner(
        id=spec["id"],
        name=spec["name"],
        code=spec["code"],
        integration_type="REST",
        api_base_url=spec.get("api_base_url"),
        currency=spec.get("currency", "BRL"),
        sla_pickup_hours=spec.get("sla_pickup_hours", 72),
        active=True,
        country=spec.get("country", "BR"),
        status="ACTIVE",
        tier=spec.get("tier", "STANDARD"),
        support_email=spec.get("support_email"),
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    return row


def _upsert_logistics(db: Session, spec: dict, now: datetime) -> LogisticsPartner:
    row = db.query(LogisticsPartner).filter(LogisticsPartner.code == spec["code"]).first()
    if row:
        row.name = spec["name"]
        row.api_base_url = spec.get("api_base_url")
        row.tracking_url_template = spec.get("tracking_url_template")
        row.default_sla_hours = spec.get("default_sla_hours", row.default_sla_hours)
        row.country = spec.get("country", row.country)
        row.active = True
        row.updated_at = now
        return row
    row = LogisticsPartner(
        id=spec["id"],
        name=spec["name"],
        code=spec["code"],
        integration_type="REST",
        api_base_url=spec.get("api_base_url"),
        tracking_url_template=spec.get("tracking_url_template"),
        default_sla_hours=spec.get("default_sla_hours", 72),
        active=True,
        country=spec.get("country", "BR"),
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    return row


def sync_world_player_catalog(db: Session) -> dict[str, int]:
    now = _utcnow()
    counts = {"channels_created": 0, "channels_updated": 0, "ecommerce": 0, "logistics": 0, "links": 0}

    for spec in ALL_PLAYER_CATALOG:
        code = spec["code"]
        channel = db.query(OrderIntegrationChannel).filter(OrderIntegrationChannel.code == code).first()
        meta = _player_metadata(spec)
        linked_codes: list[dict] = []

        if channel is None:
            channel = OrderIntegrationChannel(
                id=new_id(),
                code=code,
                name=spec["name"],
                player_type=spec["player_type"],
                country=spec["country"],
                region_scope=spec.get("region_scope", "LOCAL"),
                api_profile=spec.get("api_profile", "REST"),
                active=True,
                metadata_json=json.dumps(meta),
                created_at=now,
                updated_at=now,
            )
            db.add(channel)
            db.flush()
            counts["channels_created"] += 1
        else:
            channel.name = spec["name"]
            channel.player_type = spec["player_type"]
            channel.country = spec["country"]
            channel.region_scope = spec.get("region_scope", channel.region_scope)
            channel.api_profile = spec.get("api_profile", channel.api_profile)
            channel.metadata_json = json.dumps(meta)
            channel.updated_at = now
            counts["channels_updated"] += 1

        ec_spec = spec.get("ecommerce_partner")
        if ec_spec:
            ec = _upsert_ecommerce(db, ec_spec, now)
            counts["ecommerce"] += 1
            _upsert_link(db, channel_id=channel.id, partner_id=ec.id, partner_kind="ECOMMERCE", role="PRIMARY", now=now)
            counts["links"] += 1
            linked_codes.append({"kind": "ECOMMERCE", "code": ec.code})

        lg_spec = spec.get("logistics_partner")
        if lg_spec:
            lg = _upsert_logistics(db, lg_spec, now)
            counts["logistics"] += 1
            role = "CARRIER" if spec["player_type"] == "CARRIER" else "PRIMARY"
            _upsert_link(db, channel_id=channel.id, partner_id=lg.id, partner_kind="LOGISTICS", role=role, now=now)
            counts["links"] += 1
            linked_codes.append({"kind": "LOGISTICS", "code": lg.code})

        meta["linked_partners"] = linked_codes
        channel.metadata_json = json.dumps(meta)

    db.commit()
    return counts


def seed_integration_channels(db: Session) -> int:
    result = sync_world_player_catalog(db)
    return result["channels_created"] + result["channels_updated"]


def world_players_review(db: Session) -> dict:
    items = []
    by_type: dict[str, int] = {}
    prompt3_found: set[str] = set()
    prompt4_found: set[str] = set()

    for spec in ALL_PLAYER_CATALOG:
        code = spec["code"]
        channel = db.query(OrderIntegrationChannel).filter(OrderIntegrationChannel.code == code).first()
        meta = _parse_channel_metadata(channel) if channel else {}
        ec_code = (spec.get("ecommerce_partner") or {}).get("code")
        lg_code = (spec.get("logistics_partner") or {}).get("code")
        if channel:
            if code in PROMPT3_PLAYER_CODES:
                prompt3_found.add(code)
            if code in PROMPT4_PLAYER_CODES:
                prompt4_found.add(code)
        pt = spec["player_type"]
        by_type[pt] = by_type.get(pt, 0) + 1
        items.append(
            {
                "code": code,
                "name": spec["name"],
                "player_type": pt,
                "country": spec["country"],
                "region_scope": spec.get("region_scope", "LOCAL"),
                "review_status": meta.get("review_status", "MISSING"),
                "markets": meta.get("markets", spec.get("markets", [])),
                "pickup_modes": meta.get("pickup_modes", spec.get("pickup_modes", [])),
                "api_profile": channel.api_profile if channel else spec.get("api_profile"),
                "ecommerce_partner_code": ec_code,
                "logistics_partner_code": lg_code,
                "channel_id": channel.id if channel else None,
                "active": channel.active if channel else False,
                "configured": channel is not None,
                "prompt_group": meta.get("prompt_group", "P3" if code in PROMPT3_PLAYER_CODES else "P4"),
            }
        )

    configured = prompt3_found | prompt4_found
    return {
        "players": items,
        "by_type": by_type,
        "prompt3_total": len(PROMPT3_PLAYER_CODES),
        "prompt3_configured": len(prompt3_found),
        "prompt3_complete": prompt3_found >= PROMPT3_PLAYER_CODES,
        "prompt4_total": len(PROMPT4_PLAYER_CODES),
        "prompt4_configured": len(prompt4_found),
        "prompt4_complete": prompt4_found >= PROMPT4_PLAYER_CODES,
        "catalog_total": len(ALL_PLAYER_CATALOG),
        "catalog_configured": len(configured),
    }


def list_channels(db: Session, *, player_type: str | None, active: bool | None, limit: int, offset: int):
    q = db.query(OrderIntegrationChannel)
    if player_type:
        q = q.filter(OrderIntegrationChannel.player_type == player_type.upper())
    if active is not None:
        q = q.filter(OrderIntegrationChannel.active == active)
    total = q.count()
    rows = q.order_by(OrderIntegrationChannel.name).offset(offset).limit(limit).all()
    return [channel_to_out(r, db) for r in rows], total


def create_channel(db: Session, body: ChannelCreateIn) -> ChannelOut:
    if db.query(OrderIntegrationChannel).filter(OrderIntegrationChannel.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="channel_code_exists")
    now = _utcnow()
    row = OrderIntegrationChannel(
        id=body.id or new_id(),
        code=body.code.upper(),
        name=body.name,
        player_type=body.player_type.upper(),
        country=body.country,
        region_scope=body.region_scope,
        api_profile=body.api_profile,
        active=body.active,
        metadata_json=json.dumps(body.metadata or {}),
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return channel_to_out(row, db)


def update_channel(db: Session, channel_id: str, body: ChannelUpdateIn) -> ChannelOut:
    row = db.get(OrderIntegrationChannel, channel_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="channel_not_found")
    if body.name is not None:
        row.name = body.name
    if body.active is not None:
        row.active = body.active
    if body.api_profile is not None:
        row.api_profile = body.api_profile
    if body.metadata is not None:
        row.metadata_json = json.dumps(body.metadata)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return channel_to_out(row, db)


def list_allocations(db: Session, *, order_id: str | None, state: str | None, limit: int, offset: int):
    q = db.query(AllocationRecord)
    if order_id:
        q = q.filter(AllocationRecord.order_id == order_id)
    if state:
        q = q.filter(AllocationRecord.state == state.upper())
    total = q.count()
    rows = q.order_by(AllocationRecord.created_at.desc()).offset(offset).limit(limit).all()
    return [AllocationOut.model_validate(r) for r in rows], total


def create_allocation(db: Session, body: AllocationCreateIn) -> AllocationOut:
    aid = body.id or f"alloc-{new_id()[:12]}"
    if db.get(AllocationRecord, aid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="allocation_id_exists")
    now = _utcnow()
    row = AllocationRecord(
        id=aid,
        order_id=body.order_id,
        locker_id=body.locker_id,
        slot=body.slot,
        state=body.state,
        slot_size=body.slot_size,
        ttl_seconds=body.ttl_seconds,
        allocated_at=now if body.state != "RESERVED_PENDING_PAYMENT" else None,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return AllocationOut.model_validate(row)


def update_allocation(db: Session, alloc_id: str, body: AllocationUpdateIn) -> AllocationOut:
    row = db.get(AllocationRecord, alloc_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="allocation_not_found")
    now = _utcnow()
    if body.state is not None:
        row.state = body.state
        if body.state == "RESERVED_PAID_PENDING_PICKUP" and not row.allocated_at:
            row.allocated_at = now
        if body.state.startswith("RELEASED") or body.state == "EXPIRED":
            row.released_at = now
    if body.locker_id is not None:
        row.locker_id = body.locker_id
    if body.slot is not None:
        row.slot = body.slot
    if body.release_reason is not None:
        row.release_reason = body.release_reason
    row.updated_at = now
    db.commit()
    db.refresh(row)
    return AllocationOut.model_validate(row)


def list_manifests(db: Session, *, status: str | None, partner_id: str | None, limit: int, offset: int):
    q = db.query(LogisticsManifest)
    if status:
        q = q.filter(LogisticsManifest.status == status.upper())
    if partner_id:
        q = q.filter(LogisticsManifest.logistics_partner_id == partner_id)
    total = q.count()
    rows = q.order_by(LogisticsManifest.manifest_date.desc()).offset(offset).limit(limit).all()
    return [ManifestOut.model_validate(r) for r in rows], total


def create_manifest(db: Session, body: ManifestCreateIn) -> ManifestOut:
    mid = body.id or new_id()
    if db.get(LogisticsManifest, mid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="manifest_id_exists")
    now = _utcnow()
    row = LogisticsManifest(
        id=mid,
        logistics_partner_id=body.logistics_partner_id,
        locker_id=body.locker_id,
        manifest_date=body.manifest_date,
        carrier_route_code=body.carrier_route_code,
        expected_parcel_count=body.expected_parcel_count,
        status=body.status,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ManifestOut.model_validate(row)


def update_manifest(db: Session, manifest_id: str, body: ManifestUpdateIn) -> ManifestOut:
    row = db.get(LogisticsManifest, manifest_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="manifest_not_found")
    if body.status is not None:
        row.status = body.status
    if body.actual_parcel_count is not None:
        row.actual_parcel_count = body.actual_parcel_count
    if body.carrier_note is not None:
        row.carrier_note = body.carrier_note
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return ManifestOut.model_validate(row)


def list_manifest_items(db: Session, *, manifest_id: str | None, limit: int, offset: int):
    q = db.query(LogisticsManifestItem)
    if manifest_id:
        q = q.filter(LogisticsManifestItem.manifest_id == manifest_id)
    total = q.count()
    rows = q.order_by(LogisticsManifestItem.tracking_code.asc()).offset(offset).limit(limit).all()
    return [ManifestItemOut.model_validate(r) for r in rows], total


def add_manifest_item(db: Session, body: ManifestItemCreateIn) -> ManifestItemOut:
    if not db.get(LogisticsManifest, body.manifest_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="manifest_not_found")
    iid = body.id or new_id()
    row = LogisticsManifestItem(
        id=iid,
        manifest_id=body.manifest_id,
        delivery_id=body.delivery_id,
        tracking_code=body.tracking_code,
        sequence_number=body.sequence_number,
        status=body.status,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ManifestItemOut.model_validate(row)


def create_order_item(db: Session, body: OrderItemCreateIn) -> OrderItemOut:
    iid = body.id or new_id()
    if db.get(OrderItemRecord, iid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="order_item_id_exists")
    now = _utcnow()
    total = body.quantity * body.unit_amount_cents
    row = OrderItemRecord(
        id=iid,
        order_id=body.order_id,
        sku_id=body.sku_id,
        sku_description=body.sku_description,
        quantity=body.quantity,
        unit_amount_cents=body.unit_amount_cents,
        total_amount_cents=total,
        item_status=body.item_status,
        metadata_json=json.dumps(body.metadata or {}),
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return OrderItemOut.model_validate(row)


def update_order_item(db: Session, item_id: str, body: OrderItemUpdateIn) -> OrderItemOut:
    row = db.get(OrderItemRecord, item_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order_item_not_found")
    if body.quantity is not None:
        row.quantity = body.quantity
    if body.unit_amount_cents is not None:
        row.unit_amount_cents = body.unit_amount_cents
    if body.item_status is not None:
        row.item_status = body.item_status
    row.total_amount_cents = row.quantity * row.unit_amount_cents
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return OrderItemOut.model_validate(row)


def list_commissions(db: Session, *, order_id: str | None, status: str | None, limit: int, offset: int):
    q = db.query(OrderMarketplaceCommission)
    if order_id:
        q = q.filter(OrderMarketplaceCommission.order_id == order_id)
    if status:
        q = q.filter(OrderMarketplaceCommission.status == status.upper())
    total = q.count()
    rows = q.order_by(OrderMarketplaceCommission.created_at.desc()).offset(offset).limit(limit).all()
    return [CommissionOut.model_validate(r) for r in rows], total


def create_commission(db: Session, body: CommissionCreateIn) -> CommissionOut:
    cid = body.id or new_id()
    now = _utcnow()
    row = OrderMarketplaceCommission(
        id=cid,
        seller_id=body.seller_id,
        order_id=body.order_id,
        order_item_id=body.order_item_id,
        commission_rate_pct=body.commission_rate_pct,
        commission_amount_cents=body.commission_amount_cents,
        ellan_fee_cents=body.ellan_fee_cents,
        payment_gateway_fee_cents=body.payment_gateway_fee_cents,
        net_to_seller_cents=body.net_to_seller_cents,
        status=body.status,
        created_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return CommissionOut.model_validate(row)


def list_deadlines_orm(
    db: Session, *, order_id: str | None, status: str | None, deadline_type: str | None, limit: int, offset: int
):
    q = db.query(LifecycleDeadlineRecord)
    if order_id:
        q = q.filter(LifecycleDeadlineRecord.order_id == order_id)
    if status:
        q = q.filter(LifecycleDeadlineRecord.status == status.upper())
    if deadline_type:
        q = q.filter(LifecycleDeadlineRecord.deadline_type == deadline_type.upper())
    total = q.count()
    rows = q.order_by(LifecycleDeadlineRecord.due_at.asc()).offset(offset).limit(limit).all()
    return [LifecycleDeadlineOut.model_validate(r) for r in rows], total


def list_audit(db: Session, *, order_id: str | None, limit: int, offset: int):
    q = db.query(OrderOpsAudit)
    if order_id:
        q = q.filter(OrderOpsAudit.order_id == order_id)
    total = q.count()
    rows = q.order_by(OrderOpsAudit.created_at.desc()).offset(offset).limit(limit).all()
    return [OrderOpsAuditOut.model_validate(r) for r in rows], total


def record_audit(
    db: Session,
    *,
    action: str,
    result: str,
    correlation_id: str,
    order_id: str | None = None,
    details: dict | None = None,
) -> OrderOpsAuditOut:
    row = OrderOpsAudit(
        id=f"aud-{new_id()[:16]}",
        action=action,
        result=result,
        correlation_id=correlation_id,
        order_id=order_id,
        details_json=json.dumps(details or {}),
        created_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return OrderOpsAuditOut.model_validate(row)


def list_food_delivery(
    db: Session, *, order_id: str | None, platform_code: str | None, limit: int, offset: int
) -> tuple[list[FoodDeliveryOrderOut], int]:
    q = db.query(FoodDeliveryOrder)
    if order_id:
        q = q.filter(FoodDeliveryOrder.order_id == order_id)
    if platform_code:
        q = q.filter(FoodDeliveryOrder.platform_code == platform_code.upper())
    total = q.count()
    rows = q.order_by(FoodDeliveryOrder.created_at.desc()).offset(offset).limit(limit).all()
    return [FoodDeliveryOrderOut.model_validate(r) for r in rows], total


def create_food_delivery(db: Session, body: FoodDeliveryOrderCreateIn) -> FoodDeliveryOrderOut:
    fid = body.id or new_id()
    if db.get(FoodDeliveryOrder, fid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="food_delivery_id_exists")
    now = _utcnow()
    row = FoodDeliveryOrder(
        id=fid,
        order_id=body.order_id,
        platform_code=body.platform_code.upper(),
        external_order_ref=body.external_order_ref,
        restaurant_id=body.restaurant_id,
        status=body.status,
        temperature_zone=body.temperature_zone,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return FoodDeliveryOrderOut.model_validate(row)


def update_food_delivery(db: Session, row_id: str, body: FoodDeliveryOrderUpdateIn) -> FoodDeliveryOrderOut:
    row = db.get(FoodDeliveryOrder, row_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="food_delivery_not_found")
    for field in ("status", "prep_ready_at", "locker_handoff_at", "picked_up_at"):
        val = getattr(body, field, None)
        if val is not None:
            setattr(row, field, val)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return FoodDeliveryOrderOut.model_validate(row)


def seed_extended_order_graph(db: Session, *, order_id: str, partner_id: str) -> None:
    now = _utcnow()
    seed_integration_channels(db)

    alloc_id = "alloc-seed-demo-001"
    if not db.get(AllocationRecord, alloc_id):
        db.add(
            AllocationRecord(
                id=alloc_id,
                order_id=order_id,
                locker_id="LOCKER-DEMO-01",
                slot=12,
                state="RESERVED_PAID_PENDING_PICKUP",
                slot_size="M",
                allocated_at=now,
                created_at=now,
                updated_at=now,
            )
        )

    mf_id = "mf-seed-demo-001"
    if not db.get(LogisticsManifest, mf_id):
        db.add(
            LogisticsManifest(
                id=mf_id,
                logistics_partner_id="lg-ops-001",
                locker_id="LOCKER-DEMO-01",
                manifest_date=date.today(),
                carrier_route_code="DPD-BR-SP-01",
                expected_parcel_count=1,
                actual_parcel_count=1,
                status="DELIVERED",
                delivered_at=now,
                created_at=now,
                updated_at=now,
            )
        )
        db.add(
            LogisticsManifestItem(
                id="mfi-seed-demo-001",
                manifest_id=mf_id,
                tracking_code="BR123456789ELL",
                sequence_number=1,
                status="STORED",
                processed_at=now,
            )
        )

    dl_key = f"order.{order_id}.pickup_timeout"
    if not db.query(LifecycleDeadlineRecord).filter(LifecycleDeadlineRecord.deadline_key == dl_key).first():
        db.add(
            LifecycleDeadlineRecord(
                id=new_id(),
                deadline_key=dl_key,
                order_id=order_id,
                order_channel="KIOSK",
                deadline_type="PICKUP_TIMEOUT",
                status="PENDING",
                due_at=now + timedelta(hours=48),
                failure_count=0,
                payload_json=json.dumps({"order_id": order_id}),
                created_at=now,
                updated_at=now,
            )
        )

    if not db.query(OrderMarketplaceCommission).filter(OrderMarketplaceCommission.order_id == order_id).first():
        db.add(
            OrderMarketplaceCommission(
                id="mc-seed-demo-001",
                seller_id="seller-demo-01",
                order_id=order_id,
                order_item_id="oi-seed-demo-001",
                commission_rate_pct=12.5,
                commission_amount_cents=624,
                ellan_fee_cents=200,
                payment_gateway_fee_cents=150,
                net_to_seller_cents=4016,
                status="PENDING",
                created_at=now,
            )
        )

    fd_id = "fd-seed-demo-001"
    if not db.get(FoodDeliveryOrder, fd_id):
        db.add(
            FoodDeliveryOrder(
                id=fd_id,
                order_id=order_id,
                platform_code="IFOOD",
                external_order_ref="ifood-ext-998877",
                restaurant_id="rest-demo-sp",
                status="READY_FOR_LOCKER",
                temperature_zone="HOT",
                prep_ready_at=now,
                metadata_json=json.dumps({"handoff": "locker", "brand": "iFood"}),
                created_at=now,
                updated_at=now,
            )
        )

    from app.services.orders_advanced_service import seed_advanced_demo
    from app.services.orders_extras_service import seed_extras_demo

    seed_extras_demo(db, order_id)
    seed_advanced_demo(db, order_id)
    db.commit()
