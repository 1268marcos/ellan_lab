from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.products_cache import ProductsCache
from app.schemas.order_pickup_product_cache import OrderPickupProductCacheDTO

logger = logging.getLogger(__name__)


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def map_catalog_payload_to_dto(payload: dict[str, Any]) -> OrderPickupProductCacheDTO:
    block = payload.get("order_pickup_cache")
    if not isinstance(block, dict):
        block = payload
    return OrderPickupProductCacheDTO(
        sku_id=str(block.get("sku_id") or payload.get("sku_id")),
        partner_id=block.get("partner_id"),
        partner_sku=block.get("partner_sku"),
        name=str(block.get("name") or ""),
        description=block.get("description"),
        category_id=str(block.get("category_id") or "UNKNOWN"),
        amount_cents=int(block.get("amount_cents") or 0),
        currency=str(block.get("currency") or "BRL"),
        width_mm=block.get("width_mm"),
        height_mm=block.get("height_mm"),
        depth_mm=block.get("depth_mm"),
        weight_g=block.get("weight_g"),
        is_active=bool(block.get("is_active", True)),
        requires_signature=bool(block.get("requires_signature", False)),
        is_hazardous=bool(block.get("is_hazardous", False)),
        temperature_zone=str(block.get("temperature_zone") or "AMBIENT"),
        created_at=_parse_dt(block.get("created_at")),
        updated_at=_parse_dt(block.get("updated_at")),
        synced_at=datetime.now(timezone.utc),
    )


def upsert_products_cache_from_catalog(db: Session, payload: dict[str, Any]) -> ProductsCache:
    dto = map_catalog_payload_to_dto(payload)
    row = db.query(ProductsCache).filter(ProductsCache.sku_id == dto.sku_id).first()
    now = datetime.now(timezone.utc)
    if row is None:
        row = ProductsCache(
            sku_id=dto.sku_id,
            partner_id=dto.partner_id,
            partner_sku=dto.partner_sku,
            name=dto.name,
            description=dto.description,
            category_id=dto.category_id,
            amount_cents=dto.amount_cents,
            currency=dto.currency,
            width_mm=dto.width_mm,
            height_mm=dto.height_mm,
            depth_mm=dto.depth_mm,
            weight_g=dto.weight_g,
            is_active=dto.is_active,
            requires_signature=dto.requires_signature,
            is_hazardous=dto.is_hazardous,
            temperature_zone=dto.temperature_zone,
            payload_json=json.dumps(payload, default=str),
            created_at=dto.created_at or now,
            updated_at=dto.updated_at or now,
            synced_at=dto.synced_at,
        )
        db.add(row)
    else:
        row.partner_id = dto.partner_id
        row.partner_sku = dto.partner_sku
        row.name = dto.name
        row.description = dto.description
        row.category_id = dto.category_id
        row.amount_cents = dto.amount_cents
        row.currency = dto.currency
        row.width_mm = dto.width_mm
        row.height_mm = dto.height_mm
        row.depth_mm = dto.depth_mm
        row.weight_g = dto.weight_g
        row.is_active = dto.is_active
        row.requires_signature = dto.requires_signature
        row.is_hazardous = dto.is_hazardous
        row.temperature_zone = dto.temperature_zone
        row.payload_json = json.dumps(payload, default=str)
        row.updated_at = now
        row.synced_at = dto.synced_at
    db.commit()
    db.refresh(row)
    return row


def apply_stream_event_payload(db: Session, event_type: str, payload: dict[str, Any]) -> None:
    if event_type not in {"product.created", "product.price_changed", "product.deprecated"}:
        logger.info("catalog_sync skip unknown event_type=%s", event_type)
        return
    upsert_products_cache_from_catalog(db, payload)
