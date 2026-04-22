from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db

router = APIRouter(prefix="/dev-admin/base", tags=["dev-base-catalog"])


def _ensure_dev_mode() -> None:
    if not settings.dev_bypass_auth:
        raise HTTPException(
            status_code=403,
            detail={
                "type": "DEV_MODE_REQUIRED",
                "message": "Este endpoint exige DEV_BYPASS_AUTH=true.",
            },
        )


def _normalize_json(value: dict[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    return value


def _json_text(value: dict[str, Any] | None) -> str:
    return json.dumps(_normalize_json(value))


class CountryUpsertIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    continent: str | None = Field(default=None, max_length=50)
    default_currency: str | None = Field(default=None, min_length=3, max_length=3)
    default_timezone: str | None = Field(default=None, max_length=50)
    address_format: str | None = Field(default=None, max_length=20)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class ProvinceUpsertIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    province_code_original: str | None = Field(default=None, max_length=2)
    region: str | None = Field(default=None, max_length=50)
    timezone: str | None = Field(default=None, max_length=50)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class ProductUpsertIn(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    amount_cents: int = Field(ge=0)
    currency: str = Field(default="BRL", min_length=3, max_length=8)
    category_id: str | None = Field(default=None, max_length=64)
    width_mm: int | None = None
    height_mm: int | None = None
    depth_mm: int | None = None
    weight_g: int | None = None
    is_active: bool = True
    requires_age_verification: bool = False
    requires_id_check: bool = False
    requires_signature: bool = False
    is_hazardous: bool = False
    is_fragile: bool = False
    is_virtual: bool = False
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class LockerLocationUpsertIn(BaseModel):
    external_id: str = Field(min_length=1, max_length=100)
    province_code: str | None = Field(default=None, max_length=10)
    city_name: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = Field(default=None, max_length=50)
    address_street: str | None = Field(default=None, max_length=255)
    address_number: str | None = Field(default=None, max_length=20)
    address_complement: str | None = Field(default=None, max_length=100)
    operating_hours_json: dict[str, Any] = Field(default_factory=dict)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


def _validate_lat_lng(latitude: float | None, longitude: float | None) -> tuple[float | None, float | None]:
    if latitude is None and longitude is None:
        return None, None
    if latitude is None or longitude is None:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_COORDINATES",
                "message": "latitude e longitude devem ser enviados juntos.",
            },
        )
    if latitude < -90 or latitude > 90:
        raise HTTPException(
            status_code=400,
            detail={"type": "INVALID_LATITUDE", "message": "latitude deve estar entre -90 e 90."},
        )
    if longitude < -180 or longitude > 180:
        raise HTTPException(
            status_code=400,
            detail={"type": "INVALID_LONGITUDE", "message": "longitude deve estar entre -180 e 180."},
        )
    return latitude, longitude


@router.get("/overview")
def read_base_overview(db: Session = Depends(get_db)):
    _ensure_dev_mode()
    table_rows = db.execute(
        text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )
    ).mappings().all()
    enum_rows = db.execute(
        text(
            """
            SELECT t.typname AS enum_name
            FROM pg_type t
            JOIN pg_namespace n ON n.oid = t.typnamespace
            WHERE t.typtype = 'e'
              AND n.nspname = 'public'
            ORDER BY t.typname
            """
        )
    ).mappings().all()

    return {
        "ok": True,
        "tables_total": len(table_rows),
        "enums_total": len(enum_rows),
        "managed_tables": [
            "capability_country",
            "capability_province",
            "products",
            "capability_locker_location",
        ],
    }


@router.get("/enums")
def list_public_enums(db: Session = Depends(get_db)):
    _ensure_dev_mode()
    rows = db.execute(
        text(
            """
            SELECT t.typname AS enum_name, e.enumsortorder, e.enumlabel AS enum_value
            FROM pg_type t
            JOIN pg_namespace n ON n.oid = t.typnamespace
            JOIN pg_enum e ON e.enumtypid = t.oid
            WHERE t.typtype = 'e'
              AND n.nspname = 'public'
            ORDER BY t.typname, e.enumsortorder
            """
        )
    ).mappings().all()

    grouped: dict[str, list[str]] = {}
    for row in rows:
        grouped.setdefault(str(row["enum_name"]), []).append(str(row["enum_value"]))

    return {"ok": True, "items": [{"enum_name": k, "values": v} for k, v in grouped.items()]}


@router.get("/tables")
def list_public_tables(
    include_columns: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()
    rows = db.execute(
        text(
            """
            SELECT
              t.table_name,
              COALESCE(s.n_live_tup::bigint, 0) AS estimated_rows
            FROM information_schema.tables t
            LEFT JOIN pg_stat_user_tables s
              ON s.schemaname = t.table_schema
             AND s.relname = t.table_name
            WHERE t.table_schema = 'public'
              AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name
            """
        )
    ).mappings().all()

    items: list[dict[str, Any]] = []
    for row in rows:
        item = {"table_name": row["table_name"], "estimated_rows": int(row["estimated_rows"] or 0)}
        if include_columns:
            columns = db.execute(
                text(
                    """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = :table_name
                    ORDER BY ordinal_position
                    """
                ),
                {"table_name": row["table_name"]},
            ).mappings().all()
            item["columns"] = [dict(col) for col in columns]
        items.append(item)

    return {"ok": True, "items": items}


@router.get("/countries")
def list_countries(
    q: str | None = Query(default=None),
    active_only: bool = Query(default=False),
    limit: int = Query(default=300, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()
    rows = db.execute(
        text(
            """
            SELECT id, code, name, continent, default_currency, default_timezone,
                   address_format, metadata_json, is_active, created_at, updated_at
            FROM public.capability_country
            WHERE (:active_only = false OR is_active = true)
              AND (
                :q IS NULL
                OR code ILIKE :q_like
                OR name ILIKE :q_like
                OR continent ILIKE :q_like
              )
            ORDER BY code
            LIMIT :limit
            """
        ),
        {
            "q": q,
            "q_like": f"%{q}%" if q else None,
            "active_only": active_only,
            "limit": limit,
        },
    ).mappings().all()
    return {"ok": True, "items": [dict(row) for row in rows]}


@router.put("/countries/{code}")
def upsert_country(
    code: str,
    payload: CountryUpsertIn,
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()
    normalized_code = str(code or "").strip().upper()
    if len(normalized_code) != 2:
        raise HTTPException(status_code=400, detail={"type": "INVALID_COUNTRY_CODE", "message": "Use código ISO de 2 caracteres."})

    row = db.execute(
        text(
            """
            INSERT INTO public.capability_country (
              code, name, continent, default_currency, default_timezone,
              address_format, metadata_json, is_active
            )
            VALUES (
              :code, :name, :continent, :default_currency, :default_timezone,
              :address_format, CAST(:metadata_json AS jsonb), :is_active
            )
            ON CONFLICT (code) DO UPDATE SET
              name = EXCLUDED.name,
              continent = EXCLUDED.continent,
              default_currency = EXCLUDED.default_currency,
              default_timezone = EXCLUDED.default_timezone,
              address_format = EXCLUDED.address_format,
              metadata_json = EXCLUDED.metadata_json,
              is_active = EXCLUDED.is_active,
              updated_at = now()
            RETURNING id, code, name, continent, default_currency, default_timezone,
                      address_format, metadata_json, is_active, created_at, updated_at
            """
        ),
        {
            "code": normalized_code,
            "name": payload.name.strip(),
            "continent": payload.continent.strip() if payload.continent else None,
            "default_currency": payload.default_currency.strip().upper() if payload.default_currency else None,
            "default_timezone": payload.default_timezone.strip() if payload.default_timezone else None,
            "address_format": payload.address_format.strip() if payload.address_format else None,
            "metadata_json": _json_text(payload.metadata_json),
            "is_active": payload.is_active,
        },
    ).mappings().first()
    db.commit()
    return {"ok": True, "item": dict(row) if row else None}


@router.get("/provinces")
def list_provinces(
    country_code: str | None = Query(default=None),
    q: str | None = Query(default=None),
    active_only: bool = Query(default=False),
    limit: int = Query(default=500, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()
    normalized_country = country_code.strip().upper() if country_code else None
    rows = db.execute(
        text(
            """
            SELECT id, code, name, country_code, province_code_original, region,
                   timezone, is_active, metadata_json, created_at, updated_at
            FROM public.capability_province
            WHERE (:country_code IS NULL OR country_code = :country_code)
              AND (:active_only = false OR is_active = true)
              AND (
                :q IS NULL
                OR code ILIKE :q_like
                OR name ILIKE :q_like
                OR region ILIKE :q_like
              )
            ORDER BY country_code, code
            LIMIT :limit
            """
        ),
        {
            "country_code": normalized_country,
            "active_only": active_only,
            "q": q,
            "q_like": f"%{q}%" if q else None,
            "limit": limit,
        },
    ).mappings().all()
    return {"ok": True, "items": [dict(row) for row in rows]}


@router.get("/lockers")
def list_lockers_for_ops(
    country_code: str | None = Query(default=None, max_length=2),
    province_code: str | None = Query(default=None, max_length=10),
    q: str | None = Query(default=None),
    active_only: bool = Query(default=True),
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()
    normalized_country = country_code.strip().upper() if country_code else None
    normalized_province = province_code.strip().upper() if province_code else None
    rows = db.execute(
        text(
            """
            SELECT
              l.id AS locker_id,
              l.display_name,
              l.region,
              l.active,
              l.slots_count AS slots,
              l.country AS locker_country_raw,
              cl.province_code,
              cp.country_code,
              cp.name AS province_name,
              cl.city_name,
              cl.district
            FROM public.lockers l
            LEFT JOIN public.capability_locker_location cl
              ON cl.external_id = l.id
            LEFT JOIN public.capability_province cp
              ON cp.code = cl.province_code
            WHERE (:active_only = false OR l.active = true)
              AND (:country_code IS NULL OR cp.country_code = :country_code)
              AND (:province_code IS NULL OR cl.province_code = :province_code)
              AND (
                :q IS NULL
                OR l.id ILIKE :q_like
                OR l.display_name ILIKE :q_like
                OR cl.city_name ILIKE :q_like
                OR cl.district ILIKE :q_like
              )
            ORDER BY l.display_name, l.id
            LIMIT :limit
            """
        ),
        {
            "active_only": active_only,
            "country_code": normalized_country,
            "province_code": normalized_province,
            "q": q,
            "q_like": f"%{q}%" if q else None,
            "limit": limit,
        },
    ).mappings().all()
    return {"ok": True, "items": [dict(row) for row in rows]}


@router.get("/locker-locations")
def list_locker_locations(
    country_code: str | None = Query(default=None, max_length=2),
    province_code: str | None = Query(default=None, max_length=10),
    q: str | None = Query(default=None),
    active_only: bool = Query(default=False),
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()
    normalized_country = country_code.strip().upper() if country_code else None
    normalized_province = province_code.strip().upper() if province_code else None
    rows = db.execute(
        text(
            """
            SELECT
              cl.id, cl.external_id, cl.province_code, cp.country_code,
              cl.city_name, cl.district, cl.postal_code,
              cl.latitude, cl.longitude,
              ST_AsText(cl.geom) AS geom_wkt,
              cl.timezone, cl.address_street, cl.address_number,
              cl.address_complement, cl.operating_hours_json,
              cl.metadata_json, cl.is_active, cl.created_at, cl.updated_at
            FROM public.capability_locker_location cl
            LEFT JOIN public.capability_province cp
              ON cp.code = cl.province_code
            WHERE (:active_only = false OR cl.is_active = true)
              AND (:country_code IS NULL OR cp.country_code = :country_code)
              AND (:province_code IS NULL OR cl.province_code = :province_code)
              AND (
                :q IS NULL
                OR cl.external_id ILIKE :q_like
                OR cl.city_name ILIKE :q_like
                OR cl.district ILIKE :q_like
                OR cl.address_street ILIKE :q_like
              )
            ORDER BY cl.external_id, cl.id
            LIMIT :limit
            """
        ),
        {
            "active_only": active_only,
            "country_code": normalized_country,
            "province_code": normalized_province,
            "q": q,
            "q_like": f"%{q}%" if q else None,
            "limit": limit,
        },
    ).mappings().all()
    return {"ok": True, "items": [dict(row) for row in rows]}


@router.put("/locker-locations/{external_id}")
def upsert_locker_location(
    external_id: str,
    payload: LockerLocationUpsertIn,
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()
    normalized_external_id = str(external_id or "").strip()
    if not normalized_external_id:
        raise HTTPException(status_code=400, detail={"type": "INVALID_EXTERNAL_ID", "message": "external_id é obrigatório."})

    payload_external = str(payload.external_id or "").strip()
    if payload_external and payload_external != normalized_external_id:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "EXTERNAL_ID_MISMATCH",
                "message": "external_id do path e payload não conferem.",
            },
        )

    latitude, longitude = _validate_lat_lng(payload.latitude, payload.longitude)
    row = db.execute(
        text(
            """
            INSERT INTO public.capability_locker_location (
              external_id, province_code, city_name, district, postal_code,
              latitude, longitude, timezone, address_street, address_number,
              address_complement, operating_hours_json, metadata_json, is_active
            )
            VALUES (
              :external_id, :province_code, :city_name, :district, :postal_code,
              :latitude, :longitude, :timezone, :address_street, :address_number,
              :address_complement, CAST(:operating_hours_json AS jsonb),
              CAST(:metadata_json AS jsonb), :is_active
            )
            ON CONFLICT (external_id) DO UPDATE SET
              province_code = EXCLUDED.province_code,
              city_name = EXCLUDED.city_name,
              district = EXCLUDED.district,
              postal_code = EXCLUDED.postal_code,
              latitude = EXCLUDED.latitude,
              longitude = EXCLUDED.longitude,
              timezone = EXCLUDED.timezone,
              address_street = EXCLUDED.address_street,
              address_number = EXCLUDED.address_number,
              address_complement = EXCLUDED.address_complement,
              operating_hours_json = EXCLUDED.operating_hours_json,
              metadata_json = EXCLUDED.metadata_json,
              is_active = EXCLUDED.is_active,
              updated_at = now()
            RETURNING id, external_id, province_code, city_name, district, postal_code,
                      latitude, longitude, ST_AsText(geom) AS geom_wkt, timezone,
                      address_street, address_number, address_complement,
                      operating_hours_json, metadata_json, is_active, created_at, updated_at
            """
        ),
        {
            "external_id": normalized_external_id,
            "province_code": payload.province_code.strip().upper() if payload.province_code else None,
            "city_name": payload.city_name.strip() if payload.city_name else None,
            "district": payload.district.strip() if payload.district else None,
            "postal_code": payload.postal_code.strip() if payload.postal_code else None,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": payload.timezone.strip() if payload.timezone else None,
            "address_street": payload.address_street.strip() if payload.address_street else None,
            "address_number": payload.address_number.strip() if payload.address_number else None,
            "address_complement": payload.address_complement.strip() if payload.address_complement else None,
            "operating_hours_json": _json_text(payload.operating_hours_json),
            "metadata_json": _json_text(payload.metadata_json),
            "is_active": payload.is_active,
        },
    ).mappings().first()
    db.commit()
    return {"ok": True, "item": dict(row) if row else None}


@router.put("/provinces/{code}")
def upsert_province(
    code: str,
    payload: ProvinceUpsertIn,
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()
    normalized_code = str(code or "").strip().upper()
    if not normalized_code:
        raise HTTPException(status_code=400, detail={"type": "INVALID_PROVINCE_CODE", "message": "code é obrigatório."})

    row = db.execute(
        text(
            """
            INSERT INTO public.capability_province (
              code, name, country_code, province_code_original, region,
              timezone, metadata_json, is_active
            )
            VALUES (
              :code, :name, :country_code, :province_code_original, :region,
              :timezone, CAST(:metadata_json AS jsonb), :is_active
            )
            ON CONFLICT (code) DO UPDATE SET
              name = EXCLUDED.name,
              country_code = EXCLUDED.country_code,
              province_code_original = EXCLUDED.province_code_original,
              region = EXCLUDED.region,
              timezone = EXCLUDED.timezone,
              metadata_json = EXCLUDED.metadata_json,
              is_active = EXCLUDED.is_active,
              updated_at = now()
            RETURNING id, code, name, country_code, province_code_original, region,
                      timezone, is_active, metadata_json, created_at, updated_at
            """
        ),
        {
            "code": normalized_code,
            "name": payload.name.strip(),
            "country_code": payload.country_code.strip().upper() if payload.country_code else None,
            "province_code_original": payload.province_code_original.strip().upper() if payload.province_code_original else None,
            "region": payload.region.strip().upper() if payload.region else None,
            "timezone": payload.timezone.strip() if payload.timezone else None,
            "metadata_json": _json_text(payload.metadata_json),
            "is_active": payload.is_active,
        },
    ).mappings().first()
    db.commit()
    return {"ok": True, "item": dict(row) if row else None}


@router.get("/products")
def list_products(
    q: str | None = Query(default=None),
    active_only: bool = Query(default=False),
    limit: int = Query(default=400, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()
    rows = db.execute(
        text(
            """
            SELECT id, name, description, amount_cents, currency, category_id,
                   width_mm, height_mm, depth_mm, weight_g, is_active,
                   requires_age_verification, requires_id_check, requires_signature,
                   is_hazardous, is_fragile, is_virtual,
                   metadata_json, created_at, updated_at
            FROM public.products
            WHERE (:active_only = false OR is_active = true)
              AND (
                :q IS NULL
                OR id ILIKE :q_like
                OR name ILIKE :q_like
                OR COALESCE(description, '') ILIKE :q_like
              )
            ORDER BY id
            LIMIT :limit
            """
        ),
        {
            "active_only": active_only,
            "q": q,
            "q_like": f"%{q}%" if q else None,
            "limit": limit,
        },
    ).mappings().all()
    return {"ok": True, "items": [dict(row) for row in rows]}


@router.put("/products/{sku_id}")
def upsert_product(
    sku_id: str,
    payload: ProductUpsertIn,
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()
    normalized_sku = str(sku_id or "").strip()
    if not normalized_sku:
        raise HTTPException(status_code=400, detail={"type": "INVALID_SKU_ID", "message": "sku_id é obrigatório."})

    row = db.execute(
        text(
            """
            INSERT INTO public.products (
              id, name, description, amount_cents, currency, category_id,
              width_mm, height_mm, depth_mm, weight_g, is_active,
              requires_age_verification, requires_id_check, requires_signature,
              is_hazardous, is_fragile, is_virtual, metadata_json
            )
            VALUES (
              :id, :name, :description, :amount_cents, :currency, :category_id,
              :width_mm, :height_mm, :depth_mm, :weight_g, :is_active,
              :requires_age_verification, :requires_id_check, :requires_signature,
              :is_hazardous, :is_fragile, :is_virtual, CAST(:metadata_json AS jsonb)
            )
            ON CONFLICT (id) DO UPDATE SET
              name = EXCLUDED.name,
              description = EXCLUDED.description,
              amount_cents = EXCLUDED.amount_cents,
              currency = EXCLUDED.currency,
              category_id = EXCLUDED.category_id,
              width_mm = EXCLUDED.width_mm,
              height_mm = EXCLUDED.height_mm,
              depth_mm = EXCLUDED.depth_mm,
              weight_g = EXCLUDED.weight_g,
              is_active = EXCLUDED.is_active,
              requires_age_verification = EXCLUDED.requires_age_verification,
              requires_id_check = EXCLUDED.requires_id_check,
              requires_signature = EXCLUDED.requires_signature,
              is_hazardous = EXCLUDED.is_hazardous,
              is_fragile = EXCLUDED.is_fragile,
              is_virtual = EXCLUDED.is_virtual,
              metadata_json = EXCLUDED.metadata_json,
              updated_at = now()
            RETURNING id, name, description, amount_cents, currency, category_id,
                      width_mm, height_mm, depth_mm, weight_g, is_active,
                      requires_age_verification, requires_id_check, requires_signature,
                      is_hazardous, is_fragile, is_virtual, metadata_json,
                      created_at, updated_at
            """
        ),
        {
            "id": normalized_sku,
            "name": payload.name.strip(),
            "description": payload.description,
            "amount_cents": payload.amount_cents,
            "currency": payload.currency.strip().upper(),
            "category_id": payload.category_id,
            "width_mm": payload.width_mm,
            "height_mm": payload.height_mm,
            "depth_mm": payload.depth_mm,
            "weight_g": payload.weight_g,
            "is_active": payload.is_active,
            "requires_age_verification": payload.requires_age_verification,
            "requires_id_check": payload.requires_id_check,
            "requires_signature": payload.requires_signature,
            "is_hazardous": payload.is_hazardous,
            "is_fragile": payload.is_fragile,
            "is_virtual": payload.is_virtual,
            "metadata_json": _json_text(payload.metadata_json),
        },
    ).mappings().first()
    db.commit()
    return {"ok": True, "item": dict(row) if row else None}
