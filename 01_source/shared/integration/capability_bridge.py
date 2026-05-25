"""Ponte compartilhada Hardware OPS ↔ Marketplace Admin — capability codes e mapeamento de players."""

from __future__ import annotations

Cap3 = tuple[str, str, str]
Cap4 = tuple[str, str, str, str]

# capability_code: ORDERS_WEBHOOK, ORDERS_POLL, TRACKING_PUSH, LOCKER_INVENTORY,
# SETTLEMENT_FEED, SELLER_OAUTH, LABEL_API, RETURNS_RMA, LOCKER_HANDOFF

TARGET_DOMAIN_BY_CAPABILITY: dict[str, str] = {
    "LOCKER_INVENTORY": "HARDWARE",
    "LOCKER_HANDOFF": "HARDWARE",
    "TRACKING_PUSH": "ORDER_PICKUP",
    "LABEL_API": "ORDER_PICKUP",
    "ORDERS_WEBHOOK": "ORDER_PICKUP",
    "ORDERS_POLL": "ORDER_PICKUP",
    "RETURNS_RMA": "ORDER_PICKUP",
    "SELLER_OAUTH": "MARKETPLACE",
    "SETTLEMENT_FEED": "FINANCE",
}

CARRIER_LOCKER_STANDARD: list[Cap3] = [
    ("TRACKING_PUSH", "WEBHOOK", "INBOUND"),
    ("LABEL_API", "REST", "OUTBOUND"),
    ("LOCKER_INVENTORY", "REST", "OUTBOUND"),
    ("RETURNS_RMA", "REST", "OUTBOUND"),
]

CARRIER_POSTAL_STANDARD: list[Cap3] = [
    ("TRACKING_PUSH", "REST", "INBOUND"),
    ("LABEL_API", "REST", "OUTBOUND"),
    ("LOCKER_INVENTORY", "REST", "OUTBOUND"),
    ("RETURNS_RMA", "REST", "OUTBOUND"),
]

LOCKER_NETWORK_STANDARD: list[Cap3] = [
    ("LOCKER_INVENTORY", "REST", "OUTBOUND"),
    ("TRACKING_PUSH", "WEBHOOK", "INBOUND"),
    ("LABEL_API", "REST", "OUTBOUND"),
]

AGGREGATOR_STANDARD: list[Cap3] = [
    ("LABEL_API", "REST", "OUTBOUND"),
    ("TRACKING_PUSH", "WEBHOOK", "INBOUND"),
]

FOOD_DELIVERY_STANDARD: list[Cap3] = [
    ("ORDERS_WEBHOOK", "WEBHOOK", "INBOUND"),
    ("LOCKER_HANDOFF", "REST", "OUTBOUND"),
]

MARKETPLACE_STANDARD: list[Cap3] = [
    ("ORDERS_WEBHOOK", "WEBHOOK", "INBOUND"),
    ("ORDERS_POLL", "REST", "OUTBOUND"),
    ("SELLER_OAUTH", "OAUTH2", "OUTBOUND"),
]

ECOMMERCE_STANDARD: list[Cap3] = [
    ("ORDERS_POLL", "REST", "OUTBOUND"),
    ("ORDERS_WEBHOOK", "WEBHOOK", "INBOUND"),
]

# Overrides explícitos (espelho marketplace channel_players_catalog)
PLAYER_CAPABILITY_OVERRIDES: dict[str, list[Cap3]] = {
    "INPOST": [
        ("LOCKER_INVENTORY", "REST", "OUTBOUND"),
        ("TRACKING_PUSH", "WEBHOOK", "INBOUND"),
        ("LABEL_API", "REST", "OUTBOUND"),
    ],
    "DHL": [
        ("TRACKING_PUSH", "WEBHOOK", "INBOUND"),
        ("LABEL_API", "REST", "OUTBOUND"),
        ("LOCKER_INVENTORY", "REST", "OUTBOUND"),
    ],
    "DHL-PACKSTATION": [
        ("TRACKING_PUSH", "WEBHOOK", "INBOUND"),
        ("LABEL_API", "REST", "OUTBOUND"),
        ("LOCKER_INVENTORY", "REST", "OUTBOUND"),
    ],
    "USPS": [
        ("TRACKING_PUSH", "REST", "INBOUND"),
        ("LABEL_API", "REST", "OUTBOUND"),
        ("LOCKER_INVENTORY", "REST", "OUTBOUND"),
    ],
    "MAGALU": [
        ("ORDERS_WEBHOOK", "WEBHOOK", "INBOUND"),
        ("SELLER_OAUTH", "OAUTH2", "OUTBOUND"),
        ("SETTLEMENT_FEED", "REST", "INBOUND"),
    ],
    "MERCADOLIVRE": [
        ("ORDERS_POLL", "REST", "OUTBOUND"),
        ("ORDERS_WEBHOOK", "WEBHOOK", "INBOUND"),
        ("SELLER_OAUTH", "OAUTH2", "OUTBOUND"),
    ],
    "AMAZON-HUB-US": [
        ("LOCKER_INVENTORY", "REST", "OUTBOUND"),
        ("ORDERS_POLL", "REST", "OUTBOUND"),
    ],
    "AMAZON_US": [
        ("LOCKER_INVENTORY", "REST", "OUTBOUND"),
        ("ORDERS_POLL", "REST", "OUTBOUND"),
    ],
    "AMAZON-BR": [
        ("ORDERS_POLL", "REST", "OUTBOUND"),
        ("LOCKER_INVENTORY", "REST", "OUTBOUND"),
        ("SETTLEMENT_FEED", "REST", "INBOUND"),
    ],
    "AMAZON_BR": [
        ("ORDERS_POLL", "REST", "OUTBOUND"),
        ("LOCKER_INVENTORY", "REST", "OUTBOUND"),
        ("SETTLEMENT_FEED", "REST", "INBOUND"),
    ],
    "MELHOR-ENVIO": [
        ("LABEL_API", "REST", "OUTBOUND"),
        ("TRACKING_PUSH", "WEBHOOK", "INBOUND"),
    ],
    "MELHOR_ENVIO": [
        ("LABEL_API", "REST", "OUTBOUND"),
        ("TRACKING_PUSH", "WEBHOOK", "INBOUND"),
    ],
    "IFOOD": [
        ("ORDERS_WEBHOOK", "WEBHOOK", "INBOUND"),
        ("LOCKER_HANDOFF", "REST", "OUTBOUND"),
    ],
    "TIKTOK-SHOP": [
        ("ORDERS_WEBHOOK", "WEBHOOK", "INBOUND"),
        ("SELLER_OAUTH", "OAUTH2", "OUTBOUND"),
    ],
    "TIKTOK_SHOP": [
        ("ORDERS_WEBHOOK", "WEBHOOK", "INBOUND"),
        ("SELLER_OAUTH", "OAUTH2", "OUTBOUND"),
    ],
}

CARRIER_POSTAL_PLAYER_CODES = frozenset(
    {
        "USPS",
        "CORREIOS",
        "CTT",
        "ROYAL-MAIL",
        "LA-POSTE",
        "COLISSIMO",
        "CORREOS-ES",
        "CORREOS_ES",
        "SWISS-POST",
        "SWISS_POST",
        "AUSPOST",
        "BRING",
        "POSTNORD",
        "BLUE-DART",
        "BLUE_DART",
    }
)

# hardware player_code → marketplace channel partner `code`
HARDWARE_TO_MARKETPLACE_CODE: dict[str, str] = {
    "INPOST": "INPOST",
    "DHL-PACKSTATION": "DHL",
    "DPD-LOCKER": "DPD",
    "SWIPBOX": "SWIPBOX",
    "CLEVERON": "CLEVERON",
    "BLOQIT": "BLOQ",
    "PACKETA": "PACKETA",
    "PICKUP-PL": "PICKUP_POLAND",
    "QUADIENT": "QUADIENT",
    "MONDIAL-RELAY": "MONDIAL_RELAY",
    "EVRI": "EVRI",
    "MAGALU": "MAGALU",
    "MERCADOLIVRE": "MERCADOLIVRE",
    "AMAZON-HUB-US": "AMAZON_US",
    "AMAZON-BR": "AMAZON_BR",
    "AMAZON-ES": "AMAZON_ES",
    "WORTEN": "WORTEN",
    "EL-CORTE-INGLES": "EL_CORTE_INGLES",
    "SHOPEE": "SHOPEE",
    "SHEIN": "SHEIN",
    "TEMU": "TEMU",
    "TIKTOK-SHOP": "TIKTOK_SHOP",
    "WALMART": "WALMART",
    "RAKUTEN": "RAKUTEN",
    "CDISCOUNT": "CDISCOUNT",
    "OTTO": "OTTO",
    "FLIPKART": "FLIPKART",
    "AMERICANAS": "AMERICANAS",
    "FNAC": "FNAC",
    "CARREFOUR": "CARREFOUR",
    "ZALANDO": "ZALANDO",
    "CORREIOS": "CORREIOS",
    "CTT": "CTT",
    "USPS": "USPS",
    "ROYAL-MAIL": "ROYAL_MAIL",
    "LA-POSTE": "LA_POSTE",
    "COLISSIMO": "COLISSIMO",
    "HERMES-DE": "HERMES_DE",
    "YODEL": "YODEL",
    "SWISS-POST": "SWISS_POST",
    "AUSPOST": "AUSPOST",
    "BLUE-DART": "BLUE_DART",
    "BRING": "BRING",
    "POSTNORD": "POSTNORD",
    "UPS": "UPS",
    "FEDEX": "FEDEX",
    "GLS": "GLS",
    "JADLOG": "JADLOG",
    "LOGGI": "LOGGI",
    "CORREOS-ES": "CORREOS_ES",
    "CAINIAO": "CAINIAO",
    "MELHOR-ENVIO": "MELHOR_ENVIO",
    "INTELIPOST": "INTELIPOST",
    "EASYPOST": "EASYPOST",
    "SHIPPO": "SHIPPO",
    "PARCEL2GO": "PARCEL2GO",
    "IFOOD": "IFOOD",
    "RAPPI": "RAPPI",
    "VINTEDGO": "VINTED",
}

MARKETPLACE_TO_HARDWARE_CODE: dict[str, str] = {v: k for k, v in HARDWARE_TO_MARKETPLACE_CODE.items()}

HARDWARE_TO_MARKETPLACE_PARTNER_ID: dict[str, str] = {
    "INPOST": "mcp-inpost",
    "DHL-PACKSTATION": "mcp-dhl",
    "DPD-LOCKER": "mcp-dpd",
    "MAGALU": "mcp-magalu",
    "MERCADOLIVRE": "mcp-meli",
    "CORREIOS": "mcp-correios",
    "CTT": "mcp-ctt",
    "USPS": "mcp-usps",
    "MELHOR-ENVIO": "mcp-melhor-envio",
    "IFOOD": "mcp-ifood",
    "CAINIAO": "mcp-cainiao",
}

MODE_SCORES: dict[str, float] = {
    "LOCKER_NETWORK_API": 12.0,
    "BIDIRECTIONAL": 10.0,
    "AGGREGATOR": 8.0,
    "DIRECT_API": 6.0,
    "WEBHOOK_INBOUND": 4.0,
}

READINESS_BANDS = ("GO_LIVE", "PILOT", "PLANNED", "BLOCKED")


def to_hardware_capabilities(caps: list[Cap3]) -> list[Cap4]:
    out: list[Cap4] = []
    for cap_code, protocol, direction in caps:
        out.append((cap_code, protocol, direction, TARGET_DOMAIN_BY_CAPABILITY.get(cap_code, "HARDWARE")))
    return out


def default_capabilities_for_player(
    *,
    player_code: str,
    segment: str,
    parent_group: str,
    integration_mode: str = "DIRECT_API",
    supports_lockers: bool = True,
    supports_marketplace: bool = False,
    supports_food_delivery: bool = False,
    supports_aggregation: bool = False,
) -> list[Cap3]:
    if player_code in PLAYER_CAPABILITY_OVERRIDES:
        return list(PLAYER_CAPABILITY_OVERRIDES[player_code])
    mkt_code = HARDWARE_TO_MARKETPLACE_CODE.get(player_code, player_code)
    if mkt_code in PLAYER_CAPABILITY_OVERRIDES:
        return list(PLAYER_CAPABILITY_OVERRIDES[mkt_code])

    if parent_group == "PAYMENTS_FISCAL" or segment == "PAYMENTS":
        return []
    if segment == "FOOD_DELIVERY" or supports_food_delivery or parent_group == "FOOD_DELIVERY":
        return list(FOOD_DELIVERY_STANDARD)
    if segment == "AGGREGATOR" or segment == "LOGISTICS_HUB" or supports_aggregation:
        return list(AGGREGATOR_STANDARD)
    if segment == "CARRIER_LOCKER" or parent_group == "CARRIER_LAST_MILE":
        if player_code in CARRIER_POSTAL_PLAYER_CODES or mkt_code in CARRIER_POSTAL_PLAYER_CODES:
            return list(CARRIER_POSTAL_STANDARD)
        return list(CARRIER_LOCKER_STANDARD)
    if segment in {"MARKETPLACE_LOCKER", "HYBRID"} or (supports_marketplace and supports_lockers):
        return list(MARKETPLACE_STANDARD)
    if segment in {"ECOMMERCE_CHANNEL", "COLLECTION_POINT"} and supports_marketplace:
        return list(ECOMMERCE_STANDARD)
    if segment in {"LOCKER_NETWORK", "NETWORK_OPERATOR"} and supports_lockers:
        return list(LOCKER_NETWORK_STANDARD)
    return []


def marketplace_code_for_hardware(player_code: str, marketplace_channel_code: str | None = None) -> str | None:
    if marketplace_channel_code:
        return marketplace_channel_code
    return HARDWARE_TO_MARKETPLACE_CODE.get(player_code)


def expected_hardware_capabilities(
    *,
    player_code: str,
    segment: str,
    parent_group: str,
    integration_mode: str = "DIRECT_API",
    supports_lockers: bool = True,
    supports_marketplace: bool = False,
    supports_food_delivery: bool = False,
    supports_aggregation: bool = False,
    explicit: list[Cap4] | None = None,
) -> list[Cap4]:
    if explicit:
        return list(explicit)
    caps3 = default_capabilities_for_player(
        player_code=player_code,
        segment=segment,
        parent_group=parent_group,
        integration_mode=integration_mode,
        supports_lockers=supports_lockers,
        supports_marketplace=supports_marketplace,
        supports_food_delivery=supports_food_delivery,
        supports_aggregation=supports_aggregation,
    )
    return to_hardware_capabilities(caps3)


def score_player_readiness(
    *,
    capability_count: int,
    integration_mode: str,
    parent_group: str,
    supports_lockers: bool,
    operator_id: str | None,
    regions_count: int,
    marketplace_linked: bool,
) -> tuple[float, float, float, float, str, list[str]]:
    blockers: list[str] = []
    score_capabilities = min(40.0, capability_count * 8.0)

    score_api = 15.0 if marketplace_linked else 0.0
    if not marketplace_linked and parent_group in ("MARKETPLACE", "CARRIER_LAST_MILE", "LOCKER_NETWORK"):
        blockers.append("missing_marketplace_link")

    score_ops = 0.0
    if operator_id:
        score_ops += 10.0
    elif supports_lockers or parent_group in ("LOCKER_NETWORK", "CARRIER_LAST_MILE"):
        blockers.append("missing_operator_ref")

    score_ops += MODE_SCORES.get(integration_mode or "", 3.0)
    score_ops += min(15.0, regions_count * 3.0)
    if supports_lockers:
        score_ops += 5.0
    score_ops = min(45.0, score_ops)

    score_total = min(100.0, score_capabilities + score_api + score_ops)

    if capability_count == 0 and parent_group in ("MARKETPLACE", "LOCKER_NETWORK", "CARRIER_LAST_MILE"):
        blockers.append("no_capabilities_defined")
    if parent_group == "LOGISTICS_PLATFORM" and capability_count == 0:
        blockers.append("aggregator_without_capabilities")

    if score_total >= 75 and capability_count >= 2 and not blockers:
        band = "GO_LIVE"
    elif score_total >= 50:
        band = "PILOT"
    elif score_total >= 25:
        band = "PLANNED"
    else:
        band = "BLOCKED"

    return score_total, score_capabilities, score_api, score_ops, band, blockers
