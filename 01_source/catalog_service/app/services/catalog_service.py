from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.events import publishers, streams
from app.models.category import Category
from app.models.dimensions import ProductDimensions
from app.models.product import Product, ProductVersion
from app.schemas.product import (
    BulkProductIn,
    BulkProductResponse,
    OrderPickupProductCacheDTO,
    ProductCreateIn,
    ProductCreateResponse,
    ProductDetailOut,
    ProductVersionOut,
)
from app.services import cache_service, webhook_service


class CatalogError(Exception):
    pass


def assert_partner_active(partner_id: str) -> None:
    if not partner_id or len(partner_id) < 8:
        raise CatalogError("invalid_partner")


def ensure_category(db: Session, category_id: str) -> Category:
    c = db.query(Category).filter(Category.id == category_id, Category.is_active.is_(True)).first()
    if not c:
        raise CatalogError("category_not_found")
    return c


def _snapshot_product(p: Product) -> dict[str, Any]:
    d = p.dimensions
    return {
        "sku_id": p.sku_id,
        "partner_id": p.partner_id,
        "partner_sku": p.partner_sku,
        "name": p.name,
        "description": p.description,
        "category_id": p.category_id,
        "price_cents": p.price_cents,
        "currency": p.currency,
        "images": json.loads(p.images) if p.images else [],
        "requires_signature": p.requires_signature,
        "is_hazardous": p.is_hazardous,
        "temperature_zone": p.temperature_zone,
        "version": p.version,
        "is_active": p.is_active,
        "dimensions": {
            "width_mm": d.width_mm if d else None,
            "height_mm": d.height_mm if d else None,
            "depth_mm": d.depth_mm if d else None,
            "weight_g": d.weight_g if d else None,
        },
    }


def to_order_pickup_dto(p: Product) -> OrderPickupProductCacheDTO:
    d = p.dimensions
    return OrderPickupProductCacheDTO(
        sku_id=p.sku_id,
        partner_id=p.partner_id,
        partner_sku=p.partner_sku,
        name=p.name,
        description=p.description,
        category_id=p.category_id,
        amount_cents=p.price_cents,
        currency=p.currency,
        width_mm=d.width_mm if d else None,
        height_mm=d.height_mm if d else None,
        depth_mm=d.depth_mm if d else None,
        weight_g=d.weight_g if d else None,
        is_active=p.is_active,
        requires_signature=p.requires_signature,
        is_hazardous=p.is_hazardous,
        temperature_zone=p.temperature_zone,
        created_at=p.created_at,
        updated_at=p.updated_at,
        synced_at=datetime.now(timezone.utc),
    )


def to_detail_out(p: Product) -> ProductDetailOut:
    imgs = json.loads(p.images) if p.images else []
    return ProductDetailOut(
        sku_id=p.sku_id,
        partner_id=p.partner_id,
        partner_sku=p.partner_sku,
        name=p.name,
        description=p.description,
        category_id=p.category_id,
        price_cents=p.price_cents,
        currency=p.currency,
        images=imgs if isinstance(imgs, list) else [],
        requires_signature=p.requires_signature,
        is_hazardous=p.is_hazardous,
        temperature_zone=p.temperature_zone,
        version=p.version,
        is_active=p.is_active,
        order_pickup_cache=to_order_pickup_dto(p),
    )


def record_version(db: Session, p: Product) -> None:
    snap = _snapshot_product(p)
    v = ProductVersion(
        id=str(uuid.uuid4()),
        sku_id=p.sku_id,
        version=p.version,
        snapshot_json=json.dumps(snap, default=str),
    )
    db.add(v)


def create_product(
    db: Session,
    redis: Any,
    partner_id: str,
    body: ProductCreateIn,
    *,
    emit_events: bool = True,
) -> ProductCreateResponse:
    assert_partner_active(partner_id)
    ensure_category(db, body.category_id)
    exists = (
        db.query(Product)
        .filter(Product.partner_id == partner_id, Product.partner_sku == body.partner_sku)
        .first()
    )
    if exists:
        raise CatalogError("partner_sku_exists")
    p = Product(
        sku_id=str(uuid.uuid4()),
        partner_id=partner_id,
        partner_sku=body.partner_sku,
        name=body.name,
        description=body.description,
        category_id=body.category_id,
        price_cents=body.price_cents,
        currency=body.currency,
        images=json.dumps(body.images),
        requires_signature=body.compatibility_rules.requires_signature,
        is_hazardous=body.compatibility_rules.is_fragile,
        temperature_zone=body.compatibility_rules.temperature_zone,
        version=1,
        is_active=True,
    )
    dim = ProductDimensions(
        id=str(uuid.uuid4()),
        product_sku_id=p.sku_id,
        width_mm=body.dimensions.width_mm,
        height_mm=body.dimensions.height_mm,
        depth_mm=body.dimensions.depth_mm,
        weight_g=body.dimensions.weight_g,
    )
    p.dimensions = dim
    db.add(p)
    db.commit()
    db.refresh(p)
    record_version(db, p)
    db.commit()
    detail = to_detail_out(p)
    cache_service.set_json(redis, cache_service.cache_key_product(p.sku_id), detail.model_dump(mode="json"))
    pl = _snapshot_product(p)
    if emit_events:
        publishers.publish_product_created(redis, pl)
        publishers.publish_synced(redis, {"sku_id": p.sku_id, "snapshot": pl})
        webhook_service.notify_partner(redis, partner_id, streams.PRODUCT_CREATED, pl)
    return ProductCreateResponse(
        sku_id=p.sku_id,
        partner_id=partner_id,
        partner_sku=body.partner_sku,
        version=p.version,
    )


def bulk_create(db: Session, redis: Any, bulk: BulkProductIn) -> BulkProductResponse:
    partner_id = bulk.partner_id
    created: list[ProductCreateResponse] = []
    errors: list[dict[str, Any]] = []
    for idx, item in enumerate(bulk.items):
        try:
            body = ProductCreateIn(
                partner_sku=item.partner_sku,
                name=item.name,
                category_id=item.category_id,
                dimensions=item.dimensions,
                price_cents=item.price_cents,
                currency=item.currency,
                images=item.images,
                compatibility_rules=item.compatibility_rules,
            )
            created.append(create_product(db, redis, partner_id, body))
        except CatalogError as e:
            errors.append({"index": idx, "error": str(e)})
    return BulkProductResponse(created=created, errors=errors)


def get_product_detail(db: Session, redis: Any | None, sku_id: str) -> tuple[ProductDetailOut, str] | None:
    key = cache_service.cache_key_product(sku_id)
    if redis is not None:
        cached = cache_service.get_json(redis, key)
        if cached:
            try:
                return ProductDetailOut.model_validate(cached), "HIT"
            except Exception:
                cache_service.delete(redis, key)
    p = db.query(Product).filter(Product.sku_id == sku_id).first()
    if not p:
        return None
    out = to_detail_out(p)
    if redis is not None:
        cache_service.set_json(redis, key, out.model_dump(mode="json"))
    return out, "MISS"


def list_product_versions(db: Session, sku_id: str) -> list[ProductVersionOut]:
    rows = (
        db.query(ProductVersion)
        .filter(ProductVersion.sku_id == sku_id)
        .order_by(ProductVersion.version.desc())
        .all()
    )
    out: list[ProductVersionOut] = []
    for r in rows:
        out.append(
            ProductVersionOut(version=r.version, snapshot=json.loads(r.snapshot_json), created_at=r.created_at)
        )
    return out


def update_price(db: Session, redis: Any, sku_id: str, price_cents: int, *, emit_events: bool = True) -> None:
    p = db.query(Product).filter(Product.sku_id == sku_id).first()
    if not p:
        raise CatalogError("not_found")
    p.price_cents = price_cents
    p.version += 1
    db.add(p)
    db.commit()
    db.refresh(p)
    record_version(db, p)
    db.commit()
    cache_service.invalidate_product(redis, sku_id)
    if emit_events:
        publishers.publish_price_changed(redis, {"sku_id": sku_id, "price_cents": price_cents, "version": p.version})
        publishers.publish_synced(redis, {"sku_id": sku_id, "snapshot": _snapshot_product(p)})
        webhook_service.notify_partner(redis, p.partner_id, streams.PRODUCT_PRICE_CHANGED, {"sku_id": sku_id, "price_cents": price_cents})


def deprecate_product(db: Session, redis: Any, sku_id: str, *, emit_events: bool = True) -> None:
    p = db.query(Product).filter(Product.sku_id == sku_id).first()
    if not p:
        raise CatalogError("not_found")
    p.is_active = False
    p.deprecated_at = datetime.now(timezone.utc)
    p.version += 1
    db.add(p)
    db.commit()
    db.refresh(p)
    record_version(db, p)
    db.commit()
    cache_service.invalidate_product(redis, sku_id)
    if emit_events:
        publishers.publish_deprecated(redis, {"sku_id": sku_id})
        publishers.publish_synced(redis, {"sku_id": sku_id, "snapshot": _snapshot_product(p)})
        webhook_service.notify_partner(redis, p.partner_id, streams.PRODUCT_DEPRECATED, {"sku_id": sku_id})


def apply_stream_event(db: Session, event_type: str, payload: dict[str, Any]) -> None:
    if event_type == streams.PRODUCT_CREATED:
        snap = payload.get("snapshot") or payload
        sku_id = snap.get("sku_id")
        if not sku_id or db.query(Product).filter(Product.sku_id == sku_id).first():
            return
        p = Product(
            sku_id=sku_id,
            partner_id=snap["partner_id"],
            partner_sku=snap["partner_sku"],
            name=snap["name"],
            description=snap.get("description"),
            category_id=snap["category_id"],
            price_cents=int(snap["price_cents"]),
            currency=snap.get("currency", "BRL"),
            images=json.dumps(snap.get("images") or []),
            requires_signature=bool(snap.get("requires_signature", False)),
            is_hazardous=bool(snap.get("is_hazardous", False)),
            temperature_zone=snap.get("temperature_zone", "AMBIENT"),
            version=int(snap.get("version", 1)),
            is_active=bool(snap.get("is_active", True)),
        )
        dm = snap.get("dimensions") or {}
        p.dimensions = ProductDimensions(
            id=str(uuid.uuid4()),
            product_sku_id=sku_id,
            width_mm=dm.get("width_mm"),
            height_mm=dm.get("height_mm"),
            depth_mm=dm.get("depth_mm"),
            weight_g=dm.get("weight_g"),
        )
        db.add(p)
        db.commit()
        return
    if event_type == streams.PRODUCT_PRICE_CHANGED:
        sku_id = payload.get("sku_id")
        if not sku_id:
            return
        p = db.query(Product).filter(Product.sku_id == sku_id).first()
        if p:
            p.price_cents = int(payload.get("price_cents", p.price_cents))
            if payload.get("version"):
                p.version = int(payload["version"])
            db.add(p)
            db.commit()
        return
    if event_type == streams.PRODUCT_DEPRECATED:
        sku_id = payload.get("sku_id")
        if not sku_id:
            return
        p = db.query(Product).filter(Product.sku_id == sku_id).first()
        if p:
            p.is_active = False
            db.add(p)
            db.commit()
        return
    if event_type == streams.PRODUCT_SYNCED:
        snap = payload.get("snapshot")
        if isinstance(snap, dict):
            apply_stream_event(db, streams.PRODUCT_CREATED, {"snapshot": snap})


def seed_defaults(db: Session) -> None:
    if db.query(Category).count() == 0:
        db.add_all(
            [
                Category(id="ELECTRONICS_ACCESSORIES", name="Electronics Accessories", is_active=True),
                Category(id="GENERAL", name="General", is_active=True),
            ]
        )
        db.commit()
