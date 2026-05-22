"""Seed de promoções PR3 (marketplace, carriers, redes locker mundiais)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.global_players_seed import seed_global_players_registry
from app.core.promotions_players_integration import (
    _table_exists,
    load_players_catalog,
    seed_player_aliases_and_relations,
)
from app.data.catalog_players_registry import PLAYERS_REGISTRY


@dataclass(frozen=True)
class PromotionSeedRow:
    code: str
    name: str
    type: str
    discount_pct: float | None = None
    discount_cents: int | None = None
    min_order_cents: int = 0
    max_discount_cents: int | None = None
    max_uses: int | None = None
    per_user_limit: int = 1
    conditions_json: dict | None = None
    days_valid: int = 365


PROMOTIONS_SEED: tuple[PromotionSeedRow, ...] = (
    PromotionSeedRow(
        code="PR3-PROMO-001",
        name="Promo demo PR3 — 10% geral",
        type="PERCENT_OFF",
        discount_pct=10.0,
        min_order_cents=1000,
        max_discount_cents=5000,
    ),
    PromotionSeedRow(
        code="MAGALU10",
        name="Magalu Marketplace — 10% locker",
        type="PERCENT_OFF",
        discount_pct=10.0,
        min_order_cents=2500,
        conditions_json={"channel": "MAGALU", "marketplace": "BR"},
    ),
    PromotionSeedRow(
        code="ML-LOCKER-15",
        name="Mercado Livre — 15% retirada locker",
        type="PERCENT_OFF",
        discount_pct=15.0,
        min_order_cents=3000,
        max_discount_cents=8000,
        conditions_json={"channel": "MERCADO_LIVRE", "pickup": "LOCKER"},
    ),
    PromotionSeedRow(
        code="INPOST-PT-FIX",
        name="InPost Parcel Lockers PT — €2 off",
        type="FIXED_OFF",
        discount_cents=200,
        min_order_cents=1500,
        conditions_json={"network": "INPOST", "country": "PT"},
    ),
    PromotionSeedRow(
        code="DHL-PACK-5",
        name="DHL Packstation — 5% off",
        type="PERCENT_OFF",
        discount_pct=5.0,
        min_order_cents=2000,
        conditions_json={"carrier": "DHL", "service": "PACKSTATION"},
    ),
    PromotionSeedRow(
        code="AMZN-HUB-BUNDLE",
        name="Amazon US Hub — bundle desconto",
        type="BUNDLE_DISCOUNT",
        max_discount_cents=1200,
        conditions_json={"bundle_size": 2, "bundle_price_cents": 900, "marketplace": "AMAZON_US_HUB"},
    ),
    PromotionSeedRow(
        code="WORTEN-FIXED",
        name="Worten — €3 off coleta",
        type="FIXED_OFF",
        discount_cents=300,
        min_order_cents=2000,
        conditions_json={"retailer": "WORTEN", "country": "PT"},
    ),
    PromotionSeedRow(
        code="CORTEINGLES-BXGY",
        name="El Corte Inglés — compre 2 leve 1",
        type="BUY_X_GET_Y",
        conditions_json={"buy_qty": 2, "get_qty": 1, "free_item_price_cents": 400},
    ),
    PromotionSeedRow(
        code="SHOPEE-FREE",
        name="Shopee — item grátis campanha",
        type="FREE_ITEM",
        conditions_json={"free_qty": 1, "free_item_price_cents": 350},
    ),
    PromotionSeedRow(
        code="TIKTOK-BUNDLE",
        name="TikTok Shop — pacote locker",
        type="BUNDLE_DISCOUNT",
        max_discount_cents=1500,
        conditions_json={"bundle_size": 3, "bundle_price_cents": 1200, "channel": "TIKTOK_SHOP"},
    ),
    PromotionSeedRow(
        code="DPD-LOCKER-8",
        name="DPD rede locker — 8%",
        type="PERCENT_OFF",
        discount_pct=8.0,
        min_order_cents=1800,
        conditions_json={"operator": "DPD", "network_type": "LOCKER"},
    ),
    PromotionSeedRow(
        code="USPS-HUB-FIX",
        name="USPS Hub Locker — $1.50 off",
        type="FIXED_OFF",
        discount_cents=150,
        min_order_cents=1000,
        conditions_json={"carrier": "USPS", "country": "US"},
    ),
    PromotionSeedRow(
        code="CORREIOS-LOCKER-12",
        name="Correios — 12% retirada locker",
        type="PERCENT_OFF",
        discount_pct=12.0,
        min_order_cents=2000,
        max_discount_cents=6000,
        conditions_json={"carrier": "CORREIOS", "network_type": "LOCKER", "country": "BR"},
    ),
    PromotionSeedRow(
        code="CTT-LOCKER-PT",
        name="CTT Expresso — €2.50 locker PT",
        type="FIXED_OFF",
        discount_cents=250,
        min_order_cents=1200,
        conditions_json={"carrier": "CTT", "country": "PT", "pickup": "LOCKER"},
    ),
    PromotionSeedRow(
        code="INPOST-UK-5",
        name="InPost UK — 5% parcel locker",
        type="PERCENT_OFF",
        discount_pct=5.0,
        min_order_cents=1000,
        conditions_json={"network": "INPOST", "country": "UK"},
    ),
    PromotionSeedRow(
        code="DHL-DE-PACK-7",
        name="DHL Packstation DE — 7%",
        type="PERCENT_OFF",
        discount_pct=7.0,
        min_order_cents=2500,
        conditions_json={"carrier": "DHL", "country": "DE", "service": "PACKSTATION"},
    ),
    PromotionSeedRow(
        code="GLS-LOCKER-6",
        name="GLS Parcel Locker — 6%",
        type="PERCENT_OFF",
        discount_pct=6.0,
        min_order_cents=1500,
        conditions_json={"operator": "GLS", "network_type": "LOCKER"},
    ),
    PromotionSeedRow(
        code="UPS-ACCESS-FIX",
        name="UPS Access Point — $2 off",
        type="FIXED_OFF",
        discount_cents=200,
        min_order_cents=1500,
        conditions_json={"carrier": "UPS", "service": "ACCESS_POINT"},
    ),
    PromotionSeedRow(
        code="PACKETA-LOCKER-10",
        name="Packeta / Zásilkovna — 10%",
        type="PERCENT_OFF",
        discount_pct=10.0,
        min_order_cents=800,
        conditions_json={"operator": "PACKETA", "region": "EU"},
    ),
    PromotionSeedRow(
        code="MONDIAL-RELAY-8",
        name="Mondial Relay — 8% ponto locker",
        type="PERCENT_OFF",
        discount_pct=8.0,
        min_order_cents=1200,
        conditions_json={"operator": "MONDIAL_RELAY", "country": "FR"},
    ),
    PromotionSeedRow(
        code="PONTO-MAGALU-FIX",
        name="Ponto Magalu — R$5 off retirada",
        type="FIXED_OFF",
        discount_cents=500,
        min_order_cents=3000,
        conditions_json={"retail_pudo": "PONTO_MAGALU", "country": "BR"},
    ),
    PromotionSeedRow(
        code="CAINIAO-HUB-5",
        name="Cainiao hub — 5% agregador",
        type="PERCENT_OFF",
        discount_pct=5.0,
        min_order_cents=1000,
        conditions_json={"aggregator": "CAINIAO"},
    ),
    PromotionSeedRow(
        code="MELHOR-ENVIO-10",
        name="Melhor Envio — 10% locker BR",
        type="PERCENT_OFF",
        discount_pct=10.0,
        min_order_cents=2000,
        conditions_json={"aggregator": "MELHOR_ENVIO", "country": "BR"},
    ),
    PromotionSeedRow(
        code="VINTED-GO-FIX",
        name="Vinted Go locker — €1 off",
        type="FIXED_OFF",
        discount_cents=100,
        min_order_cents=900,
        conditions_json={"operator": "VINTED_GO", "network_type": "LOCKER"},
    ),
    PromotionSeedRow(
        code="IFOOD-LOCKER-10",
        name="iFood — 10% retirada locker climatizado",
        type="PERCENT_OFF",
        discount_pct=10.0,
        min_order_cents=2500,
        conditions_json={"food_delivery": "IFOOD", "pickup": "LOCKER"},
    ),
    PromotionSeedRow(
        code="UBER-LOCKER-FIX",
        name="Uber Eats — R$4 off locker",
        type="FIXED_OFF",
        discount_cents=400,
        min_order_cents=2000,
        conditions_json={"food_delivery": "UBER_EATS", "country": "BR"},
    ),
    PromotionSeedRow(
        code="GLOVO-PICKUP-8",
        name="Glovo — 8% parcel shop / locker",
        type="PERCENT_OFF",
        discount_pct=8.0,
        min_order_cents=1000,
        conditions_json={"food_delivery": "GLOVO", "country": "ES"},
    ),
    PromotionSeedRow(
        code="DELIVEROO-LOCKER",
        name="Deliveroo — £1.50 locker UK",
        type="FIXED_OFF",
        discount_cents=150,
        min_order_cents=1200,
        conditions_json={"food_delivery": "DELIVEROO", "country": "GB"},
    ),
)


def _conditions_json_sql_value(db: Session) -> str:
    if db.get_bind().dialect.name == "postgresql":
        return "CAST(:conditions_json AS JSONB)"
    return ":conditions_json"


def seed_promotions(db: Session, *, created_by: str | None = None) -> dict[str, int]:
    """Insere promoções de demonstração (idempotente por code)."""
    import json

    conditions_sql = _conditions_json_sql_value(db)
    now = datetime.now(timezone.utc)
    inserted = 0
    skipped = 0
    for row in PROMOTIONS_SEED:
        exists = db.execute(
            text("SELECT 1 FROM promotions WHERE code = :code LIMIT 1"),
            {"code": row.code},
        ).scalar()
        if exists:
            skipped += 1
            continue
        valid_until = now + timedelta(days=row.days_valid)
        promo_id = str(uuid4())
        db.execute(
            text(
                f"""
                INSERT INTO promotions (
                    id, code, name, type, discount_pct, discount_cents, min_order_cents,
                    max_discount_cents, max_uses, uses_count, per_user_limit, conditions_json,
                    is_active, valid_from, valid_until, created_by, created_at, updated_at
                ) VALUES (
                    :id, :code, :name, :type, :discount_pct, :discount_cents, :min_order_cents,
                    :max_discount_cents, :max_uses, 0, :per_user_limit, {conditions_sql},
                    TRUE, :valid_from, :valid_until, :created_by, :created_at, :updated_at
                )
                """
            ),
            {
                "id": promo_id,
                "code": row.code,
                "name": row.name,
                "type": row.type,
                "discount_pct": row.discount_pct,
                "discount_cents": row.discount_cents,
                "min_order_cents": row.min_order_cents,
                "max_discount_cents": row.max_discount_cents,
                "max_uses": row.max_uses,
                "per_user_limit": row.per_user_limit,
                "conditions_json": json.dumps(row.conditions_json or {}),
                "valid_from": now,
                "valid_until": valid_until,
                "created_by": created_by,
                "created_at": now,
                "updated_at": now,
            },
        )
        inserted += 1
    db.commit()
    return {"inserted": inserted, "skipped": skipped, "total_catalog": len(PROMOTIONS_SEED)}


_CAMPAIGN_PLAYER_CODES = [
    "INPOST", "DHL_PACKSTATION", "MAGALU", "MERCADO_LIVRE", "AMAZON_HUB", "DPD",
    "CORREIOS", "CTT", "WORTEN", "EL_CORTE_INGLES", "UBER_EATS", "IFOOD", "CAINIAO",
]

CAMPAIGNS_SEED: tuple[tuple[str, str, str, str | None, int], ...] = (
    ("GLOBAL_LOCKER_2026", "Campanha global redes locker", "LOCKER_NETWORK", None, 10),
    ("LOCKER_BR", "Brasil locker (Correios, Magalu, ML, Shopee)", "LOCKER_NETWORK", "BR", 12),
    ("LOCKER_PT", "Portugal locker (CTT, InPost, Worten)", "LOCKER_NETWORK", "PT", 14),
    ("LOCKER_EU_CORE", "UE core (DHL, DPD, GLS, Mondial Relay, Packeta)", "LOCKER_NETWORK", "EU", 16),
    ("MARKETPLACE_BR", "Marketplaces Brasil (Magalu, ML, Shopee)", "MARKETPLACE", "BR", 20),
    ("MARKETPLACE_EU", "Marketplaces Europa (Worten, Corte Inglés, Amazon)", "MARKETPLACE", "EU", 25),
    ("CARRIER_EU", "Carriers UE (InPost, DHL, DPD, CTT)", "CARRIER", "EU", 30),
    ("CARRIER_US", "Carriers EUA (USPS, Amazon Hub, UPS)", "CARRIER", "US", 35),
    ("AGGREGATOR_GLOBAL", "Agregadores (Cainiao, Melhor Envio)", "AGGREGATOR", None, 40),
    ("FOOD_LOCKER_GLOBAL", "Food delivery → locker (iFood, Uber, Glovo, Deliveroo)", "FOOD_DELIVERY", None, 45),
)

PROMO_CAMPAIGN_MAP: dict[str, str] = {
    "PR3-PROMO-001": "GLOBAL_LOCKER_2026",
    "MAGALU10": "MARKETPLACE_BR",
    "ML-LOCKER-15": "MARKETPLACE_BR",
    "INPOST-PT-FIX": "LOCKER_PT",
    "INPOST-UK-5": "LOCKER_EU_CORE",
    "DHL-PACK-5": "LOCKER_EU_CORE",
    "DHL-DE-PACK-7": "LOCKER_EU_CORE",
    "AMZN-HUB-BUNDLE": "MARKETPLACE_EU",
    "WORTEN-FIXED": "LOCKER_PT",
    "CORTEINGLES-BXGY": "MARKETPLACE_EU",
    "SHOPEE-FREE": "MARKETPLACE_BR",
    "TIKTOK-BUNDLE": "MARKETPLACE_BR",
    "DPD-LOCKER-8": "LOCKER_EU_CORE",
    "USPS-HUB-FIX": "CARRIER_US",
    "CORREIOS-LOCKER-12": "LOCKER_BR",
    "CTT-LOCKER-PT": "LOCKER_PT",
    "GLS-LOCKER-6": "LOCKER_EU_CORE",
    "UPS-ACCESS-FIX": "CARRIER_US",
    "PACKETA-LOCKER-10": "LOCKER_EU_CORE",
    "MONDIAL-RELAY-8": "LOCKER_EU_CORE",
    "PONTO-MAGALU-FIX": "LOCKER_BR",
    "CAINIAO-HUB-5": "AGGREGATOR_GLOBAL",
    "MELHOR-ENVIO-10": "AGGREGATOR_GLOBAL",
    "VINTED-GO-FIX": "LOCKER_EU_CORE",
    "IFOOD-LOCKER-10": "FOOD_LOCKER_GLOBAL",
    "UBER-LOCKER-FIX": "FOOD_LOCKER_GLOBAL",
    "GLOVO-PICKUP-8": "FOOD_LOCKER_GLOBAL",
    "DELIVEROO-LOCKER": "FOOD_LOCKER_GLOBAL",
}

PROMO_SCOPES_SEED: dict[str, list[tuple[str, str, str]]] = {
    "PR3-PROMO-001": [("CHANNEL", "LOCKER", "INCLUDE")],
    "MAGALU10": [
        ("PLAYER", "MAGALU", "INCLUDE"),
        ("COUNTRY", "BR", "INCLUDE"),
        ("CHANNEL", "MARKETPLACE", "INCLUDE"),
        ("LOCKER_OPERATOR", "MAGALU", "INCLUDE"),
    ],
    "ML-LOCKER-15": [
        ("PLAYER", "MERCADO_LIVRE", "INCLUDE"),
        ("COUNTRY", "BR", "INCLUDE"),
        ("CHANNEL", "LOCKER", "INCLUDE"),
        ("LOCKER_OPERATOR", "MERCADO_LIVRE", "INCLUDE"),
    ],
    "INPOST-PT-FIX": [
        ("PLAYER", "INPOST", "INCLUDE"),
        ("LOCKER_OPERATOR", "INPOST", "INCLUDE"),
        ("COUNTRY", "PT", "INCLUDE"),
    ],
    "INPOST-UK-5": [("PLAYER", "INPOST", "INCLUDE"), ("COUNTRY", "UK", "INCLUDE")],
    "DHL-PACK-5": [
        ("PLAYER", "DHL", "INCLUDE"),
        ("LOCKER_OPERATOR", "DHL", "INCLUDE"),
        ("MARKETPLACE", "DHL_PACKSTATION", "INCLUDE"),
    ],
    "DHL-DE-PACK-7": [("PLAYER", "DHL", "INCLUDE"), ("COUNTRY", "DE", "INCLUDE"), ("LOCKER_OPERATOR", "DHL", "INCLUDE")],
    "WORTEN-FIXED": [("PLAYER", "WORTEN", "INCLUDE"), ("COUNTRY", "PT", "INCLUDE"), ("CHANNEL", "PUDO", "INCLUDE")],
    "CORTEINGLES-BXGY": [
        ("PLAYER", "EL_CORTE_INGLES", "INCLUDE"),
        ("COUNTRY", "ES", "INCLUDE"),
        ("CHANNEL", "PUDO", "INCLUDE"),
    ],
    "DPD-LOCKER-8": [("PLAYER", "DPD", "INCLUDE"), ("LOCKER_OPERATOR", "DPD", "INCLUDE"), ("CHANNEL", "LOCKER", "INCLUDE")],
    "USPS-HUB-FIX": [("PLAYER", "USPS", "INCLUDE"), ("COUNTRY", "US", "INCLUDE"), ("LOCKER_OPERATOR", "USPS", "INCLUDE")],
    "AMZN-HUB-BUNDLE": [
        ("PLAYER", "AMAZON_HUB", "INCLUDE"),
        ("MARKETPLACE", "AMAZON_HUB", "INCLUDE"),
        ("CHANNEL", "LOCKER", "INCLUDE"),
    ],
    "SHOPEE-FREE": [("PLAYER", "SHOPEE", "INCLUDE"), ("COUNTRY", "BR", "INCLUDE")],
    "TIKTOK-BUNDLE": [("PLAYER", "TIKTOK_SHOP", "INCLUDE"), ("COUNTRY", "BR", "INCLUDE")],
    "CORREIOS-LOCKER-12": [
        ("PLAYER", "CORREIOS", "INCLUDE"),
        ("LOCKER_OPERATOR", "CORREIOS", "INCLUDE"),
        ("COUNTRY", "BR", "INCLUDE"),
        ("CHANNEL", "LOCKER", "INCLUDE"),
    ],
    "CTT-LOCKER-PT": [
        ("PLAYER", "CTT", "INCLUDE"),
        ("LOCKER_OPERATOR", "CTT", "INCLUDE"),
        ("COUNTRY", "PT", "INCLUDE"),
    ],
    "GLS-LOCKER-6": [("PLAYER", "GLS", "INCLUDE"), ("LOCKER_OPERATOR", "GLS", "INCLUDE")],
    "UPS-ACCESS-FIX": [("PLAYER", "UPS", "INCLUDE"), ("COUNTRY", "US", "INCLUDE")],
    "PACKETA-LOCKER-10": [("PLAYER", "PACKETA", "INCLUDE"), ("LOCKER_OPERATOR", "PACKETA", "INCLUDE")],
    "MONDIAL-RELAY-8": [("PLAYER", "MONDIAL_RELAY", "INCLUDE"), ("LOCKER_OPERATOR", "MONDIAL_RELAY", "INCLUDE")],
    "PONTO-MAGALU-FIX": [("PLAYER", "PONTO_MAGALU", "INCLUDE"), ("PLAYER", "MAGALU", "INCLUDE"), ("COUNTRY", "BR", "INCLUDE")],
    "CAINIAO-HUB-5": [("PLAYER", "CAINIAO", "INCLUDE"), ("CHANNEL", "AGGREGATOR", "INCLUDE")],
    "MELHOR-ENVIO-10": [("PLAYER", "MELHOR_ENVIO", "INCLUDE"), ("COUNTRY", "BR", "INCLUDE")],
    "VINTED-GO-FIX": [("PLAYER", "VINTED_GO", "INCLUDE"), ("LOCKER_OPERATOR", "VINTED_GO", "INCLUDE")],
    "IFOOD-LOCKER-10": [("PLAYER", "IFOOD", "INCLUDE"), ("COUNTRY", "BR", "INCLUDE"), ("CHANNEL", "FOOD_DELIVERY", "INCLUDE")],
    "UBER-LOCKER-FIX": [("PLAYER", "UBER_EATS", "INCLUDE"), ("COUNTRY", "BR", "INCLUDE")],
    "GLOVO-PICKUP-8": [("PLAYER", "GLOVO", "INCLUDE"), ("COUNTRY", "ES", "INCLUDE")],
    "DELIVEROO-LOCKER": [("PLAYER", "DELIVEROO", "INCLUDE"), ("COUNTRY", "GB", "INCLUDE")],
}


def seed_promotion_campaigns(db: Session) -> tuple[int, int, dict[str, str]]:
    import json

    meta_sql = (
        "CAST(:metadata_json AS JSONB)"
        if db.get_bind().dialect.name == "postgresql"
        else ":metadata_json"
    )
    now = datetime.now(timezone.utc)
    inserted = 0
    skipped = 0
    campaign_ids: dict[str, str] = {}
    for code, name, family, country, priority in CAMPAIGNS_SEED:
        existing = db.execute(
            text("SELECT id FROM promotion_campaigns WHERE code = :code"),
            {"code": code},
        ).mappings().first()
        if existing:
            campaign_ids[code] = str(existing.get("id"))
            skipped += 1
            continue
        cid = str(uuid4())
        campaign_ids[code] = cid
        db.execute(
            text(
                f"""
                INSERT INTO promotion_campaigns (
                    id, code, name, description, channel_family, primary_country,
                    priority, max_stack_promotions, is_active, valid_from, valid_until,
                    metadata_json, created_at, updated_at
                ) VALUES (
                    :id, :code, :name, :description, :family, :country,
                    :priority, 1, TRUE, :vf, :vu, {meta_sql}, :ca, :ua
                )
                """
            ),
            {
                "id": cid,
                "code": code,
                "name": name,
                "description": f"Seed mundial — {family}",
                "family": family,
                "country": country,
                "priority": priority,
                "vf": now,
                "vu": now + timedelta(days=400),
                "metadata_json": json.dumps(
                    {
                        "seed": True,
                        "channel_family": family,
                        "catalog_size": len(PLAYERS_REGISTRY),
                        **(
                            {"reference_players": _CAMPAIGN_PLAYER_CODES}
                            if code == "GLOBAL_LOCKER_2026"
                            else {}
                        ),
                    }
                ),
                "ca": now,
                "ua": now,
            },
        )
        inserted += 1
    db.commit()
    return inserted, skipped, campaign_ids


def _link_promotions_to_campaigns(db: Session, campaign_ids: dict[str, str]) -> None:
    for promo_code, camp_code in PROMO_CAMPAIGN_MAP.items():
        cid = campaign_ids.get(camp_code)
        if not cid:
            continue
        db.execute(
            text("UPDATE promotions SET campaign_id = :cid WHERE code = :pcode AND campaign_id IS NULL"),
            {"cid": cid, "pcode": promo_code},
        )
    db.commit()


def seed_promotion_scopes(db: Session) -> int:
    inserted = 0
    now = datetime.now(timezone.utc)
    for promo_code, scopes in PROMO_SCOPES_SEED.items():
        promo = db.execute(
            text("SELECT id FROM promotions WHERE code = :code"),
            {"code": promo_code},
        ).mappings().first()
        if not promo:
            continue
        pid = str(promo.get("id"))
        for scope_type, scope_value, mode in scopes:
            exists = db.execute(
                text(
                    """
                    SELECT 1 FROM promotion_scopes
                    WHERE promotion_id = :pid AND scope_type = :st AND scope_value = :sv AND mode = :m
                    """
                ),
                {"pid": pid, "st": scope_type, "sv": scope_value, "m": mode},
            ).scalar()
            if exists:
                continue
            db.execute(
                text(
                    """
                    INSERT INTO promotion_scopes (id, promotion_id, scope_type, scope_value, mode, created_at)
                    VALUES (:id, :pid, :st, :sv, :m, :at)
                    """
                ),
                {"id": str(uuid4()), "pid": pid, "st": scope_type, "sv": scope_value, "m": mode, "at": now},
            )
            inserted += 1
    db.commit()
    return inserted


def get_locker_players_catalog(db: Session | None = None) -> list[dict]:
    if db is not None:
        return load_players_catalog(db)
    from app.core.promotions_players_integration import _registry_catalog

    return _registry_catalog()


def seed_promotions_world(db: Session, *, created_by: str | None = None) -> dict[str, int]:
    gp: dict = {}
    link_counts: dict = {"aliases": 0, "relations": 0}
    if _table_exists(db, "global_players"):
        gp = seed_global_players_registry(db, sync_ecosystem=False)
        link_counts = seed_player_aliases_and_relations(db)
    promo_counts = seed_promotions(db, created_by=created_by)
    camp_ins, camp_skip, campaign_ids = seed_promotion_campaigns(db)
    _link_promotions_to_campaigns(db, campaign_ids)
    scopes_ins = seed_promotion_scopes(db)
    return {
        "campaigns_inserted": camp_ins,
        "campaigns_skipped": camp_skip,
        "promotions_inserted": promo_counts["inserted"],
        "promotions_skipped": promo_counts["skipped"],
        "scopes_inserted": scopes_ins,
        "global_players_inserted": int(gp.get("players", 0)),
        "player_aliases_inserted": link_counts.get("aliases", 0),
        "player_relations_inserted": link_counts.get("relations", 0),
    }
