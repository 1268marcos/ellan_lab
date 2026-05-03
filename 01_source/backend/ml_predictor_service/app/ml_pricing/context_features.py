"""Carrega contexto para precificação dinâmica a partir do Postgres (schema Ellan)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app import db
from app.ml_pricing.elasticity_model import historical_elasticity_for_sku_region

# Feriados fixos BR (mês, dia) — sem dependência externa
BR_FIXED_HOLIDAYS: set[tuple[int, int]] = {
    (1, 1),
    (4, 21),
    (5, 1),
    (9, 7),
    (10, 12),
    (11, 2),
    (11, 15),
    (12, 25),
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _is_br_holiday(dt: datetime) -> bool:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone()
    return (local.month, local.day) in BR_FIXED_HOLIDAYS


@dataclass
class PricingContextRaw:
    hour: int
    dow: int  # 0=Monday
    is_holiday: float  # 0 or 1
    occupancy_ratio: float  # 0..1
    dist_competitor_km: float
    temp_season_norm: float  # 0..1 (normalização grosseira)
    historical_elasticity: float  # tipicamente negativo
    base_price_cents: int
    region: str
    sku_id: str


def _locker_coords(locker_id: str) -> tuple[float | None, float | None, str]:
    row = db.fetch_one(
        """
        SELECT l.latitude, l.longitude, l.region
        FROM lockers l
        WHERE l.id = %s
        LIMIT 1
        """,
        (locker_id,),
    )
    if not row:
        return None, None, ""
    lat, lon = row.get("latitude"), row.get("longitude")
    if lat is None or lon is None:
        cap = db.fetch_one(
            """
            SELECT cl.latitude, cl.longitude
            FROM lockers l
            JOIN capability_locker_location cl
              ON cl.external_id = l.external_id AND cl.is_active = true
            WHERE l.id = %s
            LIMIT 1
            """,
            (locker_id,),
        )
        if cap:
            lat, lon = cap.get("latitude"), cap.get("longitude")
            try:
                lat = float(lat) if lat is not None else None
                lon = float(lon) if lon is not None else None
            except (TypeError, ValueError):
                lat, lon = None, None
    return (float(lat) if lat is not None else None, float(lon) if lon is not None else None, str(row.get("region") or ""))


def _nearest_competitor_km(locker_id: str, lat: float | None, lon: float | None, region: str) -> float:
    if lat is None or lon is None:
        return 5.0  # prior fraco: mercado moderadamente contestado
    rows = db.fetch_all(
        """
        SELECT id, latitude, longitude
        FROM lockers
        WHERE active = true AND id <> %s AND region = %s
          AND latitude IS NOT NULL AND longitude IS NOT NULL
        LIMIT 500
        """,
        (locker_id, region),
    )
    best = 50.0
    for r in rows:
        try:
            d = _haversine_km(lat, lon, float(r["latitude"]), float(r["longitude"]))
        except (TypeError, ValueError):
            continue
        if d > 0.05 and d < best:
            best = d
    return float(best)


def _occupancy_ratio(locker_id: str) -> float:
    row = db.fetch_one(
        """
        SELECT measured_occupied_hours, billed_storage_units
        FROM locker_utilization_snapshots
        WHERE locker_id = %s
        ORDER BY snapshot_date DESC
        LIMIT 1
        """,
        (locker_id,),
    )
    if not row:
        return 0.45
    occ_h = float(row.get("measured_occupied_hours") or 0)
    units = float(row.get("billed_storage_units") or 0)
    if units <= 0:
        return min(1.0, occ_h / 24.0)
    return float(min(1.0, max(0.0, occ_h / (24.0 * max(units, 0.01)))))


def _telemetry_temp_norm(locker_id: str) -> float:
    row = db.fetch_one(
        """
        SELECT AVG(temperature_celsius)::float AS t
        FROM locker_telemetry
        WHERE locker_id = %s
          AND occurred_at >= NOW() - INTERVAL '7 days'
          AND temperature_celsius IS NOT NULL
        """,
        (locker_id,),
    )
    if not row or row.get("t") is None:
        return 0.5
    t = float(row["t"])
    # Normaliza ~10–40°C para 0–1 (proxy sazonal / conforto)
    return float(min(1.0, max(0.0, (t - 10.0) / 30.0)))


def resolve_base_price_cents(locker_id: str, region: str, sku_id: str) -> int:
    pr = db.fetch_one(
        """
        SELECT base_amount_cents
        FROM pricing_rules
        WHERE is_active = true
          AND valid_from <= NOW()
          AND (valid_until IS NULL OR valid_until > NOW())
          AND (locker_id = %s OR (locker_id IS NULL AND region = %s))
        ORDER BY CASE WHEN locker_id IS NOT NULL THEN 0 ELSE 1 END, valid_from DESC
        LIMIT 1
        """,
        (locker_id, region),
    )
    if pr and pr.get("base_amount_cents"):
        return int(pr["base_amount_cents"])
    med = db.fetch_one(
        """
        SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY oi.unit_amount_cents)::bigint AS m
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        JOIN allocations a ON a.order_id = o.id
        JOIN lockers lk ON lk.id = a.locker_id
        WHERE oi.sku_id = %s AND lk.region = %s
          AND o.created_at >= NOW() - INTERVAL '90 days'
        """,
        (sku_id, region),
    )
    if med and med.get("m"):
        return int(med["m"])
    return 999  # fallback simbólico


def load_pricing_context(locker_id: str, product_id: str, at: datetime | None = None) -> PricingContextRaw:
    """product_id = sku_id do catálogo."""
    at = at or datetime.now(timezone.utc)
    lat, lon, region = _locker_coords(locker_id)
    occ = _occupancy_ratio(locker_id)
    dist = _nearest_competitor_km(locker_id, lat, lon, region)
    temp_n = _telemetry_temp_norm(locker_id)
    elast = historical_elasticity_for_sku_region(product_id, region or "XX")
    base = resolve_base_price_cents(locker_id, region or "XX", product_id)
    local = at.astimezone() if at.tzinfo else at.replace(tzinfo=timezone.utc).astimezone()
    return PricingContextRaw(
        hour=local.hour,
        dow=local.weekday(),
        is_holiday=1.0 if _is_br_holiday(at) else 0.0,
        occupancy_ratio=occ,
        dist_competitor_km=dist,
        temp_season_norm=temp_n,
        historical_elasticity=elast,
        base_price_cents=base,
        region=region or "XX",
        sku_id=product_id,
    )


def context_to_vector(ctx: PricingContextRaw) -> tuple[list[str], list[float]]:
    """Vetor para bandit linear + SHAP linear."""
    h = 2 * math.pi * ctx.hour / 24.0
    d = 2 * math.pi * ctx.dow / 7.0
    names = [
        "bias",
        "hora_sin",
        "hora_cos",
        "dia_semana_sin",
        "dia_semana_cos",
        "feriado",
        "ocupacao_locker",
        "distancia_concorrente_km",
        "temporada_temp_norm",
        "elasticidade_historica",
    ]
    vals = [
        1.0,
        math.sin(h),
        math.cos(h),
        math.sin(d),
        math.cos(d),
        ctx.is_holiday,
        ctx.occupancy_ratio,
        math.log1p(max(0.0, ctx.dist_competitor_km)),
        ctx.temp_season_norm,
        ctx.historical_elasticity,
    ]
    return names, vals


def fetch_active_bundle_for_product(product_id: str) -> dict[str, Any] | None:
    return db.fetch_one(
        """
        SELECT pb.id, pb.name, pb.code, pb.amount_cents, pb.currency
        FROM product_bundle_items pbi
        JOIN product_bundles pb ON pb.id = pbi.bundle_id
        WHERE pbi.product_id = %s
          AND pb.is_active = true
          AND (pb.valid_from IS NULL OR pb.valid_from <= NOW())
          AND (pb.valid_until IS NULL OR pb.valid_until > NOW())
        ORDER BY pb.updated_at DESC NULLS LAST
        LIMIT 1
        """,
        (product_id,),
    )


def active_promotions_digest(region: str) -> list[dict[str, Any]]:
    _ = region
    return db.fetch_all(
        """
        SELECT id, code, type, discount_pct, discount_cents
        FROM promotions
        WHERE is_active = true
          AND valid_from <= NOW()
          AND (valid_until IS NULL OR valid_until > NOW())
        ORDER BY discount_pct DESC NULLS LAST
        LIMIT 5
        """,
        (),
    )
