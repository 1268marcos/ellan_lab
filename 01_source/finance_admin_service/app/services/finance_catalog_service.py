from __future__ import annotations

import json
from collections import Counter
from datetime import date

from sqlalchemy.orm import Session

from app.data.global_locker_finance_catalog import (
    COUNTRY_COVERAGE,
    ECOSYSTEM_SEGMENTS,
    FINANCE_DEMO_PRIORITY_CODES,
    GLOBAL_LOCKER_FINANCE_CATALOG,
    INTEGRATION_BLUEPRINTS,
    PLAYER_ALIASES,
    PLAYER_RELATIONS,
    RELATION_TYPES,
    ROLE_TO_PARTNER_TYPE,
)
from app.models.finance import FinancePartnerAccount, PartnerBillingPlan
from app.models.finance_catalog import FinanceLockerNetworkCatalog
from app.models.finance_ecosystem import (
    FinanceEcosystemSegment,
    FinancePlayerCapability,
    FinancePlayerRelation,
)
from app.models.finance_world_meta import (
    FinanceIntegrationBlueprint,
    FinancePlayerAlias,
    FinancePlayerCountryCoverage,
    FinanceRelationType,
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


def _sync_relation_types(db: Session) -> int:
    n = 0
    for spec in RELATION_TYPES:
        row = db.get(FinanceRelationType, spec["code"])
        if row:
            row.name = spec["name"]
            row.description = spec.get("description")
        else:
            db.add(FinanceRelationType(**spec))
        n += 1
    return n


def _sync_aliases(db: Session) -> int:
    n = 0
    for spec in PLAYER_ALIASES:
        row = db.get(FinancePlayerAlias, spec["alias_code"])
        if row:
            row.catalog_code = spec["catalog_code"]
            row.source = spec.get("source", "LEGACY")
            row.notes = spec.get("notes")
        else:
            db.add(FinancePlayerAlias(**spec))
            n += 1
    return n


def _sync_country_coverage(db: Session) -> int:
    n = 0
    for catalog_code, country, locker, pudo, mkt, food in COUNTRY_COVERAGE:
        existing = (
            db.query(FinancePlayerCountryCoverage)
            .filter(
                FinancePlayerCountryCoverage.catalog_code == catalog_code,
                FinancePlayerCountryCoverage.country_code == country,
            )
            .first()
        )
        if existing:
            existing.locker_service = locker
            existing.pudo_service = pudo
            existing.marketplace_channel = mkt
            existing.food_pickup = food
        else:
            db.add(
                FinancePlayerCountryCoverage(
                    id=new_id(),
                    catalog_code=catalog_code,
                    country_code=country,
                    locker_service=locker,
                    pudo_service=pudo,
                    marketplace_channel=mkt,
                    food_pickup=food,
                )
            )
            n += 1
    return n


def _sync_integration_blueprints(db: Session) -> int:
    n = 0
    for spec in INTEGRATION_BLUEPRINTS:
        row = db.get(FinanceIntegrationBlueprint, spec["code"])
        payload = {
            "name": spec["name"],
            "target_segments_json": json.dumps(spec["target_segments"]),
            "auth_type": spec["auth_type"],
            "primary_capability": spec["primary_capability"],
            "webhook_events_json": json.dumps(spec["webhook_events"]),
            "reference_players_json": json.dumps(spec["reference_players"]),
            "docs_hint": spec.get("docs_hint"),
            "sort_order": spec.get("sort_order", 100),
        }
        if row:
            for k, v in payload.items():
                setattr(row, k, v)
        else:
            db.add(FinanceIntegrationBlueprint(code=spec["code"], **payload))
            n += 1
    return n


def resolve_catalog_code(db: Session, code_or_alias: str) -> str | None:
    """Resolve código canónico (ex. MELI → MERCADOLIVRE)."""
    direct = (
        db.query(FinanceLockerNetworkCatalog)
        .filter(FinanceLockerNetworkCatalog.code == code_or_alias)
        .first()
    )
    if direct:
        return direct.code
    alias = db.get(FinancePlayerAlias, code_or_alias)
    return alias.catalog_code if alias else None


def list_aliases(db: Session, catalog_code: str | None = None) -> list[FinancePlayerAlias]:
    q = db.query(FinancePlayerAlias)
    if catalog_code:
        q = q.filter(FinancePlayerAlias.catalog_code == catalog_code)
    return q.order_by(FinancePlayerAlias.alias_code).all()


def list_country_coverage(
    db: Session, *, catalog_code: str | None = None, country_code: str | None = None
) -> list[FinancePlayerCountryCoverage]:
    q = db.query(FinancePlayerCountryCoverage)
    if catalog_code:
        q = q.filter(FinancePlayerCountryCoverage.catalog_code == catalog_code)
    if country_code:
        q = q.filter(FinancePlayerCountryCoverage.country_code == country_code)
    return q.order_by(FinancePlayerCountryCoverage.catalog_code).all()


def list_integration_blueprints(db: Session) -> list[FinanceIntegrationBlueprint]:
    return (
        db.query(FinanceIntegrationBlueprint)
        .order_by(FinanceIntegrationBlueprint.sort_order)
        .all()
    )


def ecosystem_matrix(db: Session) -> dict:
    """Matriz segmento × país (contagem de players com cobertura locker/PUDO)."""
    segments = list_segments(db)
    coverage = list_country_coverage(db)
    by_seg_country: dict[str, dict[str, int]] = {}
    catalog_by_code = {r.code: r for r in list_catalog(db, active_only=True)}
    for cov in coverage:
        row = catalog_by_code.get(cov.catalog_code)
        seg = (row.segment_code or row.parent_group) if row else "UNKNOWN"
        by_seg_country.setdefault(seg, {})
        if cov.locker_service or cov.pudo_service:
            by_seg_country[seg][cov.country_code] = by_seg_country[seg].get(cov.country_code, 0) + 1
    return {
        "segments": [{"code": s.code, "name": s.name} for s in segments],
        "matrix": by_seg_country,
        "total_players": len(catalog_by_code),
        "total_relations": db.query(FinancePlayerRelation).count(),
        "total_aliases": db.query(FinancePlayerAlias).count(),
    }


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
        "relation_types_upserted": 0,
        "aliases_upserted": 0,
        "coverage_upserted": 0,
        "blueprints_upserted": 0,
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
    counts["relation_types_upserted"] = _sync_relation_types(db)
    counts["aliases_upserted"] = _sync_aliases(db)
    counts["coverage_upserted"] = _sync_country_coverage(db)
    counts["blueprints_upserted"] = _sync_integration_blueprints(db)
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


def _blueprint_targets(bp: FinanceIntegrationBlueprint) -> list[str]:
    try:
        return json.loads(bp.target_segments_json or "[]")
    except json.JSONDecodeError:
        return []


def _blueprint_refs(bp: FinanceIntegrationBlueprint) -> list[str]:
    try:
        return json.loads(bp.reference_players_json or "[]")
    except json.JSONDecodeError:
        return []


def match_blueprint_for_player(db: Session, row: FinanceLockerNetworkCatalog) -> FinanceIntegrationBlueprint | None:
    """Escolhe blueprint de integração por segmento ou referência explícita."""
    segment = row.segment_code or row.parent_group
    blueprints = list_integration_blueprints(db)
    for bp in blueprints:
        if segment in _blueprint_targets(bp):
            return bp
    for bp in blueprints:
        if row.code in _blueprint_refs(bp):
            return bp
    return blueprints[0] if blueprints else None


def get_catalog_row(db: Session, catalog_code: str) -> FinanceLockerNetworkCatalog | None:
    code = resolve_catalog_code(db, catalog_code.upper()) or catalog_code.upper()
    return (
        db.query(FinanceLockerNetworkCatalog)
        .filter(FinanceLockerNetworkCatalog.code == code, FinanceLockerNetworkCatalog.active.is_(True))
        .first()
    )


def build_integration_guide(db: Session, catalog_code: str) -> dict:
    """Painel 'Como integrar': blueprint + relações + cobertura + capabilities + readiness."""
    row = get_catalog_row(db, catalog_code)
    if not row:
        return {}

    code = row.code
    blueprint = match_blueprint_for_player(db, row)
    caps = list_capabilities(db, code)
    rels = list_relations(db, code)
    coverage = list_country_coverage(db, catalog_code=code)

    from app.models.finance_professional import FinancePartnerReadiness

    readiness = db.get(FinancePartnerReadiness, code)

    bp_out = None
    if blueprint:
        try:
            webhook_events = json.loads(blueprint.webhook_events_json or "[]")
        except json.JSONDecodeError:
            webhook_events = []
        bp_out = {
            "code": blueprint.code,
            "name": blueprint.name,
            "auth_type": blueprint.auth_type,
            "primary_capability": blueprint.primary_capability,
            "webhook_events": webhook_events,
            "docs_hint": blueprint.docs_hint,
            "target_segments": _blueprint_targets(blueprint),
        }

    steps: list[str] = []
    if bp_out:
        steps.append(f"1. Autenticação: {bp_out['auth_type']} — capability principal `{bp_out['primary_capability']}`.")
        if row.api_docs_url:
            steps.append(f"2. Documentação: {row.api_docs_url}")
        else:
            steps.append("2. Solicitar documentação API ao parceiro (api_docs_url ainda não mapeada).")
        if webhook_events := bp_out.get("webhook_events"):
            steps.append(f"3. Configurar webhooks: {', '.join(webhook_events[:4])}.")
        if rels:
            steps.append(f"4. Mapear {len(rels)} relação(ões) de ecossistema (carriers / redes / agregadores).")
        steps.append("5. Sync FINANCE + recompute readiness (`READINESS_RECOMPUTE` job).")
        steps.append(
            "6. Ligar `finance_catalog_code` em Partners/ML Admin para telemetria e settlements unificados."
        )

    return {
        "catalog_code": code,
        "name": row.name,
        "segment_code": row.segment_code or row.parent_group,
        "parent_group": row.parent_group,
        "integration_status": row.integration_status,
        "finance_partner_code": None,
        "blueprint": bp_out,
        "integration_steps": steps,
        "capabilities": [
            {
                "capability_code": c.capability_code,
                "protocol": c.protocol,
                "direction": c.direction,
            }
            for c in caps
        ],
        "relations": [
            {
                "from_catalog_code": r.from_catalog_code,
                "to_catalog_code": r.to_catalog_code,
                "relation_type": r.relation_type,
                "notes": r.notes,
            }
            for r in rels
        ],
        "country_coverage": [
            {
                "country_code": c.country_code,
                "locker_service": c.locker_service,
                "pudo_service": c.pudo_service,
                "marketplace_channel": c.marketplace_channel,
                "food_pickup": c.food_pickup,
            }
            for c in coverage
        ],
        "readiness": (
            {
                "readiness_score": readiness.readiness_score,
                "grade": readiness.grade,
                "integration_blueprint_code": readiness.integration_blueprint_code,
                "blueprint_score": readiness.blueprint_score,
                "blockers_json": readiness.blockers_json,
            }
            if readiness
            else None
        ),
        "cross_refs": {
            "finance_catalog_code": code,
            "partner_admin_path": f"/api/v1/partner-admin/ecosystem/players/by-finance-code/{code}",
            "ml_admin_path": f"/api/v1/ml-admin/ml-locker-network-players/by-finance-code/{code}",
        },
    }


def enrich_guide_finance_partner(db: Session, guide: dict) -> dict:
    if not guide:
        return guide
    row = get_catalog_row(db, guide["catalog_code"])
    if row and row.finance_partner_id:
        from app.models.finance import FinancePartnerAccount

        p = db.get(FinancePartnerAccount, row.finance_partner_id)
        if p:
            guide = {**guide, "finance_partner_code": p.code}
    return guide
