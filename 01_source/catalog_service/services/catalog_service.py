from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from events.publishers import (
    publish_product_created,
    publish_product_deprecated,
    publish_product_price_changed,
)
from models import (
    Category,
    PartnerProductRule,
    Product,
    ProductCompatibility,
    ProductDimensions,
)
from schemas import (
    DimensionsIn,
    LockerCheckIn,
    OrderPickupProductCacheDTO,
    PartnerProductCreateIn,
    ProductDetailOut,
)
from services import compatibility_service


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def assert_partner_active(partner_id: str) -> None:
    if partner_id.endswith("inactive"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Partner not active")


def get_partner_rule(db: Session, partner_id: str, category_id: str) -> PartnerProductRule | None:
    row = (
        db.query(PartnerProductRule)
        .filter(
            PartnerProductRule.partner_id == partner_id,
            PartnerProductRule.category_id == category_id,
        )
        .first()
    )
    if row is not None:
        return row
    return (
        db.query(PartnerProductRule)
        .filter(
            PartnerProductRule.partner_id == partner_id,
            PartnerProductRule.category_id.is_(None),
        )
        .first()
    )


def to_order_pickup_cache_dto(product: Product, dims: ProductDimensions | None) -> OrderPickupProductCacheDTO:
    return OrderPickupProductCacheDTO(
        sku_id=product.sku_id,
        partner_id=product.partner_id,
        partner_sku=product.partner_sku,
        name=product.name,
        description=product.description,
        category_id=product.category_id,
        amount_cents=product.amount_cents,
        currency=product.currency,
        width_mm=dims.width_mm if dims else None,
        height_mm=dims.height_mm if dims else None,
        depth_mm=dims.depth_mm if dims else None,
        weight_g=dims.weight_g if dims else None,
        is_active=product.is_active,
        requires_signature=product.requires_signature,
        is_hazardous=product.is_hazardous,
        temperature_zone=product.temperature_zone,
        created_at=product.created_at,
        updated_at=product.updated_at,
        synced_at=None,
    )


def _serialize_product_detail(product: Product, dims: ProductDimensions | None) -> ProductDetailOut:
    images: list[str] = []
    try:
        raw = json.loads(product.images_json or "[]")
        if isinstance(raw, list):
            images = [str(x) for x in raw]
    except json.JSONDecodeError:
        images = []
    dim_in: DimensionsIn | None = None
    if dims is not None:
        dim_in = DimensionsIn(
            width_mm=dims.width_mm,
            height_mm=dims.height_mm,
            depth_mm=dims.depth_mm,
            weight_g=dims.weight_g,
        )
    return ProductDetailOut(
        sku_id=product.sku_id,
        partner_id=product.partner_id,
        partner_sku=product.partner_sku,
        name=product.name,
        description=product.description,
        category_id=product.category_id,
        amount_cents=product.amount_cents,
        currency=product.currency,
        images=images,
        is_active=product.is_active,
        is_deprecated=product.is_deprecated,
        requires_signature=product.requires_signature,
        is_fragile=product.is_fragile,
        is_hazardous=product.is_hazardous,
        temperature_zone=product.temperature_zone,
        dimensions=dim_in,
        order_pickup_cache=to_order_pickup_cache_dto(product, dims),
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def get_product_detail(db: Session, sku_id: str) -> ProductDetailOut:
    product = db.query(Product).filter(Product.sku_id == sku_id).first()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    dims = db.query(ProductDimensions).filter(ProductDimensions.product_id == sku_id).first()
    return _serialize_product_detail(product, dims)


def list_categories(db: Session) -> list[Category]:
    return db.query(Category).order_by(Category.name.asc()).all()


def _validate_eligible_lockers_fit(
    payload: PartnerProductCreateIn,
    partner_id: str,
    db: Session,
) -> None:
    if not payload.eligible_lockers:
        return
    rule = get_partner_rule(db, partner_id, payload.category_id)
    synthetic = Product(
        sku_id="",
        partner_id=partner_id,
        partner_sku=payload.partner_sku,
        name=payload.name,
        description=payload.description,
        category_id=payload.category_id,
        amount_cents=payload.price_cents,
        currency=payload.currency,
        images_json="[]",
        is_active=True,
        is_deprecated=False,
        requires_signature=payload.compatibility_rules.requires_signature,
        is_fragile=payload.compatibility_rules.is_fragile,
        is_hazardous=payload.compatibility_rules.is_hazardous,
        temperature_zone=payload.compatibility_rules.temperature_zone,
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    dims = ProductDimensions(
        id="",
        product_id="",
        width_mm=payload.dimensions.width_mm,
        height_mm=payload.dimensions.height_mm,
        depth_mm=payload.dimensions.depth_mm,
        weight_g=payload.dimensions.weight_g,
    )
    for slot in payload.eligible_lockers:
        if slot.slot_width_mm is None or slot.slot_height_mm is None or slot.slot_depth_mm is None:
            continue
        locker = LockerCheckIn(
            locker_id=slot.locker_id,
            slot_width_mm=slot.slot_width_mm,
            slot_height_mm=slot.slot_height_mm,
            slot_depth_mm=slot.slot_depth_mm,
            max_weight_g=slot.max_weight_g or 1_000_000,
            temperature_zone=slot.temperature_zone or "AMBIENT",
            signature_available=slot.signature_available,
            hazardous_allowed=slot.hazardous_allowed,
        )
        res = compatibility_service.is_product_compatible_with_locker(synthetic, dims, rule, locker)
        if res.compatible:
            return
    if any(
        s.slot_width_mm is not None and s.slot_height_mm is not None and s.slot_depth_mm is not None
        for s in payload.eligible_lockers
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product does not fit any declared eligible locker",
        )


def create_or_update_partner_product(
    db: Session, partner_id: str, payload: PartnerProductCreateIn
) -> tuple[Product, str]:
    assert_partner_active(partner_id)
    cat = db.query(Category).filter(Category.id == payload.category_id).first()
    if cat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    _validate_eligible_lockers_fit(payload, partner_id, db)

    existing = (
        db.query(Product)
        .filter(
            and_(
                Product.partner_id == partner_id,
                Product.partner_sku == payload.partner_sku,
            )
        )
        .first()
    )

    images_json = json.dumps(payload.images)
    now = _utcnow()

    if existing is not None:
        old_price = existing.amount_cents
        was_deprecated = existing.is_deprecated
        existing.name = payload.name
        existing.description = payload.description
        existing.category_id = payload.category_id
        existing.amount_cents = payload.price_cents
        existing.currency = payload.currency
        existing.images_json = images_json
        existing.requires_signature = payload.compatibility_rules.requires_signature
        existing.is_fragile = payload.compatibility_rules.is_fragile
        existing.temperature_zone = payload.compatibility_rules.temperature_zone
        existing.is_hazardous = payload.compatibility_rules.is_hazardous
        existing.updated_at = now
        if payload.mark_deprecated:
            existing.is_deprecated = True
            existing.is_active = False
        dims = db.query(ProductDimensions).filter(ProductDimensions.product_id == existing.sku_id).first()
        if dims is None:
            dims = ProductDimensions(
                id=str(uuid.uuid4()),
                product_id=existing.sku_id,
                width_mm=payload.dimensions.width_mm,
                height_mm=payload.dimensions.height_mm,
                depth_mm=payload.dimensions.depth_mm,
                weight_g=payload.dimensions.weight_g,
            )
            db.add(dims)
        else:
            dims.width_mm = payload.dimensions.width_mm
            dims.height_mm = payload.dimensions.height_mm
            dims.depth_mm = payload.dimensions.depth_mm
            dims.weight_g = payload.dimensions.weight_g
        db.query(ProductCompatibility).filter(ProductCompatibility.product_id == existing.sku_id).delete()
        _insert_compatibilities(db, existing.sku_id, payload)
        db.add(existing)
        db.commit()
        db.refresh(existing)
        event = "unchanged"
        pub_payload = {
            "sku_id": existing.sku_id,
            "partner_id": partner_id,
            "partner_sku": existing.partner_sku,
            "amount_cents": existing.amount_cents,
            "currency": existing.currency,
        }
        if old_price != existing.amount_cents:
            publish_product_price_changed(pub_payload)
            event = "price_changed"
        if (not was_deprecated) and existing.is_deprecated:
            publish_product_deprecated(pub_payload)
            event = "deprecated" if event == "unchanged" else event
        return existing, event

    sku_id = str(uuid.uuid4())
    product = Product(
        sku_id=sku_id,
        partner_id=partner_id,
        partner_sku=payload.partner_sku,
        name=payload.name,
        description=payload.description,
        category_id=payload.category_id,
        amount_cents=payload.price_cents,
        currency=payload.currency,
        images_json=images_json,
        is_active=True,
        is_deprecated=bool(payload.mark_deprecated),
        requires_signature=payload.compatibility_rules.requires_signature,
        is_fragile=payload.compatibility_rules.is_fragile,
        is_hazardous=payload.compatibility_rules.is_hazardous,
        temperature_zone=payload.compatibility_rules.temperature_zone,
        created_at=now,
        updated_at=now,
    )
    if payload.mark_deprecated:
        product.is_active = False
    dims = ProductDimensions(
        id=str(uuid.uuid4()),
        product_id=sku_id,
        width_mm=payload.dimensions.width_mm,
        height_mm=payload.dimensions.height_mm,
        depth_mm=payload.dimensions.depth_mm,
        weight_g=payload.dimensions.weight_g,
    )
    db.add(product)
    db.add(dims)
    _insert_compatibilities(db, sku_id, payload)
    db.commit()
    db.refresh(product)
    publish_product_created(
        {
            "sku_id": sku_id,
            "partner_id": partner_id,
            "partner_sku": payload.partner_sku,
            "amount_cents": product.amount_cents,
            "currency": product.currency,
            "category_id": product.category_id,
        }
    )
    if product.is_deprecated:
        publish_product_deprecated(
            {
                "sku_id": sku_id,
                "partner_id": partner_id,
                "partner_sku": payload.partner_sku,
            }
        )
    return product, "created"


def _insert_compatibilities(db: Session, sku_id: str, payload: PartnerProductCreateIn) -> None:
    if not payload.eligible_lockers:
        return
    for slot in payload.eligible_lockers:
        row = ProductCompatibility(
            id=str(uuid.uuid4()),
            product_id=sku_id,
            locker_id=slot.locker_id,
            locker_label=slot.locker_label,
            recommended_slot_size=slot.recommended_slot_size,
            slot_width_mm=slot.slot_width_mm,
            slot_height_mm=slot.slot_height_mm,
            slot_depth_mm=slot.slot_depth_mm,
            max_weight_g=slot.max_weight_g,
            temperature_zone=slot.temperature_zone,
            signature_available=slot.signature_available,
            hazardous_allowed=slot.hazardous_allowed,
        )
        db.add(row)


def check_product_compatibility(
    db: Session, sku_id: str, locker: LockerCheckIn
) -> compatibility_service.CompatibilityResult:
    product = db.query(Product).filter(Product.sku_id == sku_id).first()
    if product is None:
        return compatibility_service.CompatibilityResult(False, "PRODUCT_NOT_REGISTERED", None)
    dims = db.query(ProductDimensions).filter(ProductDimensions.product_id == sku_id).first()
    rule = get_partner_rule(db, product.partner_id, product.category_id)
    return compatibility_service.is_product_compatible_with_locker(product, dims, rule, locker)


def list_eligible_lockers(
    db: Session, partner_id: str, product_sku: str | None
) -> list[dict]:
    if product_sku:
        p = (
            db.query(Product)
            .filter(and_(Product.sku_id == product_sku, Product.partner_id == partner_id))
            .first()
        )
        if p is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found for partner",
            )
    q = (
        db.query(ProductCompatibility)
        .join(Product, Product.sku_id == ProductCompatibility.product_id)
        .filter(Product.partner_id == partner_id)
    )
    if product_sku:
        q = q.filter(Product.sku_id == product_sku)
    rows = q.all()
    out: list[dict] = []
    seen: set[str] = set()
    for r in rows:
        if r.locker_id in seen:
            continue
        seen.add(r.locker_id)
        out.append(
            {
                "locker_id": r.locker_id,
                "locker_label": r.locker_label,
                "recommended_slot_size": r.recommended_slot_size,
                "sku_id": product_sku,
            }
        )
    return out
