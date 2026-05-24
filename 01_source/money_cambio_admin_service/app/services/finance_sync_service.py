from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.clients.finance_admin_client import (
    FinanceAdminClient,
    FinanceAdminClientError,
    parse_regions_json,
)
from app.core.config import get_settings
from app.data.global_locker_money_catalog import ALL_MONEY_PLAYERS
from app.models.professional import (
    MoneyEcosystemSegment,
    MoneyLockerPlayerRegistry,
    MoneyPlayerRelation,
)
from app.schemas.finance_sync import FinanceSyncOut
from app.services.crypto_util import new_id

logger = logging.getLogger(__name__)

# Último resultado em memória (OPS status sem tabela extra)
_LAST_SYNC: FinanceSyncOut | None = None

COUNTRY_DEFAULT_CURRENCY: dict[str, str] = {
    "BR": "BRL",
    "PT": "EUR",
    "ES": "EUR",
    "DE": "EUR",
    "PL": "PLN",
    "GB": "GBP",
    "US": "USD",
    "FR": "EUR",
    "NL": "EUR",
    "IT": "EUR",
    "MX": "MXN",
    "AR": "ARS",
    "CL": "CLP",
    "CA": "CAD",
    "JP": "JPY",
    "SG": "SGD",
    "CN": "CNY",
    "IN": "INR",
    "NO": "NOK",
    "SE": "SEK",
    "DK": "DKK",
    "CH": "CHF",
    "AU": "AUD",
    "HK": "HKD",
    "CO": "COP",
    "BE": "EUR",
    "AT": "EUR",
    "GLOBAL": "USD",
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _build_corridor_index() -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for spec in ALL_MONEY_PLAYERS:
        fin = spec.get("finance_catalog_code") or spec["player_code"]
        idx[fin.upper()] = spec
        idx[spec["player_code"].upper()] = spec
    return idx


def _resolve_segment(item: dict) -> str:
    seg = (item.get("segment_code") or item.get("parent_group") or "LOCKER_NETWORK").upper()
    return seg


def _resolve_currency(country_code: str) -> str:
    cc = (country_code or "US").upper()
    return COUNTRY_DEFAULT_CURRENCY.get(cc, "USD")


def get_last_finance_sync() -> FinanceSyncOut | None:
    return _LAST_SYNC


def sync_from_finance_admin(
    db: Session,
    *,
    trigger_finance_sync: bool = True,
    create_finance_partners: bool = False,
    deactivate_missing: bool = False,
    client: FinanceAdminClient | None = None,
) -> FinanceSyncOut:
    global _LAST_SYNC
    settings = get_settings()
    if not settings.finance_admin_sync_enabled:
        raise FinanceAdminClientError("finance_admin_sync_disabled")

    cli = client or FinanceAdminClient()
    corridor_idx = _build_corridor_index()
    now = _utcnow()
    warnings: list[str] = []
    out = FinanceSyncOut(
        synced_at=now,
        finance_base_url=cli.base_url,
        finance_sync_triggered=trigger_finance_sync,
    )

    if trigger_finance_sync:
        try:
            cli.trigger_catalog_sync(
                create_partners=create_finance_partners,
                create_plans=False,
            )
        except FinanceAdminClientError as exc:
            warnings.append(f"finance_catalog_sync_skipped: {exc}")

    try:
        catalog = cli.fetch_catalog()
        segments = cli.fetch_segments()
        relations = cli.fetch_relations()
    except FinanceAdminClientError:
        raise

    out.finance_catalog_total = len(catalog)
    finance_codes: set[str] = set()

    for seg in segments:
        code = seg.get("code")
        if not code:
            continue
        row = db.query(MoneyEcosystemSegment).filter(MoneyEcosystemSegment.code == code).first()
        if row:
            row.name = seg.get("name") or row.name
            row.description = seg.get("description")
            row.sort_order = int(seg.get("sort_order") or row.sort_order)
            row.is_active = True
        else:
            db.add(
                MoneyEcosystemSegment(
                    code=code,
                    name=seg.get("name") or code,
                    description=seg.get("description"),
                    sort_order=int(seg.get("sort_order") or 100),
                    is_active=True,
                )
            )
            out.segments_upserted += 1

    for item in catalog:
        code = (item.get("code") or "").upper()
        if not code:
            continue
        finance_codes.add(code)
        if not item.get("active", True):
            continue

        regions = parse_regions_json(item.get("regions_json"))
        if not regions and item.get("country_code"):
            regions = [item["country_code"]]

        local = corridor_idx.get(code, {})
        fiscal = local.get("fiscal_corridor_code")
        cambio = local.get("cambio_corridor_code")
        segment = _resolve_segment(item)
        country = (item.get("country_code") or "US").upper()[:2]
        currency = local.get("default_settlement_currency") or _resolve_currency(country)

        meta = {
            "finance_sync": True,
            "finance_synced_at": now.isoformat(),
            "finance_parent_group": item.get("parent_group"),
            "finance_player_role": item.get("player_role"),
            "finance_integration_status": item.get("integration_status"),
            "finance_global_tier": item.get("global_tier"),
            "supports_lockers": item.get("supports_lockers"),
            "supports_marketplace": item.get("supports_marketplace"),
            "supports_collection_points": item.get("supports_collection_points"),
            "supports_food_delivery": item.get("supports_food_delivery"),
        }

        row = db.query(MoneyLockerPlayerRegistry).filter(MoneyLockerPlayerRegistry.player_code == code).first()
        if row:
            row.name = item.get("name") or row.name
            row.segment = segment
            row.primary_country = country
            row.regions_json = regions
            row.default_settlement_currency = currency
            row.finance_catalog_code = code
            if fiscal and not row.fiscal_corridor_code:
                row.fiscal_corridor_code = fiscal
            if cambio and not row.cambio_corridor_code:
                row.cambio_corridor_code = cambio
            row.notes = item.get("notes") or row.notes
            row.metadata_json = {**(row.metadata_json or {}), **meta}
            row.is_active = True
            row.updated_at = now
            out.players_updated += 1
        else:
            db.add(
                MoneyLockerPlayerRegistry(
                    id=new_id(),
                    player_code=code,
                    name=item.get("name") or code,
                    segment=segment,
                    primary_country=country,
                    regions_json=regions,
                    default_settlement_currency=currency,
                    finance_catalog_code=code,
                    fiscal_corridor_code=fiscal,
                    cambio_corridor_code=cambio,
                    notes=item.get("notes"),
                    metadata_json=meta,
                    is_active=True,
                )
            )
            out.players_created += 1

    for rel in relations:
        from_c = (rel.get("from_catalog_code") or rel.get("from") or "").upper()
        to_c = (rel.get("to_catalog_code") or rel.get("to") or "").upper()
        rtype = (rel.get("relation_type") or rel.get("type") or "").upper()
        if not from_c or not to_c or not rtype:
            out.relations_skipped += 1
            continue
        exists = (
            db.query(MoneyPlayerRelation)
            .filter(
                MoneyPlayerRelation.from_player_code == from_c,
                MoneyPlayerRelation.to_player_code == to_c,
                MoneyPlayerRelation.relation_type == rtype,
            )
            .first()
        )
        if exists:
            out.relations_skipped += 1
            continue
        db.add(
            MoneyPlayerRelation(
                id=new_id(),
                from_player_code=from_c,
                to_player_code=to_c,
                relation_type=rtype,
                notes=rel.get("notes"),
                metadata_json={"source": "finance_admin_sync", "finance_synced_at": now.isoformat()},
                is_active=True,
            )
        )
        out.relations_created += 1

    if deactivate_missing:
        q = db.query(MoneyLockerPlayerRegistry).filter(MoneyLockerPlayerRegistry.is_active.is_(True))
        for row in q.all():
            if row.player_code not in finance_codes:
                meta = row.metadata_json or {}
                if meta.get("finance_sync"):
                    row.is_active = False
                    row.updated_at = now
                    out.players_deactivated += 1

    out.warnings = warnings
    db.commit()
    _LAST_SYNC = out
    logger.info(
        "finance_sync ok catalog=%s created=%s updated=%s relations=%s",
        out.finance_catalog_total,
        out.players_created,
        out.players_updated,
        out.relations_created,
    )
    return out
