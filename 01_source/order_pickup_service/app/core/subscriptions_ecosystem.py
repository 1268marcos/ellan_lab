"""Catálogo de players mundiais ligados a tiers de assinatura."""
from __future__ import annotations

from typing import Any

from app.core.subscriptions_ecosystem_relations import SUBSCRIPTION_PLAYER_RELATIONS
from app.core.subscriptions_global_players import (
    GLOBAL_SUBSCRIPTION_PLAYERS,
    PRIORITY_PLAYER_CODES,
    players_by_region,
    players_by_segment,
    priority_players_payload,
    tier_player_map_from_registry,
)

_SEGMENT_TO_BUCKET = {
    "PARCEL_LOCKER": "locker_operators",
    "HARDWARE_VENDOR": "hardware_vendors",
    "MARKETPLACE": "marketplaces",
    "PUDO_RETAIL": "collection_points",
    "CARRIER": "carriers",
    "AGGREGATOR": "aggregators",
    "FOOD_DELIVERY": "food_delivery",
}


def ecosystem_catalog_payload() -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = {
        "locker_operators": [],
        "hardware_vendors": [],
        "marketplaces": [],
        "collection_points": [],
        "carriers": [],
        "aggregators": [],
        "food_delivery": [],
    }
    for p in GLOBAL_SUBSCRIPTION_PLAYERS:
        bucket = _SEGMENT_TO_BUCKET.get(str(p.get("segment")), "other")
        if bucket == "other":
            buckets.setdefault("other", []).append(p)
        else:
            buckets[bucket].append(
                {
                    "code": p["code"],
                    "name": p["name"],
                    "type": p["player_type"],
                    "segment": p.get("segment"),
                    "regions": p.get("regions", []),
                    "priority": bool(p.get("priority") or p["code"] in PRIORITY_PLAYER_CODES),
                    "default_plan": p.get("default_plan"),
                    "website": p.get("website"),
                }
            )

    tier_map = tier_player_map_from_registry()
    return {
        "version": "2026-05-26-global-v3",
        "players_total": len(GLOBAL_SUBSCRIPTION_PLAYERS),
        "priority_player_codes": sorted(PRIORITY_PLAYER_CODES),
        "priority_players": priority_players_payload(),
        "locker_operators": buckets["locker_operators"],
        "hardware_vendors": buckets["hardware_vendors"],
        "marketplaces": buckets["marketplaces"],
        "collection_points": buckets["collection_points"],
        "carriers": buckets["carriers"],
        "aggregators": buckets["aggregators"],
        "food_delivery": buckets["food_delivery"],
        "other": buckets.get("other", []),
        "player_relations": SUBSCRIPTION_PLAYER_RELATIONS,
        "relations_total": len(SUBSCRIPTION_PLAYER_RELATIONS),
        "relation_types": sorted({r["type"] for r in SUBSCRIPTION_PLAYER_RELATIONS}),
        "integration_modes": sorted({r["mode"] for r in SUBSCRIPTION_PLAYER_RELATIONS}),
        # aliases legados para UI antiga
        "networks": buckets["locker_operators"] + buckets["hardware_vendors"],
        "marketplaces_legacy": buckets["marketplaces"],
        "carriers_legacy": buckets["carriers"],
        "aggregators_legacy": buckets["aggregators"],
        "tier_player_map": tier_map,
        "by_segment": {k: [x["code"] for x in v] for k, v in players_by_segment().items()},
        "by_region": players_by_region(),
        "interoperability_notes": [
            "InPost ↔ DPD: rede locker interoperável UE",
            "Magalu / Mercado Livre: checkout com benefício PREMIUM+",
            "Amazon Hub + DHL Packstation: retirada cross-border PRO/ENTERPRISE",
            "Correios + CTT: last-mile IBÉRIA/BR no tier BASIC+",
            "Worten + El Corte Inglés: PUDO retail Península Ibérica",
            "iFood / Rappi → PUDO Magalu ou Worten: FOOD_HANDOFF com assinatura PREMIUM+",
            "Uber Eats / Deliveroo → InPost ou Amazon Hub: retirada híbrida food+parcel",
            "Melhor Envio / Intelipost: roteamento agregador para Correios, Jadlog, Loggi",
        ],
        "webhook_events": [
            "subscription.created",
            "subscription.renewed",
            "subscription.cancelled",
            "subscription.past_due",
            "subscription.trial_ended",
            "benefit.quota_exceeded",
            "entitlement.player_enabled",
            "entitlement.player_disabled",
        ],
    }
