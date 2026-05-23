"""
Catálogo de referência — redes de lockers / pontos de coleta / marketplaces (nível mundial).

Usado pelo seed RENTAL e pelo endpoint GET /rentals/ecosystem/catalog.
Players prioritários: InPost, DHL, Magalu, Mercado Livre, Amazon, DPD, Correios, CTT,
Worten, El Corte Inglés + SwipBox, Cleveron, Bloq.it, Royal Mail, La Poste, etc.
"""
from __future__ import annotations

from typing import Any, TypedDict


class LockerNetworkDef(TypedDict, total=False):
    id: str
    code: str
    name: str
    network_type: str
    market_segment: str
    global_player_code: str | None
    hardware_vendor: str | None
    countries: list[str]
    website_url: str | None
    region_group: str


# network_type: LOCKER_NETWORK | COLLECTION_POINT | MARKETPLACE_HUB | AGGREGATOR | CARRIER_OPERATED
# market_segment: PARCEL_LOCKER | CARRIER | MARKETPLACE | PUDO_RETAIL | AGGREGATOR | FOOD_DELIVERY

_BASE_NETWORKS: list[LockerNetworkDef] = [
    # —— Europa — locker-native ——
    {
        "id": "net-inpost",
        "code": "INPOST",
        "name": "InPost Parcel Lockers",
        "network_type": "LOCKER_NETWORK",
        "hardware_vendor": "InPost",
        "countries": ["PL", "UK", "FR", "ES", "IT", "NL", "BE"],
        "website_url": "https://inpost.com",
        "region_group": "EU",
    },
    {
        "id": "net-dpd",
        "code": "DPD",
        "name": "DPD Pickup / Locker",
        "network_type": "LOCKER_NETWORK",
        "hardware_vendor": "DPD",
        "countries": ["DE", "FR", "NL", "BE", "PL", "UK", "ES"],
        "website_url": "https://www.dpd.com",
        "region_group": "EU",
    },
    {
        "id": "net-dhl-packstation",
        "code": "DHL_PACK",
        "name": "DHL Packstation",
        "network_type": "LOCKER_NETWORK",
        "hardware_vendor": "DHL",
        "countries": ["DE", "AT", "CH"],
        "website_url": "https://www.dhl.de",
        "region_group": "EU",
    },
    {
        "id": "net-dhl-parcel",
        "code": "DHL",
        "name": "DHL eCommerce / Parcel Lockers",
        "network_type": "CARRIER_OPERATED",
        "hardware_vendor": "DHL",
        "countries": ["DE", "NL", "UK", "US", "CN"],
        "website_url": "https://www.dhl.com",
        "region_group": "GLOBAL",
    },
    {
        "id": "net-royalmail",
        "code": "ROYALMAIL",
        "name": "Royal Mail Parcel Collect",
        "network_type": "LOCKER_NETWORK",
        "hardware_vendor": "Quadient",
        "countries": ["UK"],
        "website_url": "https://www.royalmail.com",
        "region_group": "EU",
    },
    {
        "id": "net-laposte",
        "code": "LAPOSTE",
        "name": "La Poste Pickup / Consignes",
        "network_type": "LOCKER_NETWORK",
        "hardware_vendor": "NeoPost",
        "countries": ["FR"],
        "website_url": "https://www.laposte.fr",
        "region_group": "EU",
    },
    {
        "id": "net-colissimo",
        "code": "COLISSIMO",
        "name": "Colissimo & Pickup Stations",
        "network_type": "LOCKER_NETWORK",
        "hardware_vendor": None,
        "countries": ["FR"],
        "website_url": "https://www.colissimo.fr",
        "region_group": "EU",
    },
    {
        "id": "net-hermes",
        "code": "HERMES",
        "name": "Hermes ParcelShops & Lockers (DE/UK)",
        "network_type": "LOCKER_NETWORK",
        "hardware_vendor": "Hermes",
        "countries": ["DE", "UK", "AT"],
        "website_url": "https://www.hermesworld.com",
        "region_group": "EU",
    },
    {
        "id": "net-ctt",
        "code": "CTT",
        "name": "CTT Locky / Pontos CTT",
        "network_type": "LOCKER_NETWORK",
        "hardware_vendor": "CTT",
        "countries": ["PT"],
        "website_url": "https://www.ctt.pt",
        "region_group": "EU",
    },
    {
        "id": "net-worten",
        "code": "WORTEN",
        "name": "Worten Pontos de Entrega",
        "network_type": "COLLECTION_POINT",
        "hardware_vendor": None,
        "countries": ["PT", "ES"],
        "website_url": "https://www.worten.pt",
        "region_group": "EU",
    },
    {
        "id": "net-eci",
        "code": "ECI",
        "name": "El Corte Inglés — Collection Point",
        "network_type": "COLLECTION_POINT",
        "hardware_vendor": None,
        "countries": ["ES", "PT"],
        "website_url": "https://www.elcorteingles.es",
        "region_group": "EU",
    },
    {
        "id": "net-packeta",
        "code": "PACKETA",
        "name": "Packeta (Zásilkovna) Pickup Points",
        "network_type": "COLLECTION_POINT",
        "hardware_vendor": "Packeta",
        "countries": ["CZ", "SK", "HU", "RO", "PL"],
        "website_url": "https://www.packeta.com",
        "region_group": "EU",
    },
    {
        "id": "net-vinted-go",
        "code": "VINTED_GO",
        "name": "Vinted Go Lockers",
        "network_type": "LOCKER_NETWORK",
        "hardware_vendor": "Vinted",
        "countries": ["FR", "NL", "BE", "ES", "PT", "UK"],
        "website_url": "https://www.vintedgo.com",
        "region_group": "EU",
    },
    {
        "id": "net-bloqit",
        "code": "BLOQIT",
        "name": "Bloq.it Smart Lockers",
        "network_type": "LOCKER_NETWORK",
        "hardware_vendor": "Bloq.it",
        "countries": ["IT", "ES", "FR", "UK"],
        "website_url": "https://bloq.it",
        "region_group": "EU",
    },
    {
        "id": "net-swipbox",
        "code": "SWIPBOX",
        "name": "SwipBox Outdoor Lockers",
        "network_type": "LOCKER_NETWORK",
        "hardware_vendor": "SwipBox",
        "countries": ["DK", "NO", "SE", "FI", "DE"],
        "website_url": "https://www.swipbox.com",
        "region_group": "EU",
    },
    {
        "id": "net-cleveron",
        "code": "CLEVERON",
        "name": "Cleveron Parcel Lockers",
        "network_type": "LOCKER_NETWORK",
        "hardware_vendor": "Cleveron",
        "countries": ["EE", "LV", "LT", "PL", "DE"],
        "website_url": "https://www.cleveron.com",
        "region_group": "EU",
    },
    {
        "id": "net-bring",
        "code": "BRING",
        "name": "Bring / Posten Pickup",
        "network_type": "CARRIER_OPERATED",
        "hardware_vendor": None,
        "countries": ["NO", "SE", "DK", "FI"],
        "website_url": "https://www.bring.com",
        "region_group": "EU",
    },
    {
        "id": "net-postnord",
        "code": "POSTNORD",
        "name": "PostNord Parcel Lockers",
        "network_type": "LOCKER_NETWORK",
        "hardware_vendor": "PostNord",
        "countries": ["SE", "DK", "NO", "FI"],
        "website_url": "https://www.postnord.com",
        "region_group": "EU",
    },
    {
        "id": "net-swisspost",
        "code": "SWISSPOST",
        "name": "Swiss Post My Post 24",
        "network_type": "LOCKER_NETWORK",
        "hardware_vendor": "Swiss Post",
        "countries": ["CH"],
        "website_url": "https://www.post.ch",
        "region_group": "EU",
    },
    # —— Américas ——
    {
        "id": "net-correios",
        "code": "CORREIOS",
        "name": "Correios Lockers / Agência Locker",
        "network_type": "CARRIER_OPERATED",
        "hardware_vendor": "Correios",
        "countries": ["BR"],
        "website_url": "https://www.correios.com.br",
        "region_group": "AMER",
    },
    {
        "id": "net-magalu",
        "code": "MAGALU",
        "name": "Ponto Magalu",
        "network_type": "COLLECTION_POINT",
        "hardware_vendor": None,
        "countries": ["BR"],
        "website_url": "https://www.magazineluiza.com.br",
        "region_group": "AMER",
    },
    {
        "id": "net-mercadolivre",
        "code": "MELI",
        "name": "Mercado Livre Envios / Lockers",
        "network_type": "MARKETPLACE_HUB",
        "hardware_vendor": None,
        "countries": ["BR", "AR", "MX", "CL", "CO"],
        "website_url": "https://www.mercadolivre.com.br",
        "region_group": "AMER",
    },
    {
        "id": "net-amazon-hub",
        "code": "AMAZON_HUB",
        "name": "Amazon Hub (Counter + Locker)",
        "network_type": "MARKETPLACE_HUB",
        "hardware_vendor": "Amazon",
        "countries": ["US", "UK", "DE", "FR", "IT", "ES", "JP"],
        "website_url": "https://www.amazon.com/amazonhub",
        "region_group": "GLOBAL",
    },
    {
        "id": "net-usps",
        "code": "USPS",
        "name": "USPS Parcel Lockers / gopost",
        "network_type": "CARRIER_OPERATED",
        "hardware_vendor": "USPS",
        "countries": ["US"],
        "website_url": "https://www.usps.com",
        "region_group": "AMER",
    },
    # —— Ásia / agregadores ——
    {
        "id": "net-cainiao",
        "code": "CAINIAO",
        "name": "Cainiao / Alibaba Logistics Lockers",
        "network_type": "AGGREGATOR",
        "hardware_vendor": "Cainiao",
        "countries": ["CN", "ES", "BR", "RU"],
        "website_url": "https://www.cainiao.com",
        "region_group": "APAC",
    },
    {
        "id": "net-quadient",
        "code": "QUADIENT",
        "name": "Quadient Parcel Pending",
        "network_type": "LOCKER_NETWORK",
        "hardware_vendor": "Quadient",
        "countries": ["UK", "FR", "US", "AU"],
        "website_url": "https://www.quadient.com",
        "region_group": "GLOBAL",
    },
]

from app.core.rental_locker_ecosystem_extra import (  # noqa: E402
    ECOSYSTEM_NETWORK_RELATIONS,
    EXTRA_ECOSYSTEM_OPERATORS,
    EXTRA_ECOSYSTEM_PLANS,
    EXTRA_LOCKER_NETWORKS,
    EXTRA_WEBHOOK_TENANTS,
    NETWORK_GLOBAL_PLAYER_CODES,
)

LOCKER_ECOSYSTEM_NETWORKS: list[LockerNetworkDef] = _BASE_NETWORKS + EXTRA_LOCKER_NETWORKS  # type: ignore[operator]

_DEFAULT_SEGMENT: dict[str, str] = {
    "LOCKER_NETWORK": "PARCEL_LOCKER",
    "COLLECTION_POINT": "PUDO_RETAIL",
    "MARKETPLACE_HUB": "MARKETPLACE",
    "AGGREGATOR": "AGGREGATOR",
    "CARRIER_OPERATED": "CARRIER",
}


def enrich_network_metadata(network: LockerNetworkDef) -> LockerNetworkDef:
    """Preenche market_segment e global_player_code quando ausentes."""
    out = dict(network)
    code = str(out.get("code") or "")
    out.setdefault("market_segment", _DEFAULT_SEGMENT.get(str(out.get("network_type") or ""), "PARCEL_LOCKER"))
    out.setdefault("global_player_code", NETWORK_GLOBAL_PLAYER_CODES.get(code))
    return out  # type: ignore[return-value]


LOCKER_ECOSYSTEM_NETWORKS = [enrich_network_metadata(n) for n in LOCKER_ECOSYSTEM_NETWORKS]

LOCKER_ECOSYSTEM_PLANS: list[dict[str, Any]] = [
    {
        "id": "rental-plan-inpost-m",
        "network_id": "net-inpost",
        "slot_size": "M",
        "name": "InPost — compartimento M (mensal)",
        "description": "Rede InPost Europa; integração DPD / Royal Mail em corredores.",
        "billing_cycle": "MONTHLY",
        "amount_cents": 14900,
    },
    {
        "id": "rental-plan-dpd-s",
        "network_id": "net-dpd",
        "slot_size": "S",
        "name": "DPD Pickup Locker — S",
        "billing_cycle": "MONTHLY",
        "amount_cents": 12900,
    },
    {
        "id": "rental-plan-dhl-packstation",
        "network_id": "net-dhl-packstation",
        "slot_size": "S",
        "name": "DHL Packstation — S semanal",
        "description": "Alemanha / Áustria — Packstation oficial DHL.",
        "billing_cycle": "WEEKLY",
        "amount_cents": 4900,
    },
    {
        "id": "rental-plan-correios-m",
        "network_id": "net-correios",
        "slot_size": "M",
        "name": "Correios Locker — M",
        "description": "Lockers Correios e parceiros nacionais.",
        "billing_cycle": "MONTHLY",
        "amount_cents": 8900,
    },
    {
        "id": "rental-plan-magalu-hub",
        "network_id": "net-magalu",
        "slot_size": "M",
        "name": "Ponto Magalu — hub",
        "billing_cycle": "MONTHLY",
        "amount_cents": 11900,
    },
    {
        "id": "rental-plan-meli-hub",
        "network_id": "net-mercadolivre",
        "slot_size": "M",
        "name": "Mercado Livre — locker hub",
        "billing_cycle": "MONTHLY",
        "amount_cents": 10900,
    },
    {
        "id": "rental-plan-amazon-counter",
        "network_id": "net-amazon-hub",
        "slot_size": "S",
        "name": "Amazon Hub Counter/Locker",
        "billing_cycle": "MONTHLY",
        "amount_cents": 15900,
    },
    {
        "id": "rental-plan-ctt-m",
        "network_id": "net-ctt",
        "slot_size": "M",
        "name": "CTT Locky — M",
        "billing_cycle": "MONTHLY",
        "amount_cents": 9900,
    },
    {
        "id": "rental-plan-worten-pt",
        "network_id": "net-worten",
        "slot_size": "S",
        "name": "Worten — ponto entrega",
        "billing_cycle": "MONTHLY",
        "amount_cents": 7900,
    },
    {
        "id": "rental-plan-eci-es",
        "network_id": "net-eci",
        "slot_size": "M",
        "name": "El Corte Inglés — collection point",
        "billing_cycle": "MONTHLY",
        "amount_cents": 12500,
    },
    {
        "id": "rental-plan-swipbox-l",
        "network_id": "net-swipbox",
        "slot_size": "L",
        "name": "SwipBox / Cleveron — L trimestral",
        "billing_cycle": "QUARTERLY",
        "amount_cents": 39900,
    },
    {
        "id": "rental-plan-cainiao-br",
        "network_id": "net-cainiao",
        "slot_size": "M",
        "name": "Cainiao — corredor CN→BR",
        "billing_cycle": "MONTHLY",
        "amount_cents": 13900,
    },
] + EXTRA_ECOSYSTEM_PLANS

LOCKER_ECOSYSTEM_CORRIDORS: list[tuple[str, str, str, int, str]] = [
    ("net-inpost", "PL", "UK", 48, "EUR"),
    ("net-inpost", "FR", "ES", 36, "EUR"),
    ("net-dpd", "DE", "FR", 30, "EUR"),
    ("net-dpd", "NL", "BE", 18, "EUR"),
    ("net-dhl-packstation", "DE", "AT", 24, "EUR"),
    ("net-correios", "BR", "BR", 12, "BRL"),
    ("net-magalu", "BR", "BR", 12, "BRL"),
    ("net-mercadolivre", "BR", "AR", 96, "USD"),
    ("net-mercadolivre", "MX", "BR", 120, "USD"),
    ("net-amazon-hub", "US", "UK", 72, "USD"),
    ("net-cainiao", "CN", "BR", 120, "USD"),
    ("net-ctt", "PT", "ES", 24, "EUR"),
    ("net-worten", "PT", "ES", 28, "EUR"),
    ("net-eci", "ES", "PT", 24, "EUR"),
]

LOCKER_ECOSYSTEM_OPERATORS: list[dict[str, Any]] = [
    {"id": "op-inpost-br", "tenant_id": "tenant-inpost-br", "network_id": "net-inpost", "legal_name": "InPost Brasil", "operator_code": "INPOST_BR", "commission_bps": 350},
    {"id": "op-dpd-eu", "tenant_id": "tenant-dpd-eu", "network_id": "net-dpd", "legal_name": "DPD Group", "operator_code": "DPD_EU", "commission_bps": 380},
    {"id": "op-dhl-de", "tenant_id": "tenant-dhl-de", "network_id": "net-dhl-packstation", "legal_name": "DHL Packstation GmbH", "operator_code": "DHL_DE", "commission_bps": 400},
    {"id": "op-correios-br", "tenant_id": "tenant-correios-br", "network_id": "net-correios", "legal_name": "Empresa Brasileira de Correios", "operator_code": "CORREIOS_BR", "commission_bps": 450},
    {"id": "op-magalu", "tenant_id": "tenant-magalu", "network_id": "net-magalu", "legal_name": "Magazine Luiza Logística", "operator_code": "MAGALU_BR", "commission_bps": 500},
    {"id": "op-meli", "tenant_id": "tenant-meli", "network_id": "net-mercadolivre", "legal_name": "Mercado Livre Envios", "operator_code": "MELI_LATAM", "commission_bps": 520},
    {"id": "op-amazon-hub", "tenant_id": "tenant-amazon-hub", "network_id": "net-amazon-hub", "legal_name": "Amazon Hub Services", "operator_code": "AMAZON_HUB", "commission_bps": 480},
    {"id": "op-ctt-pt", "tenant_id": "tenant-ctt-pt", "network_id": "net-ctt", "legal_name": "CTT — Correios de Portugal", "operator_code": "CTT_PT", "commission_bps": 420},
    {"id": "op-worten", "tenant_id": "tenant-worten", "network_id": "net-worten", "legal_name": "Worten Portugal", "operator_code": "WORTEN_PT", "commission_bps": 400},
    {"id": "op-eci", "tenant_id": "tenant-eci", "network_id": "net-eci", "legal_name": "El Corte Inglés Logística", "operator_code": "ECI_ES", "commission_bps": 410},
] + EXTRA_ECOSYSTEM_OPERATORS

LOCKER_ECOSYSTEM_SLA: list[tuple[str, str, float, str, int]] = [
    ("net-inpost", "uptime_pct", 99.5, "percent", 100),
    ("net-inpost", "access_latency_ms", 800, "ms", 50),
    ("net-dpd", "uptime_pct", 99.2, "percent", 120),
    ("net-dhl-packstation", "billing_accuracy_pct", 99.9, "percent", 200),
    ("net-correios", "uptime_pct", 98.5, "percent", 150),
    ("net-magalu", "pickup_sla_hours", 24, "hours", 80),
    ("net-mercadolivre", "listing_sync_pct", 99.0, "percent", 100),
    ("net-amazon-hub", "hub_activation_hours", 48, "hours", 90),
    ("net-ctt", "uptime_pct", 99.0, "percent", 70),
    ("net-swipbox", "slot_fault_rate_pct", 0.5, "percent", 150),
    ("net-cainiao", "cross_border_clearance_hours", 72, "hours", 200),
]

LOCKER_ECOSYSTEM_WEBHOOK_TENANTS: list[str] = [
    "tenant-inpost-br",
    "tenant-dpd-eu",
    "tenant-dhl-de",
    "tenant-correios-br",
    "tenant-magalu",
    "tenant-meli",
    "tenant-amazon-hub",
    "tenant-ctt-pt",
    "tenant-worten",
    "tenant-eci",
] + EXTRA_WEBHOOK_TENANTS

# Códigos obrigatórios (smoke / QA do catálogo)
PRIORITY_NETWORK_CODES = frozenset(
    {
        "INPOST",
        "DHL_PACK",
        "DHL",
        "DPD",
        "MAGALU",
        "MELI",
        "AMAZON_HUB",
        "CORREIOS",
        "CTT",
        "WORTEN",
        "ECI",
    }
)


def ecosystem_catalog_payload() -> dict[str, Any]:
    """Payload público para OPS (sem persistência)."""
    by_region: dict[str, list[dict[str, Any]]] = {}
    by_type: dict[str, list[str]] = {}
    by_segment: dict[str, list[str]] = {}
    for n in LOCKER_ECOSYSTEM_NETWORKS:
        rg = n.get("region_group") or "OTHER"
        by_region.setdefault(rg, []).append({k: v for k, v in n.items() if k != "region_group"})
        nt = n["network_type"]
        by_type.setdefault(nt, []).append(n["code"])
        seg = n.get("market_segment") or "PARCEL_LOCKER"
        by_segment.setdefault(seg, []).append(n["code"])
    return {
        "version": "2026-05-2",
        "networks_total": len(LOCKER_ECOSYSTEM_NETWORKS),
        "priority_codes": sorted(PRIORITY_NETWORK_CODES),
        "networks": LOCKER_ECOSYSTEM_NETWORKS,
        "by_region": by_region,
        "by_type": {k: sorted(v) for k, v in by_type.items()},
        "by_segment": {k: sorted(v) for k, v in by_segment.items()},
        "relations_catalog": [
            {"from": a, "to": b, "relation_type": rt, "integration_mode": im}
            for a, b, rt, im in ECOSYSTEM_NETWORK_RELATIONS
        ],
        "plans_catalog": len(LOCKER_ECOSYSTEM_PLANS),
        "operators_catalog": len(LOCKER_ECOSYSTEM_OPERATORS),
        "integration_notes": {
            "global_players": "Use global_player_code + POST /catalog-professional/global-players/seed",
            "rental_relations": "Persistidas em rental_network_relations após seed",
        },
    }
