"""
Liga global_players ↔ ecommerce_partners / logistics_partners e garante operadores OP-{code}.
"""
from __future__ import annotations

import json
import re
from uuid import uuid4

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.data.catalog_global_players import locker_operator_id
from app.data.catalog_players_registry import PLAYERS_REGISTRY

# Códigos legados em partners (sem underscore, abreviados, etc.)
PARTNER_CODE_ALIASES: dict[str, str] = {
    "MERCADOLIVRE": "MERCADO_LIVRE",
    "MERCADO_LIVRE": "MERCADO_LIVRE",
    "ML": "MERCADO_LIVRE",
    "MELI": "MERCADO_LIVRE",
    "AMAZON": "AMAZON_HUB",
    "AMZN": "AMAZON_HUB",
    "AMAZON_HUB": "AMAZON_HUB",
    "AMAZON_US": "AMAZON_US",
    "AMAZON_EU": "AMAZON_EU",
    "AMAZON_ES": "AMAZON_ES",
    "MAGALU": "MAGALU",
    "MAGALU_LOG": "MAGALU",
    "SHOPEE": "SHOPEE",
    "SHOPEE_XPRESS": "SHOPEE",
    "CORREIOS": "CORREIOS",
    "CTT": "CTT",
    "CTTPT": "CTT",
    "INPOST": "INPOST",
    "DPD": "DPD",
    "DHL": "DHL_PACKSTATION",
    "DHL_PACKSTATION": "DHL_PACKSTATION",
    "DHL_PARCEL": "DHL_PARCEL",
    "GLS": "GLS",
    "SEUR": "SEUR",
    "WORTEN": "WORTEN",
    "ELCORTEINGLES": "EL_CORTE_INGLES",
    "EL_CORTE_INGLES": "EL_CORTE_INGLES",
    "ECI": "EL_CORTE_INGLES",
    "FEDEX": "FEDEX",
    "UPS": "UPS",
    "UPS_ACCESS_POINT": "UPS_ACCESS_POINT",
    "JADLOG": "JADLOG",
    "LOGGI": "LOGGI",
    "IFOOD": "IFOOD",
    "UBER_EATS": "UBER_EATS",
    "UBEREATS": "UBER_EATS",
    "GLOVO": "GLOVO",
    "RAPPI": "RAPPI",
    "CAINIAO": "CAINIAO",
    "MELHOR_ENVIO": "MELHOR_ENVIO",
    "INTELIPOST": "INTELIPOST",
    "ZALANDO": "ZALANDO",
    "ALLEGRO": "ALLEGRO",
    "EBAY": "EBAY",
}

_PLAYER_CODES: frozenset[str] = frozenset(p["code"] for p in PLAYERS_REGISTRY)
_REGISTRY_BY_CODE: dict[str, dict] = {p["code"]: p for p in PLAYERS_REGISTRY}

_MARKETPLACE_TYPES = frozenset({"MARKETPLACE", "RETAIL_PUDO"})
_LOGISTICS_TYPES = frozenset({
    "LOCKER_NETWORK",
    "NETWORK_OPERATOR",
    "CARRIER",
    "POSTAL",
    "AGGREGATOR",
})
_FOOD_TYPES = frozenset({"FOOD_DELIVERY"})


def _normalize_code(raw: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", str(raw or "").strip().upper())
    return re.sub(r"_+", "_", s).strip("_")


def resolve_player_code_from_partner(*, partner_id: str | None = None, partner_code: str | None = None) -> str | None:
    """Resolve código canónico global_players a partir de id/code do parceiro."""
    candidates: list[str] = []
    if partner_code:
        candidates.append(_normalize_code(partner_code))
    if partner_id:
        pid = str(partner_id).strip().upper()
        if pid.startswith("OP-"):
            candidates.append(pid[3:])
        candidates.append(_normalize_code(pid))

    for cand in candidates:
        if not cand:
            continue
        if cand in _PLAYER_CODES:
            return cand
        if cand in PARTNER_CODE_ALIASES:
            return PARTNER_CODE_ALIASES[cand]
        compact = cand.replace("_", "")
        if compact in PARTNER_CODE_ALIASES:
            return PARTNER_CODE_ALIASES[compact]
        for alias, player in PARTNER_CODE_ALIASES.items():
            if alias.replace("_", "") == compact:
                return player
    return None


def _operator_type_for_player(player: dict) -> str:
    ptype = str(player.get("type") or "LOGISTICS")
    if ptype in _MARKETPLACE_TYPES:
        return "ECOMMERCE"
    if ptype in _FOOD_TYPES:
        return "DELIVERY"
    return "LOGISTICS"


def _needs_locker_operator(player: dict) -> bool:
    return bool(
        player.get("supports_lockers")
        or player.get("supports_pudo")
        or player.get("supports_food")
        or player.get("supports_marketplace")
    )


def _table_exists(db: Session, name: str) -> bool:
    return name in set(inspect(db.get_bind()).get_table_names())


def _insert_integration_target(
    db: Session,
    player_code: str,
    target_type: str,
    target_key: str,
) -> bool:
    if db.execute(
        text(
            "SELECT 1 FROM global_player_integration_targets "
            "WHERE player_code = :p AND target_type = :t AND target_key = :k LIMIT 1"
        ),
        {"p": player_code, "t": target_type, "k": target_key},
    ).scalar():
        return False
    db.execute(
        text(
            """
            INSERT INTO global_player_integration_targets (
                id, player_code, target_type, target_key, metadata_json, created_at
            ) VALUES (:id, :p, :t, :k, '{}', CURRENT_TIMESTAMP)
            """
        ),
        {"id": str(uuid4()), "p": player_code, "t": target_type, "k": target_key},
    )
    return True


def seed_missing_locker_operators_from_registry(db: Session) -> int:
    """Cria locker_operators OP-{player_code} para players do registo que ainda não existem."""
    if not _table_exists(db, "locker_operators"):
        return 0
    cols = {c["name"] for c in inspect(db.get_bind()).get_columns("locker_operators")}
    created = 0
    for player in PLAYERS_REGISTRY:
        if not _needs_locker_operator(player):
            continue
        code = str(player["code"])
        op_id = locker_operator_id(code)
        exists = db.execute(
            text("SELECT 1 FROM locker_operators WHERE id = :id LIMIT 1"),
            {"id": op_id},
        ).scalar()
        if exists:
            if "player_code" in cols:
                db.execute(
                    text("UPDATE locker_operators SET player_code = :pc WHERE id = :id AND player_code IS NULL"),
                    {"pc": code, "id": op_id},
                )
            continue

        country = str(player.get("country") or "BR")[:2]
        currency = "BRL" if country == "BR" else "EUR" if country in {"PT", "ES", "DE", "FR", "IT", "PL", "EU"} else "USD"
        otype = _operator_type_for_player(player)
        base = {
            "id": op_id,
            "name": str(player["name"])[:128],
            "document": f"GP-{code}"[:32],
            "email": f"ops+{code.lower()}@ellanlab.local"[:128],
            "phone": None,
            "operator_type": otype,
            "country": country,
            "commission_rate": 0.01,
            "currency": currency,
            "player_code": code,
        }
        if "sla_pickup_hours" in cols and "player_code" in cols:
            db.execute(
                text(
                    """
                    INSERT INTO locker_operators (
                        id, name, document, email, phone, operator_type, country, active,
                        commission_rate, currency, player_code, sla_pickup_hours, sla_return_hours,
                        created_at, updated_at
                    ) VALUES (
                        :id, :name, :document, :email, :phone, :operator_type, :country, TRUE,
                        :commission_rate, :currency, :player_code, 72, 24,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    """
                ),
                base,
            )
        elif "player_code" in cols:
            db.execute(
                text(
                    """
                    INSERT INTO locker_operators (
                        id, name, document, email, phone, operator_type, country, active,
                        commission_rate, currency, player_code, created_at, updated_at
                    ) VALUES (
                        :id, :name, :document, :email, :phone, :operator_type, :country, TRUE,
                        :commission_rate, :currency, :player_code, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    """
                ),
                base,
            )
        else:
            db.execute(
                text(
                    """
                    INSERT INTO locker_operators (
                        id, name, document, operator_type, country, active,
                        commission_rate, currency, created_at, updated_at
                    ) VALUES (
                        :id, :name, :document, :operator_type, :country, TRUE,
                        :commission_rate, :currency, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    """
                ),
                {k: base[k] for k in ("id", "name", "document", "operator_type", "country", "commission_rate", "currency")},
            )
        created += 1
    if created:
        db.commit()
    return created


def ensure_partners_for_global_players(db: Session) -> dict[str, int]:
    """Garante linhas em ecommerce_partners / logistics_partners alinhadas ao registo."""
    counts = {"ecommerce_created": 0, "logistics_created": 0}
    if not _table_exists(db, "global_players"):
        return counts

    for player in PLAYERS_REGISTRY:
        code = str(player["code"])
        ptype = str(player["type"])
        op_id = locker_operator_id(code)
        country = str(player.get("country") or "BR")[:2]
        currency = "BRL" if country == "BR" else "EUR" if country in {"PT", "ES", "FR", "DE", "IT", "PL"} else "USD"

        if ptype in _MARKETPLACE_TYPES and _table_exists(db, "ecommerce_partners"):
            partner_code = code[:32]
            exists = db.execute(
                text(
                    "SELECT id FROM ecommerce_partners WHERE UPPER(code) = :c OR id = :id LIMIT 1"
                ),
                {"c": partner_code, "id": op_id},
            ).first()
            if not exists:
                db.execute(
                    text(
                        """
                        INSERT INTO ecommerce_partners (
                            id, name, code, integration_type, revenue_share_pct, currency,
                            sla_pickup_hours, active, country, status, created_at, updated_at
                        ) VALUES (
                            :id, :name, :code, 'API', 0.01, :currency,
                            72, TRUE, :country, 'ACTIVE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                        """
                    ),
                    {
                        "id": op_id,
                        "name": str(player["name"])[:128],
                        "code": partner_code,
                        "currency": currency,
                        "country": country,
                    },
                )
                counts["ecommerce_created"] += 1

        if ptype in _LOGISTICS_TYPES | _FOOD_TYPES and _table_exists(db, "logistics_partners"):
            partner_code = code[:32]
            exists = db.execute(
                text(
                    "SELECT id FROM logistics_partners WHERE UPPER(code) = :c OR id = :id LIMIT 1"
                ),
                {"c": partner_code, "id": op_id},
            ).first()
            if not exists:
                db.execute(
                    text(
                        """
                        INSERT INTO logistics_partners (
                            id, name, code, integration_type, default_sla_hours,
                            reminder_hours_before, active, country, created_at, updated_at
                        ) VALUES (
                            :id, :name, :code, 'API', 72, 24, TRUE, :country,
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                        """
                    ),
                    {
                        "id": op_id,
                        "name": str(player["name"])[:128],
                        "code": partner_code,
                        "country": country,
                    },
                )
                counts["logistics_created"] += 1

    if counts["ecommerce_created"] or counts["logistics_created"]:
        db.commit()
    return counts


def link_global_players_to_partners(db: Session) -> dict[str, int]:
    """Liga parceiros existentes ao catálogo via global_player_integration_targets."""
    counts = {
        "ecommerce_links": 0,
        "logistics_links": 0,
        "metadata_updates": 0,
    }
    if not _table_exists(db, "global_player_integration_targets"):
        return counts

    if _table_exists(db, "ecommerce_partners"):
        rows = db.execute(text("SELECT id, code FROM ecommerce_partners")).mappings().all()
        for row in rows:
            player_code = resolve_player_code_from_partner(
                partner_id=str(row["id"]),
                partner_code=str(row.get("code") or ""),
            )
            if not player_code:
                continue
            if not db.execute(
                text("SELECT 1 FROM global_players WHERE code = :c LIMIT 1"),
                {"c": player_code},
            ).scalar():
                continue
            if _insert_integration_target(db, player_code, "ECOMMERCE_PARTNER", str(row["id"])):
                counts["ecommerce_links"] += 1
            _update_player_partner_metadata(db, player_code, "ecommerce_partner_id", str(row["id"]))

    if _table_exists(db, "logistics_partners"):
        rows = db.execute(text("SELECT id, code FROM logistics_partners")).mappings().all()
        for row in rows:
            player_code = resolve_player_code_from_partner(
                partner_id=str(row["id"]),
                partner_code=str(row.get("code") or ""),
            )
            if not player_code:
                continue
            if not db.execute(
                text("SELECT 1 FROM global_players WHERE code = :c LIMIT 1"),
                {"c": player_code},
            ).scalar():
                continue
            if _insert_integration_target(db, player_code, "LOGISTICS_PARTNER", str(row["id"])):
                counts["logistics_links"] += 1
            _update_player_partner_metadata(db, player_code, "logistics_partner_id", str(row["id"]))

    db.commit()
    return counts


def _update_player_partner_metadata(db: Session, player_code: str, key: str, partner_id: str) -> None:
    if not _table_exists(db, "global_players"):
        return
    row = db.execute(
        text("SELECT metadata_json FROM global_players WHERE code = :c"),
        {"c": player_code},
    ).mappings().first()
    if not row:
        return
    meta = {}
    raw = row.get("metadata_json")
    if isinstance(raw, dict):
        meta = raw
    elif isinstance(raw, str):
        try:
            meta = json.loads(raw) or {}
        except json.JSONDecodeError:
            meta = {}
    if meta.get(key) == partner_id:
        return
    meta[key] = partner_id
    db.execute(
        text(
            "UPDATE global_players SET metadata_json = :meta, updated_at = CURRENT_TIMESTAMP WHERE code = :c"
        ),
        {"meta": json.dumps(meta), "c": player_code},
    )


def sync_global_players_ecosystem(db: Session) -> dict[str, int | dict]:
    """Operadores + parceiros + ligações num único fluxo (chamado após seed global_players)."""
    ops = seed_missing_locker_operators_from_registry(db)
    partners = ensure_partners_for_global_players(db)
    links = link_global_players_to_partners(db)
    return {"operators_created": ops, **partners, **links}
