from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.core.auth_dep import require_user_roles
from app.core.db import get_db
from app.core.db_migrations import _create_catalog_professional_tables, _create_global_players_registry
from app.core.global_players_partner_link import link_global_players_to_partners, sync_global_players_ecosystem
from app.core.global_players_seed import seed_global_players_registry
from app.data.catalog_global_players import (
    GLOBAL_LOCKER_CATEGORIES,
    PLAYERS_CATALOG,
    WORLD_ATTRIBUTE_DEFS,
    WORLD_CHANNEL_ROTATION,
    WORLD_TAXONOMY_SEED,
    locker_operator_id,
)
from app.data.catalog_players_registry import PLAYER_CAPABILITIES, PLAYER_TYPES, PLAYERS_REGISTRY
from app.schemas.catalog_professional import (
    CHANNEL_CODES,
    TAXONOMY_SCHEMES,
    CatalogProfessionalSeedOut,
    GlobalPlayerDetailOut,
    GlobalPlayerListOut,
    GlobalPlayerOut,
    GlobalPlayersCatalogOut,
    GlobalPlayersSeedOut,
    CategoryEligibilityCreateIn,
    CategoryEligibilityListOut,
    CategoryEligibilityOut,
    EcosystemOverviewOut,
    PlayerIntegrationTargetOut,
    PlayerIntegrationsOut,
    PlayerTypeCountOut,
    CategoryTaxonomyCreateIn,
    CategoryTaxonomyListOut,
    CategoryTaxonomyOut,
    CategoryTaxonomyUpdateIn,
    ProductAttributeDefinitionCreateIn,
    ProductAttributeDefinitionListOut,
    ProductAttributeDefinitionOut,
    ProductAttributeValueListOut,
    ProductAttributeValueOut,
    ProductAttributeValueUpsertIn,
    ProductChannelListingCreateIn,
    ProductChannelListingListOut,
    ProductChannelListingOut,
    ProductChannelListingUpdateIn,
)

router = APIRouter(
    prefix="/catalog-professional",
    tags=["catalog-professional"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao"}))],
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(value: object) -> str:
    if value is None:
        return _utcnow().isoformat()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def _parse_json_obj(raw: object) -> dict:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _parse_json_list(raw: object) -> list[str] | None:
    if raw is None:
        return None
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except json.JSONDecodeError:
            return None
    return None


_CATALOG_TABLES = (
    "category_taxonomy_mappings",
    "product_channel_listings",
    "product_attribute_definitions",
    "product_attribute_values",
)

_GLOBAL_PLAYER_TABLES = ("global_players", "global_player_regions", "global_player_capabilities")


def _ensure_catalog_professional_tables(db: Session) -> None:
    """Cria tabelas do módulo se o serviço subiu antes da migration catalog_professional."""
    bind = db.get_bind()
    if bind.dialect.name == "sqlite":
        return
    inspector = inspect(bind)
    existing = set(inspector.get_table_names())
    if all(t in existing for t in _CATALOG_TABLES):
        return
    conn = db.connection()
    applied: list[str] = []
    _create_catalog_professional_tables(conn, applied)
    if applied:
        db.commit()


def _ensure_global_players_tables(db: Session) -> None:
    bind = db.get_bind()
    if bind.dialect.name == "sqlite":
        return
    inspector = inspect(bind)
    existing = set(inspector.get_table_names())
    if all(t in existing for t in _GLOBAL_PLAYER_TABLES):
        return
    conn = db.connection()
    applied: list[str] = []
    _create_global_players_registry(conn, applied)
    if applied:
        db.commit()


def _global_players_db_ready(db: Session) -> bool:
    if "global_players" not in set(inspect(db.get_bind()).get_table_names()):
        return False
    try:
        db.execute(text("SELECT COUNT(*) FROM global_players"))
        return True
    except ProgrammingError:
        return False


def _player_row_to_out(row: dict, caps: list[str] | None = None, regions: list[str] | None = None) -> GlobalPlayerOut:
    return GlobalPlayerOut(
        code=str(row["code"]),
        name=str(row["name"]),
        player_type=str(row.get("player_type") or row.get("type") or ""),
        country=str(row.get("hq_country") or row.get("country") or ""),
        supports_lockers=bool(row.get("supports_lockers")),
        supports_pudo=bool(row.get("supports_pudo")),
        supports_food_delivery=bool(row.get("supports_food_delivery")),
        supports_marketplace=bool(row.get("supports_marketplace")),
        operator_id=(str(row["operator_id"]) if row.get("operator_id") else None),
        capabilities=caps or [],
        regions=regions or [],
    )


def _registry_player_out(p: dict) -> GlobalPlayerOut:
    code = str(p["code"])
    op = locker_operator_id(code) if (
        p.get("supports_lockers") or p.get("supports_marketplace") or p.get("supports_food")
    ) else None
    return GlobalPlayerOut(
        code=code,
        name=str(p["name"]),
        player_type=str(p["type"]),
        country=str(p["country"]),
        supports_lockers=bool(p.get("supports_lockers")),
        supports_pudo=bool(p.get("supports_pudo")),
        supports_food_delivery=bool(p.get("supports_food")),
        supports_marketplace=bool(p.get("supports_marketplace")),
        operator_id=op,
        capabilities=list(p.get("capabilities") or []),
        regions=list(p.get("regions") or [p["country"]]),
    )


def _query_mappings_or_empty(db: Session, sql: str, params: dict | None = None) -> list:
    _ensure_catalog_professional_tables(db)
    try:
        return db.execute(text(sql), params or {}).mappings().all()
    except ProgrammingError as exc:
        msg = str(exc).lower()
        if "does not exist" in msg or "no such table" in msg:
            _ensure_catalog_professional_tables(db)
            return db.execute(text(sql), params or {}).mappings().all()
        raise


def _ensure_category(db: Session, category_id: str) -> None:
    row = db.execute(
        text("SELECT id FROM product_categories WHERE id = :id LIMIT 1"),
        {"id": category_id},
    ).first()
    if not row:
        raise HTTPException(status_code=422, detail={"type": "CATEGORY_NOT_FOUND", "message": "category_id inválido."})


def _ensure_product(db: Session, product_id: str) -> None:
    row = db.execute(text("SELECT id FROM products WHERE id = :id LIMIT 1"), {"id": product_id}).first()
    if not row:
        raise HTTPException(status_code=422, detail={"type": "PRODUCT_NOT_FOUND", "message": "product_id inválido."})


# --- Taxonomy ---


def _taxonomy_row_to_out(row: dict) -> CategoryTaxonomyOut:
    return CategoryTaxonomyOut(
        id=str(row["id"]),
        category_id=str(row["category_id"]),
        taxonomy_scheme=str(row["taxonomy_scheme"]),
        external_code=str(row["external_code"]),
        external_name=(str(row["external_name"]) if row.get("external_name") else None),
        country_code=(str(row["country_code"]) if row.get("country_code") else None),
        is_primary=bool(row.get("is_primary")),
        metadata_json=_parse_json_obj(row.get("metadata_json")),
        created_at=_to_iso(row.get("created_at")),
        updated_at=_to_iso(row.get("updated_at")),
    )


@router.get("/category-taxonomy", response_model=CategoryTaxonomyListOut)
def list_category_taxonomy(
    category_id: str | None = None,
    taxonomy_scheme: str | None = None,
    db: Session = Depends(get_db),
):
    cond, params = ["1=1"], {}
    if category_id:
        cond.append("category_id = :category_id")
        params["category_id"] = category_id.strip()
    if taxonomy_scheme:
        cond.append("taxonomy_scheme = :taxonomy_scheme")
        params["taxonomy_scheme"] = taxonomy_scheme.strip().upper()
    rows = _query_mappings_or_empty(
        db,
        f"""
            SELECT * FROM category_taxonomy_mappings
            WHERE {' AND '.join(cond)}
            ORDER BY category_id, taxonomy_scheme, is_primary DESC
        """,
        params,
    )
    return CategoryTaxonomyListOut(ok=True, items=[_taxonomy_row_to_out(dict(r)) for r in rows])


@router.post("/category-taxonomy", response_model=CategoryTaxonomyOut)
def create_category_taxonomy(payload: CategoryTaxonomyCreateIn, db: Session = Depends(get_db)):
    scheme = str(payload.taxonomy_scheme).strip().upper()
    if scheme not in TAXONOMY_SCHEMES:
        raise HTTPException(status_code=422, detail={"type": "INVALID_TAXONOMY_SCHEME", "allowed": sorted(TAXONOMY_SCHEMES)})
    _ensure_category(db, payload.category_id)
    row_id = str(uuid4())
    meta = json.dumps(payload.metadata_json if isinstance(payload.metadata_json, dict) else {})
    if payload.is_primary:
        db.execute(
            text(
                "UPDATE category_taxonomy_mappings SET is_primary = FALSE WHERE category_id = :cid AND taxonomy_scheme = :sch"
            ),
            {"cid": payload.category_id, "sch": scheme},
        )
    db.execute(
        text(
            """
            INSERT INTO category_taxonomy_mappings (
                id, category_id, taxonomy_scheme, external_code, external_name,
                country_code, is_primary, metadata_json, created_at, updated_at
            ) VALUES (
                :id, :category_id, :taxonomy_scheme, :external_code, :external_name,
                :country_code, :is_primary, :metadata_json, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "id": row_id,
            "category_id": payload.category_id.strip(),
            "taxonomy_scheme": scheme,
            "external_code": payload.external_code.strip(),
            "external_name": payload.external_name,
            "country_code": (payload.country_code.strip().upper() if payload.country_code else None),
            "is_primary": bool(payload.is_primary),
            "metadata_json": meta,
        },
    )
    db.commit()
    row = db.execute(text("SELECT * FROM category_taxonomy_mappings WHERE id = :id"), {"id": row_id}).mappings().first()
    return _taxonomy_row_to_out(dict(row or {}))


@router.patch("/category-taxonomy/{row_id}", response_model=CategoryTaxonomyOut)
def update_category_taxonomy(row_id: str, payload: CategoryTaxonomyUpdateIn, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT * FROM category_taxonomy_mappings WHERE id = :id"), {"id": row_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "TAXONOMY_NOT_FOUND"})
    if payload.is_primary:
        db.execute(
            text(
                "UPDATE category_taxonomy_mappings SET is_primary = FALSE "
                "WHERE category_id = :cid AND taxonomy_scheme = :sch AND id != :id"
            ),
            {"cid": row["category_id"], "sch": row["taxonomy_scheme"], "id": row_id},
        )
    db.execute(
        text(
            """
            UPDATE category_taxonomy_mappings SET
                external_code = COALESCE(:external_code, external_code),
                external_name = COALESCE(:external_name, external_name),
                country_code = COALESCE(:country_code, country_code),
                is_primary = COALESCE(:is_primary, is_primary),
                metadata_json = COALESCE(:metadata_json, metadata_json),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        ),
        {
            "id": row_id,
            "external_code": payload.external_code.strip() if payload.external_code else None,
            "external_name": payload.external_name,
            "country_code": payload.country_code,
            "is_primary": payload.is_primary,
            "metadata_json": json.dumps(payload.metadata_json) if payload.metadata_json is not None else None,
        },
    )
    db.commit()
    row2 = db.execute(text("SELECT * FROM category_taxonomy_mappings WHERE id = :id"), {"id": row_id}).mappings().first()
    return _taxonomy_row_to_out(dict(row2 or {}))


@router.delete("/category-taxonomy/{row_id}")
def delete_category_taxonomy(row_id: str, db: Session = Depends(get_db)):
    res = db.execute(text("DELETE FROM category_taxonomy_mappings WHERE id = :id"), {"id": row_id})
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail={"type": "TAXONOMY_NOT_FOUND"})
    return {"ok": True, "id": row_id}


# --- Channel listings ---


def _channel_row_to_out(row: dict) -> ProductChannelListingOut:
    return ProductChannelListingOut(
        id=str(row["id"]),
        product_id=str(row["product_id"]),
        channel_code=str(row["channel_code"]),
        external_sku=(str(row["external_sku"]) if row.get("external_sku") else None),
        external_category_id=(str(row["external_category_id"]) if row.get("external_category_id") else None),
        listing_status=str(row.get("listing_status") or "DRAFT"),
        price_cents=(int(row["price_cents"]) if row.get("price_cents") is not None else None),
        currency=str(row.get("currency") or "BRL"),
        partner_id=(str(row["partner_id"]) if row.get("partner_id") else None),
        sync_mode=str(row.get("sync_mode") or "MANUAL"),
        last_synced_at=_to_iso(row["last_synced_at"]) if row.get("last_synced_at") else None,
        metadata_json=_parse_json_obj(row.get("metadata_json")),
        created_at=_to_iso(row.get("created_at")),
        updated_at=_to_iso(row.get("updated_at")),
    )


@router.get("/channel-listings", response_model=ProductChannelListingListOut)
def list_channel_listings(
    product_id: str | None = None,
    channel_code: str | None = None,
    listing_status: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    cond, params = ["1=1"], {"limit": limit, "offset": offset}
    if product_id:
        cond.append("product_id = :product_id")
        params["product_id"] = product_id.strip()
    if channel_code:
        cond.append("channel_code = :channel_code")
        params["channel_code"] = channel_code.strip().upper()
    if listing_status:
        cond.append("listing_status = :listing_status")
        params["listing_status"] = listing_status.strip().upper()
    _ensure_catalog_professional_tables(db)
    total = int(
        db.execute(
            text(f"SELECT COUNT(*) FROM product_channel_listings WHERE {' AND '.join(cond)}"),
            {k: v for k, v in params.items() if k not in ("limit", "offset")},
        ).scalar()
        or 0
    )
    rows = _query_mappings_or_empty(
        db,
        f"""
            SELECT * FROM product_channel_listings
            WHERE {' AND '.join(cond)}
            ORDER BY updated_at DESC
            LIMIT :limit OFFSET :offset
        """,
        params,
    )
    return ProductChannelListingListOut(
        ok=True,
        total=total,
        items=[_channel_row_to_out(dict(r)) for r in rows],
    )


@router.post("/channel-listings", response_model=ProductChannelListingOut)
def create_channel_listing(payload: ProductChannelListingCreateIn, db: Session = Depends(get_db)):
    channel = str(payload.channel_code).strip().upper()
    if channel not in CHANNEL_CODES:
        raise HTTPException(status_code=422, detail={"type": "INVALID_CHANNEL_CODE", "allowed": sorted(CHANNEL_CODES)})
    _ensure_product(db, payload.product_id)
    row_id = str(uuid4())
    status = str(payload.listing_status or "DRAFT").strip().upper()
    db.execute(
        text(
            """
            INSERT INTO product_channel_listings (
                id, product_id, channel_code, external_sku, external_category_id,
                listing_status, price_cents, currency, partner_id, sync_mode,
                metadata_json, created_at, updated_at
            ) VALUES (
                :id, :product_id, :channel_code, :external_sku, :external_category_id,
                :listing_status, :price_cents, :currency, :partner_id, :sync_mode,
                :metadata_json, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "id": row_id,
            "product_id": payload.product_id.strip(),
            "channel_code": channel,
            "external_sku": payload.external_sku,
            "external_category_id": payload.external_category_id,
            "listing_status": status,
            "price_cents": payload.price_cents,
            "currency": (payload.currency or "BRL")[:8],
            "partner_id": payload.partner_id,
            "sync_mode": (payload.sync_mode or "MANUAL").upper(),
            "metadata_json": json.dumps(payload.metadata_json if isinstance(payload.metadata_json, dict) else {}),
        },
    )
    db.commit()
    row = db.execute(text("SELECT * FROM product_channel_listings WHERE id = :id"), {"id": row_id}).mappings().first()
    return _channel_row_to_out(dict(row or {}))


@router.patch("/channel-listings/{row_id}", response_model=ProductChannelListingOut)
def update_channel_listing(row_id: str, payload: ProductChannelListingUpdateIn, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT * FROM product_channel_listings WHERE id = :id"), {"id": row_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "CHANNEL_LISTING_NOT_FOUND"})
    db.execute(
        text(
            """
            UPDATE product_channel_listings SET
                external_sku = COALESCE(:external_sku, external_sku),
                external_category_id = COALESCE(:external_category_id, external_category_id),
                listing_status = COALESCE(:listing_status, listing_status),
                price_cents = COALESCE(:price_cents, price_cents),
                currency = COALESCE(:currency, currency),
                partner_id = COALESCE(:partner_id, partner_id),
                sync_mode = COALESCE(:sync_mode, sync_mode),
                metadata_json = COALESCE(:metadata_json, metadata_json),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """
        ),
        {
            "id": row_id,
            "external_sku": payload.external_sku,
            "external_category_id": payload.external_category_id,
            "listing_status": payload.listing_status.upper() if payload.listing_status else None,
            "price_cents": payload.price_cents,
            "currency": payload.currency,
            "partner_id": payload.partner_id,
            "sync_mode": payload.sync_mode.upper() if payload.sync_mode else None,
            "metadata_json": json.dumps(payload.metadata_json) if payload.metadata_json is not None else None,
        },
    )
    db.commit()
    row2 = db.execute(text("SELECT * FROM product_channel_listings WHERE id = :id"), {"id": row_id}).mappings().first()
    return _channel_row_to_out(dict(row2 or {}))


@router.delete("/channel-listings/{row_id}")
def delete_channel_listing(row_id: str, db: Session = Depends(get_db)):
    res = db.execute(text("DELETE FROM product_channel_listings WHERE id = :id"), {"id": row_id})
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail={"type": "CHANNEL_LISTING_NOT_FOUND"})
    return {"ok": True, "id": row_id}


# --- Attribute definitions & values ---


@router.get("/attribute-definitions", response_model=ProductAttributeDefinitionListOut)
def list_attribute_definitions(category_id: str | None = None, db: Session = Depends(get_db)):
    if category_id:
        rows = _query_mappings_or_empty(
            db,
            """
                SELECT * FROM product_attribute_definitions
                WHERE category_id = :cid OR category_id IS NULL
                ORDER BY sort_order, attr_key
            """,
            {"cid": category_id.strip()},
        )
    else:
        rows = _query_mappings_or_empty(
            db,
            "SELECT * FROM product_attribute_definitions ORDER BY category_id NULLS LAST, sort_order, attr_key",
        )
    items = [
        ProductAttributeDefinitionOut(
            id=str(r["id"]),
            category_id=(str(r["category_id"]) if r.get("category_id") else None),
            attr_key=str(r["attr_key"]),
            attr_label=str(r["attr_label"]),
            data_type=str(r["data_type"]),
            enum_values_json=_parse_json_list(r.get("enum_values_json")),
            is_required=bool(r.get("is_required")),
            sort_order=int(r.get("sort_order") or 0),
            created_at=_to_iso(r.get("created_at")),
        )
        for r in rows
    ]
    return ProductAttributeDefinitionListOut(ok=True, items=items)


@router.post("/attribute-definitions", response_model=ProductAttributeDefinitionOut)
def create_attribute_definition(payload: ProductAttributeDefinitionCreateIn, db: Session = Depends(get_db)):
    if payload.category_id:
        _ensure_category(db, payload.category_id)
    row_id = str(uuid4())
    enum_json = json.dumps(payload.enum_values) if payload.enum_values else None
    db.execute(
        text(
            """
            INSERT INTO product_attribute_definitions (
                id, category_id, attr_key, attr_label, data_type,
                enum_values_json, is_required, sort_order, created_at
            ) VALUES (
                :id, :category_id, :attr_key, :attr_label, :data_type,
                :enum_values_json, :is_required, :sort_order, CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "id": row_id,
            "category_id": payload.category_id.strip() if payload.category_id else None,
            "attr_key": payload.attr_key.strip(),
            "attr_label": payload.attr_label.strip(),
            "data_type": payload.data_type.upper(),
            "enum_values_json": enum_json,
            "is_required": bool(payload.is_required),
            "sort_order": int(payload.sort_order),
        },
    )
    db.commit()
    row = db.execute(text("SELECT * FROM product_attribute_definitions WHERE id = :id"), {"id": row_id}).mappings().first()
    r = dict(row or {})
    return ProductAttributeDefinitionOut(
        id=row_id,
        category_id=r.get("category_id"),
        attr_key=str(r.get("attr_key")),
        attr_label=str(r.get("attr_label")),
        data_type=str(r.get("data_type")),
        enum_values_json=_parse_json_list(r.get("enum_values_json")),
        is_required=bool(r.get("is_required")),
        sort_order=int(r.get("sort_order") or 0),
        created_at=_to_iso(r.get("created_at")),
    )


@router.get("/products/{product_id}/attributes", response_model=ProductAttributeValueListOut)
def list_product_attributes(product_id: str, db: Session = Depends(get_db)):
    _ensure_product(db, product_id)
    rows = db.execute(
        text(
            """
            SELECT v.*, d.attr_key, d.attr_label
            FROM product_attribute_values v
            JOIN product_attribute_definitions d ON d.id = v.definition_id
            WHERE v.product_id = :pid
            ORDER BY d.sort_order, d.attr_key
            """
        ),
        {"pid": product_id},
    ).mappings().all()
    items = [
        ProductAttributeValueOut(
            id=str(r["id"]),
            product_id=product_id,
            definition_id=str(r["definition_id"]),
            attr_key=str(r.get("attr_key") or ""),
            attr_label=str(r.get("attr_label") or ""),
            value_text=(str(r["value_text"]) if r.get("value_text") is not None else None),
            value_number=(float(r["value_number"]) if r.get("value_number") is not None else None),
            value_bool=(bool(r["value_bool"]) if r.get("value_bool") is not None else None),
            updated_at=_to_iso(r.get("updated_at")),
        )
        for r in rows
    ]
    return ProductAttributeValueListOut(ok=True, items=items)


@router.put("/products/{product_id}/attributes", response_model=ProductAttributeValueOut)
def upsert_product_attribute(product_id: str, payload: ProductAttributeValueUpsertIn, db: Session = Depends(get_db)):
    _ensure_product(db, product_id)
    def_row = db.execute(
        text("SELECT id, attr_key, attr_label FROM product_attribute_definitions WHERE id = :id"),
        {"id": payload.definition_id},
    ).mappings().first()
    if not def_row:
        raise HTTPException(status_code=404, detail={"type": "ATTR_DEFINITION_NOT_FOUND"})
    existing = db.execute(
        text(
            "SELECT id FROM product_attribute_values WHERE product_id = :pid AND definition_id = :did"
        ),
        {"pid": product_id, "did": payload.definition_id},
    ).mappings().first()
    if existing:
        db.execute(
            text(
                """
                UPDATE product_attribute_values SET
                    value_text = :value_text,
                    value_number = :value_number,
                    value_bool = :value_bool,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            {
                "id": existing["id"],
                "value_text": payload.value_text,
                "value_number": payload.value_number,
                "value_bool": payload.value_bool,
            },
        )
        row_id = str(existing["id"])
    else:
        row_id = str(uuid4())
        db.execute(
            text(
                """
                INSERT INTO product_attribute_values (
                    id, product_id, definition_id, value_text, value_number, value_bool,
                    created_at, updated_at
                ) VALUES (
                    :id, :pid, :did, :value_text, :value_number, :value_bool,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                """
            ),
            {
                "id": row_id,
                "pid": product_id,
                "did": payload.definition_id,
                "value_text": payload.value_text,
                "value_number": payload.value_number,
                "value_bool": payload.value_bool,
            },
        )
    db.commit()
    return ProductAttributeValueOut(
        id=row_id,
        product_id=product_id,
        definition_id=payload.definition_id,
        attr_key=str(def_row.get("attr_key")),
        attr_label=str(def_row.get("attr_label")),
        value_text=payload.value_text,
        value_number=payload.value_number,
        value_bool=payload.value_bool,
        updated_at=_utcnow().isoformat(),
    )


def _ensure_global_locker_categories(db: Session) -> int:
    """Insere categorias locker-specific se ainda não existirem."""
    bind = db.get_bind()
    col_names = {c["name"] for c in inspect(bind).get_columns("product_categories")}
    created = 0
    for cat in GLOBAL_LOCKER_CATEGORIES:
        exists = db.execute(
            text("SELECT 1 FROM product_categories WHERE id = :id LIMIT 1"),
            {"id": cat["id"]},
        ).scalar()
        if exists:
            continue
        if "description" in col_names and "default_temperature_zone" in col_names:
            db.execute(
                text(
                    """
                    INSERT INTO product_categories (
                        id, name, description, default_temperature_zone, default_security_level,
                        is_hazardous, requires_age_verification, created_at, updated_at
                    ) VALUES (
                        :id, :name, :description, :temp, :sec, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    """
                ),
                {
                    "id": cat["id"],
                    "name": cat["name"],
                    "description": cat.get("description"),
                    "temp": cat.get("default_temperature_zone", "AMBIENT"),
                    "sec": cat.get("default_security_level", "STANDARD"),
                },
            )
        else:
            db.execute(
                text("INSERT INTO product_categories (id, name) VALUES (:id, :name)"),
                {"id": cat["id"], "name": cat["name"]},
            )
        created += 1
    return created


@router.get("/players-reference", response_model=GlobalPlayersCatalogOut)
def get_players_reference(db: Session = Depends(get_db)):
    """Catálogo de players para UI — DB global_players se populado, senão registo em código."""
    _ensure_global_players_tables(db)
    count = 0
    if _global_players_db_ready(db):
        count = int(db.execute(text("SELECT COUNT(*) FROM global_players")).scalar() or 0)
    if count > 0:
        rows = db.execute(
            text(
                """
                SELECT code, name, player_type, hq_country, supports_lockers, supports_pudo,
                       supports_food_delivery, supports_marketplace, operator_id
                FROM global_players WHERE active = TRUE ORDER BY player_type, name
                """
            )
        ).mappings().all()
        players = []
        for r in rows:
            code = str(r["code"])
            caps = [
                str(x["capability"])
                for x in db.execute(
                    text(
                        "SELECT capability FROM global_player_capabilities WHERE player_code = :c ORDER BY capability"
                    ),
                    {"c": code},
                ).mappings().all()
            ]
            regions = [
                str(x["country_code"])
                for x in db.execute(
                    text(
                        "SELECT country_code FROM global_player_regions WHERE player_code = :c ORDER BY country_code"
                    ),
                    {"c": code},
                ).mappings().all()
            ]
            players.append(_player_row_to_out(dict(r), caps, regions))
        source = "database"
    else:
        players = [_registry_player_out(p) for p in PLAYERS_REGISTRY]
        source = "registry"
    return GlobalPlayersCatalogOut(
        ok=True,
        taxonomy_schemes=sorted(TAXONOMY_SCHEMES),
        channel_codes=sorted(CHANNEL_CODES),
        player_types=sorted(PLAYER_TYPES),
        capabilities=sorted(PLAYER_CAPABILITIES),
        players=players,
        source=source,
    )


@router.get("/global-players", response_model=GlobalPlayerListOut)
def list_global_players(
    player_type: str | None = None,
    country: str | None = None,
    capability: str | None = None,
    supports_lockers: bool | None = None,
    q: str | None = None,
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    _ensure_global_players_tables(db)
    if not _global_players_db_ready(db) or not (db.execute(text("SELECT COUNT(*) FROM global_players")).scalar() or 0):
        items = [_registry_player_out(p) for p in PLAYERS_REGISTRY]
        if player_type:
            items = [i for i in items if i.player_type == player_type.strip().upper()]
        if country:
            cc = country.strip().upper()
            items = [i for i in items if cc in i.regions or i.country == cc]
        if capability:
            cap = capability.strip().upper()
            items = [i for i in items if cap in i.capabilities]
        if supports_lockers is not None:
            items = [i for i in items if i.supports_lockers == supports_lockers]
        if q:
            needle = q.strip().lower()
            items = [i for i in items if needle in i.code.lower() or needle in i.name.lower()]
        return GlobalPlayerListOut(ok=True, total=len(items), items=items[:limit])

    cond, params = ["active = TRUE"], {}
    if player_type:
        cond.append("player_type = :ptype")
        params["ptype"] = player_type.strip().upper()
    if country:
        cond.append(
            "EXISTS (SELECT 1 FROM global_player_regions gpr "
            "WHERE gpr.player_code = global_players.code AND gpr.country_code = :cc)"
        )
        params["cc"] = country.strip().upper()[:3]
    if capability:
        cond.append(
            "EXISTS (SELECT 1 FROM global_player_capabilities gpc "
            "WHERE gpc.player_code = global_players.code AND gpc.capability = :cap)"
        )
        params["cap"] = capability.strip().upper()
    if supports_lockers is not None:
        cond.append("supports_lockers = :sl")
        params["sl"] = supports_lockers
    if q:
        cond.append("(LOWER(code) LIKE :q OR LOWER(name) LIKE :q)")
        params["q"] = f"%{q.strip().lower()}%"

    rows = db.execute(
        text(
            f"""
            SELECT code, name, player_type, hq_country, supports_lockers, supports_pudo,
                   supports_food_delivery, supports_marketplace, operator_id
            FROM global_players
            WHERE {' AND '.join(cond)}
            ORDER BY player_type, name
            LIMIT :lim
            """
        ),
        {**params, "lim": limit},
    ).mappings().all()
    items = []
    for r in rows:
        code = str(r["code"])
        caps = [
            str(x["capability"])
            for x in db.execute(
                text("SELECT capability FROM global_player_capabilities WHERE player_code = :c"),
                {"c": code},
            ).mappings().all()
        ]
        regions = [
            str(x["country_code"])
            for x in db.execute(
                text("SELECT country_code FROM global_player_regions WHERE player_code = :c"),
                {"c": code},
            ).mappings().all()
        ]
        items.append(_player_row_to_out(dict(r), caps, regions))
    total = db.execute(
        text(f"SELECT COUNT(*) FROM global_players WHERE {' AND '.join(cond)}"),
        params,
    ).scalar()
    return GlobalPlayerListOut(ok=True, total=int(total or 0), items=items)


@router.get("/global-players/{player_code}", response_model=GlobalPlayerDetailOut)
def get_global_player(player_code: str, db: Session = Depends(get_db)):
    code = player_code.strip().upper()
    _ensure_global_players_tables(db)
    row = db.execute(
        text("SELECT * FROM global_players WHERE code = :c LIMIT 1"),
        {"c": code},
    ).mappings().first()
    if not row:
        reg = next((p for p in PLAYERS_REGISTRY if p["code"] == code), None)
        if not reg:
            raise HTTPException(status_code=404, detail={"type": "PLAYER_NOT_FOUND", "message": code})
        base = _registry_player_out(reg)
        return GlobalPlayerDetailOut(**base.model_dump(), integration_modes=list(reg.get("integration_modes") or []))
    caps = [
        str(x["capability"])
        for x in db.execute(
            text("SELECT capability FROM global_player_capabilities WHERE player_code = :c"),
            {"c": code},
        ).mappings().all()
    ]
    regions = [
        str(x["country_code"])
        for x in db.execute(
            text("SELECT country_code FROM global_player_regions WHERE player_code = :c"),
            {"c": code},
        ).mappings().all()
    ]
    elig = [
        {"category_id": str(e["category_id"]), "eligibility": str(e["eligibility"])}
        for e in db.execute(
            text(
                "SELECT category_id, eligibility FROM category_player_eligibility WHERE player_code = :c"
            ),
            {"c": code},
        ).mappings().all()
    ]
    base = _player_row_to_out(dict(row), caps, regions)
    modes = _parse_json_list(row.get("integration_modes_json")) or []
    return GlobalPlayerDetailOut(**base.model_dump(), integration_modes=modes, eligibility=elig)


@router.post("/global-players/seed", response_model=GlobalPlayersSeedOut)
def seed_global_players(db: Session = Depends(get_db)):
    """Persiste registo mundial + operadores OP-{code} + parceiros + ligações."""
    _ensure_global_players_tables(db)
    counts = seed_global_players_registry(db, sync_ecosystem=True)
    return GlobalPlayersSeedOut(ok=True, **counts)


@router.post("/global-players/sync-partners")
def sync_global_players_partners(db: Session = Depends(get_db)):
    """Religa parceiros existentes e cria operadores em falta (sem re-seed completo)."""
    _ensure_global_players_tables(db)
    if not _global_players_db_ready(db):
        raise HTTPException(
            status_code=422,
            detail={"type": "GLOBAL_PLAYERS_EMPTY", "message": "Execute POST /global-players/seed primeiro."},
        )
    return {"ok": True, **sync_global_players_ecosystem(db)}


@router.post("/global-players/link-partners")
def link_partners_only(db: Session = Depends(get_db)):
    """Apenas liga ecommerce_partners / logistics_partners já existentes."""
    _ensure_global_players_tables(db)
    return {"ok": True, **link_global_players_to_partners(db)}


def _safe_scalar(db: Session, sql: str, params: dict | None = None) -> int:
    try:
        return int(db.execute(text(sql), params or {}).scalar() or 0)
    except (ProgrammingError, OperationalError):
        return 0


@router.get("/ecosystem-overview", response_model=EcosystemOverviewOut)
def ecosystem_overview(db: Session = Depends(get_db)):
    """Painel executivo: cobertura mundial, integrações e readiness locker."""
    if db.get_bind().dialect.name != "sqlite":
        _ensure_catalog_professional_tables(db)
        _ensure_global_players_tables(db)
    source = "registry"
    players_total = len(PLAYERS_REGISTRY)
    players_locker = sum(
        1
        for p in PLAYERS_REGISTRY
        if p.get("supports_lockers") or p.get("supports_pudo") or p.get("supports_marketplace")
    )
    top_players = [_registry_player_out(p) for p in PLAYERS_REGISTRY[:12]]
    by_type: dict[str, int] = {}
    for p in PLAYERS_REGISTRY:
        t = str(p.get("type") or "OTHER")
        by_type[t] = by_type.get(t, 0) + 1

    if _global_players_db_ready(db):
        source = "database"
        players_total = _safe_scalar(db, "SELECT COUNT(*) FROM global_players WHERE active = TRUE")
        players_locker = _safe_scalar(
            db,
            """
            SELECT COUNT(*) FROM global_players
            WHERE active = TRUE AND (
                supports_lockers = TRUE OR supports_pudo = TRUE
                OR supports_marketplace = TRUE OR supports_food_delivery = TRUE
            )
            """,
        )
        rows = db.execute(
            text(
                """
                SELECT player_type, COUNT(*) AS cnt FROM global_players
                WHERE active = TRUE GROUP BY player_type ORDER BY cnt DESC
                """
            )
        ).mappings().all()
        by_type = {str(r["player_type"]): int(r["cnt"]) for r in rows}
        top_rows = db.execute(
            text(
                """
                SELECT code, name, player_type, hq_country, supports_lockers, supports_pudo,
                       supports_food_delivery, supports_marketplace, operator_id
                FROM global_players WHERE active = TRUE
                ORDER BY supports_lockers DESC, name LIMIT 12
                """
            )
        ).mappings().all()
        top_players = [_player_row_to_out(dict(r)) for r in top_rows]

    locker_cat_n = sum(
        1
        for c in GLOBAL_LOCKER_CATEGORIES
        if db.execute(
            text("SELECT 1 FROM product_categories WHERE id = :id"),
            {"id": c["id"]},
        ).scalar()
    )

    return EcosystemOverviewOut(
        ok=True,
        source=source,
        players_total=players_total,
        players_locker_ready=players_locker,
        taxonomy_mappings=_safe_scalar(db, "SELECT COUNT(*) FROM category_taxonomy_mappings"),
        channel_listings=_safe_scalar(db, "SELECT COUNT(*) FROM product_channel_listings"),
        eligibility_rules=_safe_scalar(db, "SELECT COUNT(*) FROM category_player_eligibility"),
        integration_targets=_safe_scalar(db, "SELECT COUNT(*) FROM global_player_integration_targets"),
        ecommerce_partner_links=_safe_scalar(
            db,
            "SELECT COUNT(*) FROM global_player_integration_targets WHERE target_type = 'ECOMMERCE_PARTNER'",
        ),
        logistics_partner_links=_safe_scalar(
            db,
            "SELECT COUNT(*) FROM global_player_integration_targets WHERE target_type = 'LOGISTICS_PARTNER'",
        ),
        locker_operators_total=_safe_scalar(db, "SELECT COUNT(*) FROM locker_operators"),
        locker_categories_global=locker_cat_n,
        players_by_type=[PlayerTypeCountOut(player_type=k, count=v) for k, v in sorted(by_type.items())],
        top_players=top_players,
    )


@router.get("/category-eligibility", response_model=CategoryEligibilityListOut)
def list_category_eligibility(
    category_id: str | None = None,
    player_code: str | None = None,
    db: Session = Depends(get_db),
):
    _ensure_global_players_tables(db)
    if not _global_players_db_ready(db):
        return CategoryEligibilityListOut(ok=True, total=0, items=[])

    cond, params = ["1=1"], {}
    if category_id:
        cond.append("e.category_id = :cid")
        params["cid"] = category_id.strip()
    if player_code:
        cond.append("e.player_code = :pc")
        params["pc"] = player_code.strip().upper()

    rows = db.execute(
        text(
            f"""
            SELECT e.id, e.category_id, e.player_code, e.eligibility, e.notes, e.created_at,
                   c.name AS category_name, p.name AS player_name
            FROM category_player_eligibility e
            LEFT JOIN product_categories c ON c.id = e.category_id
            LEFT JOIN global_players p ON p.code = e.player_code
            WHERE {' AND '.join(cond)}
            ORDER BY e.category_id, e.eligibility, e.player_code
            """
        ),
        params,
    ).mappings().all()
    items = [
        CategoryEligibilityOut(
            id=str(r["id"]),
            category_id=str(r["category_id"]),
            category_name=(str(r["category_name"]) if r.get("category_name") else None),
            player_code=str(r["player_code"]),
            player_name=(str(r["player_name"]) if r.get("player_name") else None),
            eligibility=str(r["eligibility"]),
            notes=(str(r["notes"]) if r.get("notes") else None),
            created_at=_to_iso(r.get("created_at")),
        )
        for r in rows
    ]
    return CategoryEligibilityListOut(ok=True, total=len(items), items=items)


@router.post("/category-eligibility", response_model=CategoryEligibilityOut)
def create_category_eligibility(payload: CategoryEligibilityCreateIn, db: Session = Depends(get_db)):
    _ensure_global_players_tables(db)
    if not _global_players_db_ready(db):
        raise HTTPException(status_code=422, detail={"type": "GLOBAL_PLAYERS_REQUIRED", "message": "Execute seed global players."})
    elig = str(payload.eligibility).strip().upper()
    if elig not in {"ALLOWED", "PREFERRED", "RESTRICTED"}:
        raise HTTPException(status_code=422, detail={"type": "INVALID_ELIGIBILITY"})
    pc = payload.player_code.strip().upper()
    if not db.execute(text("SELECT 1 FROM global_players WHERE code = :c"), {"c": pc}).scalar():
        raise HTTPException(status_code=422, detail={"type": "PLAYER_NOT_FOUND", "message": pc})
    if not db.execute(
        text("SELECT 1 FROM product_categories WHERE id = :id"),
        {"id": payload.category_id},
    ).scalar():
        raise HTTPException(status_code=422, detail={"type": "CATEGORY_NOT_FOUND"})
    row_id = str(uuid4())
    db.execute(
        text(
            """
            INSERT INTO category_player_eligibility (
                id, category_id, player_code, eligibility, notes, created_at
            ) VALUES (:id, :cat, :pc, :elig, :notes, CURRENT_TIMESTAMP)
            """
        ),
        {
            "id": row_id,
            "cat": payload.category_id,
            "pc": pc,
            "elig": elig,
            "notes": payload.notes,
        },
    )
    db.commit()
    return CategoryEligibilityOut(
        id=row_id,
        category_id=payload.category_id,
        player_code=pc,
        eligibility=elig,
        notes=payload.notes,
        created_at=_utcnow().isoformat(),
    )


@router.get("/global-players/{player_code}/integrations", response_model=PlayerIntegrationsOut)
def list_player_integrations(player_code: str, db: Session = Depends(get_db)):
    code = player_code.strip().upper()
    _ensure_global_players_tables(db)
    if not _global_players_db_ready(db):
        return PlayerIntegrationsOut(ok=True, player_code=code, items=[])
    rows = db.execute(
        text(
            """
            SELECT target_type, target_key, metadata_json
            FROM global_player_integration_targets
            WHERE player_code = :c ORDER BY target_type, target_key
            """
        ),
        {"c": code},
    ).mappings().all()
    return PlayerIntegrationsOut(
        ok=True,
        player_code=code,
        items=[
            PlayerIntegrationTargetOut(
                target_type=str(r["target_type"]),
                target_key=str(r["target_key"]),
                metadata_json=_parse_json_obj(r.get("metadata_json")),
            )
            for r in rows
        ],
    )


@router.post("/seed", response_model=CatalogProfessionalSeedOut)
def seed_catalog_professional(db: Session = Depends(get_db)):
    """Seed mundial: players, taxonomias, atributos PIM e listings demo."""
    _ensure_catalog_professional_tables(db)
    _ensure_global_players_tables(db)
    gp_counts = None
    if _global_players_db_ready(db) or (
        "global_players" in set(inspect(db.get_bind()).get_table_names())
    ):
        gp_counts = seed_global_players_registry(db, sync_ecosystem=True)
    locker_cat_n = _ensure_global_locker_categories(db)
    taxonomy_seed = WORLD_TAXONOMY_SEED
    tax_n = 0
    for cat_id, scheme, code, name, country, primary in taxonomy_seed:
        exists = db.execute(
            text(
                "SELECT 1 FROM category_taxonomy_mappings "
                "WHERE category_id = :c AND taxonomy_scheme = :s AND external_code = :e LIMIT 1"
            ),
            {"c": cat_id, "s": scheme, "e": code},
        ).scalar()
        if exists:
            continue
        if not db.execute(text("SELECT 1 FROM product_categories WHERE id = :id"), {"id": cat_id}).scalar():
            continue
        db.execute(
            text(
                """
                INSERT INTO category_taxonomy_mappings (
                    id, category_id, taxonomy_scheme, external_code, external_name,
                    country_code, is_primary, metadata_json, created_at, updated_at
                ) VALUES (
                    :id, :cid, :sch, :code, :name, :country, :primary, '{}',
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                """
            ),
            {
                "id": str(uuid4()),
                "cid": cat_id,
                "sch": scheme,
                "code": code,
                "name": name,
                "country": country,
                "primary": primary,
            },
        )
        tax_n += 1

    attr_defs = [
        ("ELECTRONICS", "brand", "Marca", "STRING", None, True, 10),
        ("ELECTRONICS", "warranty_months", "Garantia (meses)", "INTEGER", None, False, 20),
        ("FASHION", "size", "Tamanho", "ENUM", ["PP", "P", "M", "G", "GG"], True, 10),
        ("FASHION", "color", "Cor", "STRING", None, False, 20),
        ("PHARMACY_OTC_MEDS", "requires_prescription", "Receita", "BOOLEAN", None, True, 5),
        *WORLD_ATTRIBUTE_DEFS,
    ]
    attr_n = 0
    for cat_id, key, label, dtype, enum_vals, required, sort_o in attr_defs:
        if not db.execute(text("SELECT 1 FROM product_categories WHERE id = :id"), {"id": cat_id}).scalar():
            continue
        exists = db.execute(
            text("SELECT 1 FROM product_attribute_definitions WHERE category_id = :c AND attr_key = :k"),
            {"c": cat_id, "k": key},
        ).scalar()
        if exists:
            continue
        db.execute(
            text(
                """
                INSERT INTO product_attribute_definitions (
                    id, category_id, attr_key, attr_label, data_type,
                    enum_values_json, is_required, sort_order, created_at
                ) VALUES (
                    :id, :cid, :key, :label, :dtype, :enum, :req, :sort, CURRENT_TIMESTAMP
                )
                """
            ),
            {
                "id": str(uuid4()),
                "cid": cat_id,
                "key": key,
                "label": label,
                "dtype": dtype,
                "enum": json.dumps(enum_vals) if enum_vals else None,
                "req": required,
                "sort": sort_o,
            },
        )
        attr_n += 1

    channel_n = 0
    products = db.execute(text("SELECT id, amount_cents FROM products ORDER BY id DESC LIMIT 12")).mappings().all()
    channels = WORLD_CHANNEL_ROTATION
    for idx, prod in enumerate(products):
        ch = channels[idx % len(channels)]
        exists = db.execute(
            text("SELECT 1 FROM product_channel_listings WHERE product_id = :p AND channel_code = :c"),
            {"p": prod["id"], "c": ch},
        ).scalar()
        if exists:
            continue
        db.execute(
            text(
                """
                INSERT INTO product_channel_listings (
                    id, product_id, channel_code, external_sku, listing_status,
                    price_cents, currency, sync_mode, metadata_json, created_at, updated_at
                ) VALUES (
                    :id, :pid, :ch, :sku, 'ACTIVE', :price, 'BRL', 'API', '{}',
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                """
            ),
            {
                "id": str(uuid4()),
                "pid": prod["id"],
                "ch": ch,
                "sku": f"{ch}-{prod['id']}",
                "price": int(prod.get("amount_cents") or 0),
            },
        )
        channel_n += 1

    db.commit()
    return CatalogProfessionalSeedOut(
        ok=True,
        taxonomy_rows=tax_n,
        channel_rows=channel_n,
        attribute_definitions=attr_n,
        locker_categories_created=locker_cat_n,
        global_players=(
            GlobalPlayersSeedOut(ok=True, **gp_counts)
            if isinstance(gp_counts, dict)
            else None
        ),
    )
