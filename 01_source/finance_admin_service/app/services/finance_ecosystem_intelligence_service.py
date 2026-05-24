from __future__ import annotations

import json
import hashlib
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.data.global_locker_finance_catalog import FINANCE_DEMO_PRIORITY_CODES, LOCKER_WORLD_PRIORITY_INDEX
from app.models.finance_catalog import FinanceLockerNetworkCatalog
from app.models.finance_ecosystem import FinancePlayerCapability, FinancePlayerRelation
from app.models.finance_intelligence import (
    FinanceEcosystemInsight,
    FinanceIntegrationHealthCheck,
    FinancePlayerBenchmark,
)
from app.models.finance_professional import FinanceIntegrationMilestone, FinancePartnerReadiness
from app.models.finance_world_meta import FinancePlayerCountryCoverage
from app.services.crypto_util import new_id
from app.services.finance_catalog_service import (
    build_integration_guide,
    get_catalog_row,
    list_country_coverage,
    list_relations,
    match_blueprint_for_player,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _upsert_insight(
    db: Session,
    *,
    catalog_code: str,
    insight_type: str,
    severity: str,
    title: str,
    detail: dict,
    suggested_action: str | None,
) -> bool:
    existing = (
        db.query(FinanceEcosystemInsight)
        .filter(
            FinanceEcosystemInsight.catalog_code == catalog_code,
            FinanceEcosystemInsight.insight_type == insight_type,
            FinanceEcosystemInsight.title == title,
        )
        .first()
    )
    detail_json = json.dumps(detail)
    if existing:
        existing.severity = severity
        existing.detail_json = detail_json
        existing.suggested_action = suggested_action
        existing.status = "OPEN" if existing.status != "RESOLVED" else existing.status
        existing.detected_at = _utcnow()
        return False
    db.add(
        FinanceEcosystemInsight(
            id=new_id(),
            catalog_code=catalog_code,
            insight_type=insight_type,
            severity=severity,
            title=title,
            detail_json=detail_json,
            suggested_action=suggested_action,
            status="OPEN",
        )
    )
    return True


def _relation_codes_for(db: Session, code: str) -> set[str]:
    rels = list_relations(db, code)
    out: set[str] = set()
    for r in rels:
        if r.from_catalog_code == code:
            out.add(r.to_catalog_code)
        else:
            out.add(r.from_catalog_code)
    return out


def analyze_ecosystem(db: Session) -> dict[str, int]:
    """Detecta gaps e oportunidades no ecossistema mundial."""
    created = updated = 0
    priority_codes = {x["code"] for x in LOCKER_WORLD_PRIORITY_INDEX} | set(FINANCE_DEMO_PRIORITY_CODES)
    players = db.query(FinanceLockerNetworkCatalog).filter(FinanceLockerNetworkCatalog.active.is_(True)).all()

    segment_carrier_peers: dict[str, set[str]] = {}
    for row in players:
        rels = list_relations(db, row.code)
        if row.parent_group == "MARKETPLACE":
            carriers = {
                r.to_catalog_code
                for r in rels
                if r.from_catalog_code == row.code and r.relation_type == "CHANNEL_USES_CARRIER"
            }
            segment_carrier_peers.setdefault(row.segment_code or row.parent_group, set()).update(carriers)

    for row in players:
        code = row.code
        cap_count = (
            db.query(FinancePlayerCapability).filter(FinancePlayerCapability.catalog_code == code).count()
        )
        rel_count = (
            db.query(FinancePlayerRelation)
            .filter(
                (FinancePlayerRelation.from_catalog_code == code)
                | (FinancePlayerRelation.to_catalog_code == code)
            )
            .count()
        )
        cov_count = (
            db.query(FinancePlayerCountryCoverage)
            .filter(FinancePlayerCountryCoverage.catalog_code == code)
            .count()
        )

        if cap_count == 0 and row.integration_status in ("LIVE", "PILOT", "IN_PROGRESS"):
            if _upsert_insight(
                db,
                catalog_code=code,
                insight_type="MISSING_CAPABILITIES",
                severity="HIGH",
                title="Capabilities não mapeadas",
                detail={"capability_count": 0},
                suggested_action="Sync catálogo e definir capabilities no blueprint de integração.",
            ):
                created += 1
            else:
                updated += 1

        if not match_blueprint_for_player(db, row):
            if _upsert_insight(
                db,
                catalog_code=code,
                insight_type="NO_BLUEPRINT",
                severity="MEDIUM",
                title="Sem blueprint de integração",
                detail={"segment": row.segment_code or row.parent_group},
                suggested_action="Adicionar segmento ao INTEGRATION_BLUEPRINTS ou referência explícita.",
            ):
                created += 1
            else:
                updated += 1

        if code in priority_codes and cov_count == 0:
            if _upsert_insight(
                db,
                catalog_code=code,
                insight_type="MISSING_COVERAGE",
                severity="MEDIUM",
                title="Player prioritário sem cobertura país",
                detail={"priority": True},
                suggested_action="Preencher COUNTRY_COVERAGE em global_locker_finance_catalog_expansion.py.",
            ):
                created += 1
            else:
                updated += 1

        if row.parent_group == "MARKETPLACE" and row.supports_marketplace:
            has_carrier = any(
                r.relation_type in ("CHANNEL_USES_CARRIER", "AGGREGATES", "FULFILLS_FOR")
                for r in list_relations(db, code)
                if r.from_catalog_code == code
            )
            if not has_carrier and row.integration_status != "PLANNED":
                peers = segment_carrier_peers.get(row.segment_code or row.parent_group, set())
                if _upsert_insight(
                    db,
                    catalog_code=code,
                    insight_type="MISSING_CARRIER_LINK",
                    severity="HIGH",
                    title="Marketplace sem carrier/agregador ligado",
                    detail={"peer_carriers": sorted(peers)[:5]},
                    suggested_action=f"Ligar via PLAYER_RELATIONS (ex.: {', '.join(sorted(peers)[:2]) or 'CORREIOS, INPOST'}).",
                ):
                    created += 1
                else:
                    updated += 1

        if not row.finance_partner_id and code in FINANCE_DEMO_PRIORITY_CODES:
            if _upsert_insight(
                db,
                catalog_code=code,
                insight_type="MISSING_FINANCE_PARTNER",
                severity="HIGH",
                title="Sem conta finance_partner",
                detail={},
                suggested_action="POST /locker-network-catalog/sync com create_partners=true.",
            ):
                created += 1
            else:
                updated += 1

        readiness = db.get(FinancePartnerReadiness, code)
        if readiness and readiness.grade in ("C", "D"):
            if _upsert_insight(
                db,
                catalog_code=code,
                insight_type="LOW_READINESS",
                severity="HIGH" if readiness.grade == "D" else "MEDIUM",
                title=f"Readiness baixo (grade {readiness.grade})",
                detail={"score": readiness.readiness_score, "blockers": readiness.blockers_json},
                suggested_action="Ver integration-guide e job READINESS_RECOMPUTE.",
            ):
                created += 1
            else:
                updated += 1

        if rel_count == 0 and row.global_tier in ("GLOBAL", "PRIORITY"):
            if _upsert_insight(
                db,
                catalog_code=code,
                insight_type="ORPHAN_PLAYER",
                severity="LOW",
                title="Player global sem relações no grafo",
                detail={"global_tier": row.global_tier},
                suggested_action="Adicionar PLAYER_RELATIONS para interoperabilidade.",
            ):
                created += 1
            else:
                updated += 1

    db.commit()
    return {"insights_created": created, "insights_updated": updated}


def compute_benchmarks(db: Session) -> int:
    players = db.query(FinanceLockerNetworkCatalog).filter(FinanceLockerNetworkCatalog.active.is_(True)).all()
    scored: list[tuple[FinanceLockerNetworkCatalog, int, dict]] = []

    for row in players:
        code = row.code
        readiness = db.get(FinancePartnerReadiness, code)
        r_score = readiness.readiness_score if readiness else 0
        rel_count = (
            db.query(FinancePlayerRelation)
            .filter(
                (FinancePlayerRelation.from_catalog_code == code)
                | (FinancePlayerRelation.to_catalog_code == code)
            )
            .count()
        )
        cap_count = (
            db.query(FinancePlayerCapability).filter(FinancePlayerCapability.catalog_code == code).count()
        )
        cov_count = (
            db.query(FinancePlayerCountryCoverage)
            .filter(FinancePlayerCountryCoverage.catalog_code == code)
            .count()
        )
        locker_bonus = min(15, (row.estimated_locker_count or 0) // 5000)
        status_bonus = {"LIVE": 10, "PILOT": 6, "IN_PROGRESS": 3}.get(row.integration_status, 0)
        composite = min(100, r_score // 2 + rel_count * 3 + cap_count * 2 + cov_count * 2 + locker_bonus + status_bonus)
        scored.append((row, composite, {"r_score": r_score, "rel_count": rel_count, "cap_count": cap_count, "cov_count": cov_count}))

    scored.sort(key=lambda x: x[1], reverse=True)
    n = len(scored)
    now = _utcnow()

    for rank, (row, composite, meta) in enumerate(scored, start=1):
        percentile = round(100 * (n - rank + 1) / n, 2) if n else 0
        payload = {
            "segment_code": row.segment_code or row.parent_group,
            "readiness_score": meta["r_score"],
            "readiness_rank": rank,
            "readiness_percentile": percentile,
            "relation_count": meta["rel_count"],
            "capability_count": meta["cap_count"],
            "coverage_count": meta["cov_count"],
            "estimated_locker_count": row.estimated_locker_count,
            "integration_status": row.integration_status,
            "composite_score": composite,
            "computed_at": now,
        }
        existing = db.get(FinancePlayerBenchmark, row.code)
        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
        else:
            db.add(FinancePlayerBenchmark(catalog_code=row.code, **payload))

    db.commit()
    return n


def run_health_checks(db: Session) -> int:
    """Health check heurístico (demo profissional) — LIVE/PILOT players."""
    now = _utcnow()
    count = 0
    players = (
        db.query(FinanceLockerNetworkCatalog)
        .filter(
            FinanceLockerNetworkCatalog.active.is_(True),
            FinanceLockerNetworkCatalog.integration_status.in_(("LIVE", "PILOT")),
        )
        .all()
    )

    for row in players:
        checks = [
            ("API_DOCS", row.api_docs_url is not None, row.api_docs_url or "missing api_docs_url"),
            (
                "FINANCE_LINK",
                row.finance_partner_id is not None,
                "linked" if row.finance_partner_id else "no finance partner",
            ),
            (
                "BLUEPRINT",
                match_blueprint_for_player(db, row) is not None,
                "blueprint matched",
            ),
        ]
        for check_type, ok, msg in checks:
            seed = int(hashlib.md5(f"{row.code}:{check_type}".encode()).hexdigest()[:6], 16)
            latency = 40 + (seed % 120) if ok else None
            status = "HEALTHY" if ok else ("DEGRADED" if row.integration_status == "PILOT" else "OFFLINE")
            existing = (
                db.query(FinanceIntegrationHealthCheck)
                .filter(
                    FinanceIntegrationHealthCheck.catalog_code == row.code,
                    FinanceIntegrationHealthCheck.check_type == check_type,
                )
                .first()
            )
            payload = {
                "status": status,
                "latency_ms": latency,
                "http_status": 200 if ok else 503,
                "message": str(msg)[:500],
                "checked_at": now,
            }
            if existing:
                for k, v in payload.items():
                    setattr(existing, k, v)
            else:
                db.add(
                    FinanceIntegrationHealthCheck(
                        id=new_id(),
                        catalog_code=row.code,
                        check_type=check_type,
                        **payload,
                    )
                )
            count += 1

    db.commit()
    return count


def generate_playbook_milestones(db: Session, catalog_code: str) -> int:
    """Gera roadmap DISCOVERY→LIVE a partir do integration-guide / blueprint."""
    guide = build_integration_guide(db, catalog_code)
    if not guide:
        return 0

    phases = [
        ("DISCOVERY", "Mapear API e contrato comercial", 10),
        ("SANDBOX", "Ambiente sandbox + credenciais", 30),
        ("INTEGRATION", "Implementar blueprint principal", 50),
        ("PILOT", "Piloto em corredor limitado", 70),
        ("LIVE", "Go-live produção", 90),
    ]
    blueprint_name = (guide.get("blueprint") or {}).get("name") or "Integração"
    created = 0
    base_date = date.today()

    for phase, title_suffix, sort_order in phases:
        title = f"{blueprint_name}: {title_suffix}"
        exists = (
            db.query(FinanceIntegrationMilestone)
            .filter(
                FinanceIntegrationMilestone.catalog_code == guide["catalog_code"],
                FinanceIntegrationMilestone.phase == phase,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            FinanceIntegrationMilestone(
                id=new_id(),
                catalog_code=guide["catalog_code"],
                phase=phase,
                title=title,
                target_date=base_date + timedelta(days=sort_order * 3),
                status="PENDING" if phase != "DISCOVERY" else "IN_PROGRESS",
                owner="OPS_INTEGRATION",
                blocker_notes=None,
                sort_order=sort_order,
            )
        )
        created += 1

    if created:
        db.commit()
    return created


def get_recommendations(db: Session, catalog_code: str) -> list[dict]:
    row = get_catalog_row(db, catalog_code)
    if not row:
        return []

    recs: list[dict] = []
    code = row.code
    linked = _relation_codes_for(db, code)
    guide = build_integration_guide(db, code)

    if row.parent_group == "MARKETPLACE":
        for peer in ("CORREIOS", "INPOST", "DHL", "CTT"):
            if peer not in linked and get_catalog_row(db, peer):
                recs.append(
                    {
                        "catalog_code": code,
                        "recommendation_type": "ADD_CARRIER",
                        "target_code": peer,
                        "title": f"Ligar last mile via {peer}",
                        "rationale": "Marketplaces similares usam carrier nacional para locker/PUDO.",
                        "priority": 1,
                    }
                )

    if row.parent_group in ("LOCKER_NETWORK", "LOCKER_NETWORK_OPERATOR"):
        for agg in ("MELHOR_ENVIO", "SENDCLOUD", "EASYPOST"):
            if agg not in linked and get_catalog_row(db, agg):
                recs.append(
                    {
                        "catalog_code": code,
                        "recommendation_type": "ADD_AGGREGATOR",
                        "target_code": agg,
                        "title": f"Expor via agregador {agg}",
                        "rationale": "Agregadores multi-carrier ampliam alcance de sellers.",
                        "priority": 2,
                    }
                )

    if guide.get("blueprint") and not db.get(FinancePartnerReadiness, code):
        recs.append(
            {
                "catalog_code": code,
                "recommendation_type": "RUN_READINESS",
                "target_code": None,
                "title": "Calcular readiness por blueprint",
                "rationale": "Score ainda não calculado — executar READINESS_RECOMPUTE.",
                "priority": 1,
            }
        )

    if not list_country_coverage(db, catalog_code=code):
        recs.append(
            {
                "catalog_code": code,
                "recommendation_type": "ADD_COVERAGE",
                "target_code": row.country_code,
                "title": f"Registrar cobertura {row.country_code}",
                "rationale": "Cobertura país habilita corredores fiscais e matriz segmento×país.",
                "priority": 3,
            }
        )

    return sorted(recs, key=lambda x: x["priority"])[:8]


def run_full_intelligence_scan(db: Session) -> dict[str, int]:
    analyze = analyze_ecosystem(db)
    benchmarks = compute_benchmarks(db)
    health = run_health_checks(db)
    milestones = 0
    for code in FINANCE_DEMO_PRIORITY_CODES:
        milestones += generate_playbook_milestones(db, code)
    return {
        "insights_created": analyze["insights_created"],
        "insights_updated": analyze["insights_updated"],
        "benchmarks_computed": benchmarks,
        "health_checks_run": health,
        "milestones_generated": milestones,
    }


def list_insights(
    db: Session,
    *,
    catalog_code: str | None = None,
    status: str | None = "OPEN",
    severity: str | None = None,
    limit: int = 100,
) -> list[FinanceEcosystemInsight]:
    q = db.query(FinanceEcosystemInsight).order_by(
        FinanceEcosystemInsight.severity.desc(),
        FinanceEcosystemInsight.detected_at.desc(),
    )
    if catalog_code:
        q = q.filter(FinanceEcosystemInsight.catalog_code == catalog_code)
    if status:
        q = q.filter(FinanceEcosystemInsight.status == status)
    if severity:
        q = q.filter(FinanceEcosystemInsight.severity == severity)
    return q.limit(limit).all()


def list_benchmarks(
    db: Session, *, segment_code: str | None = None, limit: int = 50
) -> list[FinancePlayerBenchmark]:
    q = db.query(FinancePlayerBenchmark).order_by(FinancePlayerBenchmark.composite_score.desc())
    if segment_code:
        q = q.filter(FinancePlayerBenchmark.segment_code == segment_code)
    return q.limit(limit).all()


def list_health_checks(db: Session, catalog_code: str | None = None) -> list[FinanceIntegrationHealthCheck]:
    q = db.query(FinanceIntegrationHealthCheck).order_by(FinanceIntegrationHealthCheck.checked_at.desc())
    if catalog_code:
        q = q.filter(FinanceIntegrationHealthCheck.catalog_code == catalog_code)
    return q.all()


def resolve_insight(db: Session, insight_id: str) -> FinanceEcosystemInsight | None:
    row = db.get(FinanceEcosystemInsight, insight_id)
    if not row:
        return None
    row.status = "RESOLVED"
    row.resolved_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def intelligence_dashboard(db: Session) -> dict:
    insights = list_insights(db, status="OPEN", limit=20)
    open_count = db.query(FinanceEcosystemInsight).filter(FinanceEcosystemInsight.status == "OPEN").count()
    critical = (
        db.query(FinanceEcosystemInsight)
        .filter(FinanceEcosystemInsight.status == "OPEN", FinanceEcosystemInsight.severity == "HIGH")
        .count()
    )
    benchmarks = list_benchmarks(db, limit=10)
    health_rows = list_health_checks(db)
    health_summary = {"HEALTHY": 0, "DEGRADED": 0, "OFFLINE": 0, "UNKNOWN": 0}
    for h in health_rows:
        health_summary[h.status] = health_summary.get(h.status, 0) + 1

    readiness_rows = db.query(FinancePartnerReadiness).all()
    avg_readiness = sum(r.readiness_score for r in readiness_rows) / len(readiness_rows) if readiness_rows else 0.0
    avg_composite = (
        db.query(FinancePlayerBenchmark).with_entities(FinancePlayerBenchmark.composite_score).all()
    )
    avg_comp = sum(x[0] for x in avg_composite) / len(avg_composite) if avg_composite else 0.0

    return {
        "open_insights": open_count,
        "critical_insights": critical,
        "players_analyzed": db.query(FinanceLockerNetworkCatalog).filter(FinanceLockerNetworkCatalog.active.is_(True)).count(),
        "avg_readiness": round(avg_readiness, 2),
        "avg_composite_score": round(float(avg_comp), 2),
        "top_benchmarks": benchmarks,
        "recent_insights": insights,
        "health_summary": health_summary,
    }
