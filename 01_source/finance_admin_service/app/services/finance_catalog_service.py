from __future__ import annotations

import json
from collections import Counter
from datetime import date

from sqlalchemy.orm import Session

from app.data.global_locker_finance_catalog import (
    ECOSYSTEM_SEGMENTS,
    FINANCE_DEMO_PRIORITY_CODES,
    GLOBAL_LOCKER_FINANCE_CATALOG,
    PLAYER_RELATIONS,
    ROLE_TO_PARTNER_TYPE,
)
from app.models.finance import FinancePartnerAccount, PartnerBillingPlan
from app.models.finance_catalog import FinanceLockerNetworkCatalog
from app.models.finance_ecosystem import (
    FinanceEcosystemSegment,
    FinancePlayerCapability,
    FinancePlayerRelation,
)
from app.services.crypto_util import new_id


def _currency_for_country(country: str) -> str:
    if country == "BR":
        return "BRL"
    if country in ("US", "CN"):
        return "USD"
    if country in ("GB",):
        return "GBP"
    if country in ("JP",):
        return "JPY"
    if country in ("IN",):
        return "INR"
    return "EUR"


def list_catalog(
    db: Session,
    *,
    parent_group: str | None = None,
    segment_code: str | None = None,
    country_code: str | None = None,
    linked_only: bool = False,
    active_only: bool = True,
) -> list[FinanceLockerNetworkCatalog]:
    q = db.query(FinanceLockerNetworkCatalog)
    if parent_group:
        q = q.filter(FinanceLockerNetworkCatalog.parent_group == parent_group)
    if segment_code:
        q = q.filter(FinanceLockerNetworkCatalog.segment_code == segment_code)
    if country_code:
        q = q.filter(FinanceLockerNetworkCatalog.country_code == country_code)
    if linked_only:
        q = q.filter(FinanceLockerNetworkCatalog.finance_partner_id.isnot(None))
    if active_only:
        q = q.filter(FinanceLockerNetworkCatalog.active.is_(True))
    return q.order_by(FinanceLockerNetworkCatalog.sort_order, FinanceLockerNetworkCatalog.code).all()


def _sync_segments(db: Session) -> int:
    n = 0
    for seg in ECOSYSTEM_SEGMENTS:
        row = db.get(FinanceEcosystemSegment, seg["code"])
        if row:
            row.name = seg["name"]
            row.description = seg.get("description")
            row.sort_order = seg["sort_order"]
        else:
            db.add(FinanceEcosystemSegment(**seg))
        n += 1
    return n


def _sync_relations(db: Session) -> int:
    n = 0
    for rel in PLAYER_RELATIONS:
        existing = (
            db.query(FinancePlayerRelation)
            .filter(
                FinancePlayerRelation.from_catalog_code == rel["from"],
                FinancePlayerRelation.to_catalog_code == rel["to"],
                FinancePlayerRelation.relation_type == rel["type"],
            )
            .first()
        )
        if not existing:
            db.add(
                FinancePlayerRelation(
                    id=new_id(),
                    from_catalog_code=rel["from"],
                    to_catalog_code=rel["to"],
                    relation_type=rel["type"],
                    notes=rel.get("notes"),
                )
            )
            n += 1
    return n


def _sync_capabilities(db: Session, entry: dict) -> None:
    code = entry["code"]
    db.query(FinancePlayerCapability).filter(FinancePlayerCapability.catalog_code == code).delete()
    for cap_code, protocol, direction in entry.get("capabilities") or []:
        db.add(
            FinancePlayerCapability(
                catalog_code=code,
                capability_code=cap_code,
                protocol=protocol,
                direction=direction,
            )
        )


def list_segments(db: Session) -> list[FinanceEcosystemSegment]:
    return db.query(FinanceEcosystemSegment).order_by(FinanceEcosystemSegment.sort_order).all()


def list_relations(db: Session, catalog_code: str | None = None) -> list[FinancePlayerRelation]:
    q = db.query(FinancePlayerRelation)
    if catalog_code:
        q = q.filter(
            (FinancePlayerRelation.from_catalog_code == catalog_code)
            | (FinancePlayerRelation.to_catalog_code == catalog_code)
        )
    return q.order_by(FinancePlayerRelation.from_catalog_code).all()


def list_capabilities(db: Session, catalog_code: str | None = None) -> list[FinancePlayerCapability]:
    q = db.query(FinancePlayerCapability)
    if catalog_code:
        q = q.filter(FinancePlayerCapability.catalog_code == catalog_code)
    return q.order_by(FinancePlayerCapability.catalog_code).all()


def sync_global_catalog(db: Session, *, create_partners: bool = True, create_plans: bool = True) -> dict[str, int]:
    """Sincroniza catálogo estático → DB e opcionalmente finance_partner_accounts + planos."""
    counts = {
        "catalog_upserted": 0,
        "partners_created": 0,
        "partners_linked": 0,
        "plans_created": 0,
        "segments_upserted": 0,
        "relations_upserted": 0,
        "capabilities_upserted": 0,
    }
    today = date.today()
    counts["segments_upserted"] = _sync_segments(db)

    for entry in GLOBAL_LOCKER_FINANCE_CATALOG:
        code = entry["code"]
        row = db.query(FinanceLockerNetworkCatalog).filter(FinanceLockerNetworkCatalog.code == code).first()
        regions_json = json.dumps(entry["regions"])
        payload = {
            "name": entry["name"],
            "player_role": entry["player_role"],
            "parent_group": entry["parent_group"],
            "segment_code": entry.get("segment_code") or entry["parent_group"],
            "country_code": entry["country_code"],
            "regions_json": regions_json,
            "supports_lockers": entry["supports_lockers"],
            "supports_marketplace": entry["supports_marketplace"],
            "supports_collection_points": entry.get("supports_collection_points", False),
            "supports_food_delivery": entry.get("supports_food_delivery", False),
            "integration_modes_json": json.dumps(entry.get("integration_modes") or []),
            "global_tier": entry["global_tier"],
            "locker_operator_ref": entry.get("locker_operator_ref"),
            "default_billing_model": entry["default_billing_model"],
            "default_revenue_share_pct": entry.get("default_revenue_share_pct"),
            "monthly_fee_cents": entry.get("monthly_fee_cents"),
            "integration_status": entry["integration_status"],
            "estimated_locker_count": entry.get("estimated_locker_count"),
            "api_docs_url": entry.get("api_docs_url"),
            "notes": entry.get("notes"),
            "sort_order": entry["sort_order"],
            "active": True,
        }
        if row:
            for k, v in payload.items():
                setattr(row, k, v)
        else:
            row = FinanceLockerNetworkCatalog(id=new_id(), code=code, **payload)
            db.add(row)
        counts["catalog_upserted"] += 1
        if entry.get("capabilities"):
            _sync_capabilities(db, entry)
            counts["capabilities_upserted"] += len(entry["capabilities"])

        if not entry.get("seed_finance_partner", True) or not create_partners:
            continue

        partner = db.query(FinancePartnerAccount).filter(FinancePartnerAccount.code == code).first()
        ptype = ROLE_TO_PARTNER_TYPE.get(entry["player_role"], "ECOMMERCE")
        currency = _currency_for_country(entry["country_code"])

        if not partner:
            partner = FinancePartnerAccount(
                id=new_id(),
                code=code,
                name=entry["name"],
                partner_type=ptype,
                country_code=entry["country_code"],
                currency=currency,
                active=entry["integration_status"] in ("LIVE", "PILOT"),
                metadata_json=json.dumps(
                    {
                        "parent_group": entry["parent_group"],
                        "locker_operator_ref": entry.get("locker_operator_ref"),
                        "global_tier": entry["global_tier"],
                    }
                ),
            )
            db.add(partner)
            counts["partners_created"] += 1
        row.finance_partner_id = partner.id
        counts["partners_linked"] += 1

        if create_plans and code in FINANCE_DEMO_PRIORITY_CODES:
            if not db.query(PartnerBillingPlan).filter(PartnerBillingPlan.partner_id == partner.id).first():
                db.add(
                    PartnerBillingPlan(
                        id=new_id(),
                        partner_id=partner.id,
                        partner_type=partner.partner_type,
                        plan_name=f"{code} {entry['default_billing_model']} 2026",
                        billing_model=entry["default_billing_model"],
                        currency=currency,
                        country_code=entry["country_code"],
                        monthly_fee_cents=entry.get("monthly_fee_cents"),
                        revenue_share_pct=entry.get("default_revenue_share_pct"),
                        valid_from=today.replace(day=1),
                        is_active=True,
                    )
                )
                counts["plans_created"] += 1

    counts["relations_upserted"] = _sync_relations(db)
    db.commit()
    return counts


def catalog_stats(db: Session) -> dict[str, int]:
    rows = (
        db.query(FinanceLockerNetworkCatalog.segment_code, FinanceLockerNetworkCatalog.parent_group)
        .filter(FinanceLockerNetworkCatalog.active.is_(True))
        .all()
    )
    by_segment: Counter[str] = Counter()
    for seg, parent in rows:
        by_segment[seg or parent] += 1
    return dict(by_segment)
