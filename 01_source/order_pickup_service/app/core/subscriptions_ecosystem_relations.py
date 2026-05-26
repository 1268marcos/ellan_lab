"""
Relações entre players do ecossistema de assinaturas (interconnect, routing, food handoff).

relation_type:
  INTERCONNECT | MARKETPLACE_ROUTING | AGGREGATOR_ROUTING | FOOD_HANDOFF | WHITELABEL | PUDO_NETWORK
integration_mode: API | WEBHOOK | EDI | OAUTH | MTLS | MANUAL | INTERNAL
"""
from __future__ import annotations

from typing import Any

# (from_code, to_code, relation_type, integration_mode, min_plan_code, notes)
SUBSCRIPTION_PLAYER_RELATIONS: list[dict[str, Any]] = [
    {"from": "inpost", "to": "dpd", "type": "INTERCONNECT", "mode": "API", "min_plan": "PRO"},
    {"from": "inpost", "to": "royal_mail", "type": "INTERCONNECT", "mode": "EDI", "min_plan": "PRO"},
    {"from": "dpd", "to": "gls", "type": "INTERCONNECT", "mode": "API", "min_plan": "PRO"},
    {"from": "dhl", "to": "dpd", "type": "INTERCONNECT", "mode": "API", "min_plan": "PRO"},
    {"from": "mercado_livre", "to": "correios", "type": "MARKETPLACE_ROUTING", "mode": "WEBHOOK", "min_plan": "PREMIUM"},
    {"from": "mercado_livre", "to": "jadlog", "type": "MARKETPLACE_ROUTING", "mode": "API", "min_plan": "PREMIUM"},
    {"from": "magalu", "to": "correios", "type": "MARKETPLACE_ROUTING", "mode": "API", "min_plan": "PREMIUM"},
    {"from": "amazon", "to": "usps", "type": "MARKETPLACE_ROUTING", "mode": "API", "min_plan": "PRO"},
    {"from": "shopee", "to": "cainiao", "type": "MARKETPLACE_ROUTING", "mode": "API", "min_plan": "PREMIUM"},
    {"from": "temu", "to": "cainiao", "type": "AGGREGATOR_ROUTING", "mode": "API", "min_plan": "PREMIUM"},
    {"from": "melhor_envio", "to": "correios", "type": "AGGREGATOR_ROUTING", "mode": "API", "min_plan": "PREMIUM"},
    {"from": "melhor_envio", "to": "jadlog", "type": "AGGREGATOR_ROUTING", "mode": "API", "min_plan": "PREMIUM"},
    {"from": "melhor_envio", "to": "loggi", "type": "AGGREGATOR_ROUTING", "mode": "API", "min_plan": "PRO"},
    {"from": "intelipost", "to": "mercado_livre", "type": "AGGREGATOR_ROUTING", "mode": "WEBHOOK", "min_plan": "ENTERPRISE"},
    {"from": "easypost", "to": "usps", "type": "AGGREGATOR_ROUTING", "mode": "API", "min_plan": "ENTERPRISE"},
    {"from": "shippo", "to": "usps", "type": "AGGREGATOR_ROUTING", "mode": "API", "min_plan": "ENTERPRISE"},
    {"from": "cainiao", "to": "correios", "type": "AGGREGATOR_ROUTING", "mode": "EDI", "min_plan": "ENTERPRISE"},
    {"from": "worten", "to": "ctt", "type": "PUDO_NETWORK", "mode": "API", "min_plan": "PRO"},
    {"from": "el_corte_ingles", "to": "seur", "type": "PUDO_NETWORK", "mode": "API", "min_plan": "PRO"},
    {"from": "ifood", "to": "magalu", "type": "FOOD_HANDOFF", "mode": "WEBHOOK", "min_plan": "PREMIUM", "notes": "Retirada em PUDO Magalu"},
    {"from": "ifood", "to": "worten", "type": "FOOD_HANDOFF", "mode": "WEBHOOK", "min_plan": "PRO"},
    {"from": "rappi", "to": "magalu", "type": "FOOD_HANDOFF", "mode": "WEBHOOK", "min_plan": "PREMIUM"},
    {"from": "uber_eats", "to": "amazon", "type": "FOOD_HANDOFF", "mode": "API", "min_plan": "PRO", "notes": "Amazon Hub pickup"},
    {"from": "uber_eats", "to": "worten", "type": "FOOD_HANDOFF", "mode": "API", "min_plan": "PRO"},
    {"from": "glovo", "to": "mondial_relay", "type": "FOOD_HANDOFF", "mode": "MANUAL", "min_plan": "PRO"},
    {"from": "deliveroo", "to": "inpost", "type": "FOOD_HANDOFF", "mode": "API", "min_plan": "PRO"},
    {"from": "doordash", "to": "usps", "type": "FOOD_HANDOFF", "mode": "API", "min_plan": "ENTERPRISE"},
    {"from": "grabfood", "to": "shopee", "type": "FOOD_HANDOFF", "mode": "WEBHOOK", "min_plan": "ENTERPRISE"},
    {"from": "ponto_magalu", "to": "magalu", "type": "WHITELABEL", "mode": "INTERNAL", "min_plan": "PREMIUM"},
    {"from": "parcel2go", "to": "royal_mail", "type": "AGGREGATOR_ROUTING", "mode": "API", "min_plan": "ENTERPRISE"},
    {"from": "walmart", "to": "fedex", "type": "MARKETPLACE_ROUTING", "mode": "API", "min_plan": "ENTERPRISE"},
    {"from": "flipkart", "to": "cainiao", "type": "MARKETPLACE_ROUTING", "mode": "API", "min_plan": "ENTERPRISE"},
]
