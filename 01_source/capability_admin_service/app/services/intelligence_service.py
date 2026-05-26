from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.capability import (
    CapabilityProfile,
    CapabilityProfileAction,
    CapabilityProfileConstraint,
    CapabilityProfileMethod,
)
from app.models.ecosystem import CapabilityProfilePlayerBinding
from app.models.ecosystem_global import CapabilityPlayerLockerPresence
from app.models.integration import CapabilityProfileWebhook
from app.models.intelligence import (
    CapabilityCorridor,
    CapabilityFeatureFlag,
    CapabilityInsight,
    CapabilityProfileReadiness,
)
from app.services.matrix_service import build_matrix


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def seed_intelligence_baseline(db: Session) -> dict[str, int]:
    counts = {"feature_flags": 0, "corridors": 0}
    flags = [
        ("LOCKER_WORLD_PRESET", "Preset ecossistema locker mundial", "GLOBAL", True),
        ("AUTO_INSIGHT_RECOMPUTE", "Recalcular insights apos seed", "GLOBAL", True),
        ("MATRIX_STRICT_MODE", "Exigir perfil em toda celula matriz", "GLOBAL", False),
        ("WEBHOOK_REQUIRED", "Webhook obrigatorio por perfil ativo", "GLOBAL", False),
        ("PLAYER_BINDING_MIN", "Binding minimo perfil-player", "GLOBAL", True),
    ]
    for code, name, scope, enabled in flags:
        if db.query(CapabilityFeatureFlag).filter(CapabilityFeatureFlag.code == code).first():
            continue
        db.add(
            CapabilityFeatureFlag(
                code=code,
                name=name,
                scope=scope,
                is_enabled=enabled,
                metadata_json={},
            )
        )
        counts["feature_flags"] += 1
    corridors = [
        ("BR_SP_KIOSK", "SP", "SP", "kiosk", "Corredor SP Kiosk", "BRL"),
        ("PT_KIOSK", "PT", "PT", "kiosk", "Corredor PT Kiosk", "EUR"),
        ("DE_CARRIER", "DE", "DE", "carrier", "Corredor DE Carrier OOH", "EUR"),
        ("UK_ONLINE", "UK", "UK", "online", "Corredor UK Online", "GBP"),
        ("BR_PT_CROSS", "SP", "PT", "partner", "Corredor cross-border BR-PT", "EUR"),
    ]
    for code, fr, to, ch, name, cur in corridors:
        if db.query(CapabilityCorridor).filter(CapabilityCorridor.code == code).first():
            continue
        db.add(
            CapabilityCorridor(
                code=code,
                from_region_code=fr,
                to_region_code=to,
                channel_code=ch,
                name=name,
                default_currency=cur,
                is_active=True,
                metadata_json={},
            )
        )
        counts["corridors"] += 1
    db.flush()
    return counts


def _profile_dimensions(db: Session, profile: CapabilityProfile) -> tuple[dict, list[str], int]:
    gaps: list[str] = []
    actions = (
        db.query(func.count(CapabilityProfileAction.id))
        .filter(CapabilityProfileAction.profile_id == profile.id, CapabilityProfileAction.is_active.is_(True))
        .scalar()
        or 0
    )
    methods = (
        db.query(func.count(CapabilityProfileMethod.id))
        .filter(CapabilityProfileMethod.profile_id == profile.id, CapabilityProfileMethod.is_active.is_(True))
        .scalar()
        or 0
    )
    constraints = (
        db.query(func.count(CapabilityProfileConstraint.id))
        .filter(CapabilityProfileConstraint.profile_id == profile.id)
        .scalar()
        or 0
    )
    bindings = (
        db.query(func.count(CapabilityProfilePlayerBinding.id))
        .filter(
            CapabilityProfilePlayerBinding.profile_id == profile.id,
            CapabilityProfilePlayerBinding.is_active.is_(True),
        )
        .scalar()
        or 0
    )
    webhooks = (
        db.query(func.count(CapabilityProfileWebhook.id))
        .filter(CapabilityProfileWebhook.profile_id == profile.id, CapabilityProfileWebhook.active.is_(True))
        .scalar()
        or 0
    )
    dims = {
        "actions": actions,
        "payment_methods": methods,
        "constraints": constraints,
        "player_bindings": bindings,
        "webhooks": webhooks,
    }
    weights = {"actions": 20, "payment_methods": 25, "constraints": 15, "player_bindings": 25, "webhooks": 15}
    score = 0
    for key, weight in weights.items():
        val = dims[key]
        if val > 0:
            score += weight
        else:
            gaps.append(f"missing_{key}")
    if not profile.is_active:
        gaps.append("profile_inactive")
        score = max(0, score - 20)
    return dims, gaps, min(100, score)


def recompute_intelligence(db: Session) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    db.query(CapabilityInsight).filter(CapabilityInsight.status == "OPEN").update(
        {"status": "SUPERSEDED", "resolved_at": now},
        synchronize_session=False,
    )
    profiles = db.query(CapabilityProfile).all()
    readiness_count = 0
    for p in profiles:
        dims, gaps, score = _profile_dimensions(db, p)
        grade = _grade(score)
        row = db.query(CapabilityProfileReadiness).filter(CapabilityProfileReadiness.profile_id == p.id).first()
        if row:
            row.score = score
            row.grade = grade
            row.dimensions_json = dims
            row.gaps_json = gaps
            row.computed_at = now
        else:
            db.add(
                CapabilityProfileReadiness(
                    profile_id=p.id,
                    profile_code=p.profile_code,
                    score=score,
                    grade=grade,
                    dimensions_json=dims,
                    gaps_json=gaps,
                    computed_at=now,
                )
            )
        readiness_count += 1
        if gaps:
            db.add(
                CapabilityInsight(
                    id=str(uuid.uuid4()),
                    severity="WARN" if score < 60 else "INFO",
                    category="PROFILE_GAP",
                    title=f"Gaps no perfil {p.profile_code}",
                    detail=", ".join(gaps),
                    entity_type="profile",
                    entity_id=str(p.id),
                    status="OPEN",
                    recommendation="Adicione acoes, metodos, bindings ou webhook conforme gaps.",
                    metadata_json={"score": score, "grade": grade},
                )
            )

    matrix = build_matrix(db)
    if matrix["coverage_pct"] < 80:
        db.add(
            CapabilityInsight(
                id=str(uuid.uuid4()),
                severity="WARN",
                category="MATRIX_COVERAGE",
                title="Cobertura de matriz abaixo do alvo",
                detail=f"coverage={matrix['coverage_pct']}%",
                entity_type="matrix",
                entity_id="global",
                status="OPEN",
                recommendation="Crie perfis para celulas region x canal x contexto sem cobertura.",
                metadata_json={"coverage_pct": matrix["coverage_pct"]},
            )
        )

    locker_count = db.query(func.count(CapabilityPlayerLockerPresence.id)).scalar() or 0
    if locker_count < 15:
        db.add(
            CapabilityInsight(
                id=str(uuid.uuid4()),
                severity="INFO",
                category="LOCKER_WORLD",
                title="Ecossistema locker pode ser expandido",
                detail=f"locker_presences={locker_count}",
                entity_type="ecosystem",
                entity_id="locker",
                status="OPEN",
                recommendation="Execute seed mundial e revise locker-presence.",
                metadata_json={"locker_presences": locker_count},
            )
        )

    db.commit()
    open_insights = db.query(func.count(CapabilityInsight.id)).filter(CapabilityInsight.status == "OPEN").scalar() or 0
    return {
        "readiness_profiles": readiness_count,
        "open_insights": open_insights,
        "avg_readiness_score": int(
            db.query(func.avg(CapabilityProfileReadiness.score)).scalar() or 0
        ),
    }


def list_readiness(db: Session, profile_id: int | None = None) -> list[CapabilityProfileReadiness]:
    q = db.query(CapabilityProfileReadiness).order_by(CapabilityProfileReadiness.score.desc())
    if profile_id:
        q = q.filter(CapabilityProfileReadiness.profile_id == profile_id)
    return q.all()


def list_insights(db: Session, status: str | None = "OPEN", limit: int = 100) -> list[CapabilityInsight]:
    q = db.query(CapabilityInsight).order_by(CapabilityInsight.created_at.desc())
    if status:
        q = q.filter(CapabilityInsight.status == status)
    return q.limit(limit).all()


def list_corridors(db: Session) -> list[CapabilityCorridor]:
    return db.query(CapabilityCorridor).filter(CapabilityCorridor.is_active.is_(True)).order_by(CapabilityCorridor.code).all()


def list_feature_flags(db: Session) -> list[CapabilityFeatureFlag]:
    return db.query(CapabilityFeatureFlag).order_by(CapabilityFeatureFlag.code).all()


def set_feature_flag(db: Session, code: str, enabled: bool) -> CapabilityFeatureFlag:
    row = db.query(CapabilityFeatureFlag).filter(CapabilityFeatureFlag.code == code).first()
    if not row:
        raise ValueError("flag_not_found")
    row.is_enabled = enabled
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def build_recommendations(db: Session) -> list[dict]:
    recs: list[dict] = []
    low = (
        db.query(CapabilityProfileReadiness)
        .filter(CapabilityProfileReadiness.score < 70)
        .order_by(CapabilityProfileReadiness.score)
        .limit(10)
        .all()
    )
    for r in low:
        for gap in r.gaps_json or []:
            recs.append(
                {
                    "priority": "HIGH" if r.score < 50 else "MEDIUM",
                    "profile_code": r.profile_code,
                    "action": f"resolve_{gap}",
                    "message": f"Perfil {r.profile_code}: corrigir {gap}",
                }
            )
    insights = list_insights(db, status="OPEN", limit=5)
    for ins in insights:
        recs.append(
            {
                "priority": ins.severity,
                "profile_code": None,
                "action": ins.category,
                "message": ins.recommendation or ins.title,
            }
        )
    return recs[:25]


def build_world_report(db: Session) -> dict:
    from app.services.dashboard_service import get_dashboard

    dash = get_dashboard(db)
    matrix = build_matrix(db)
    readiness = db.query(CapabilityProfileReadiness).all()
    avg_score = int(sum(r.score for r in readiness) / len(readiness)) if readiness else 0
    grades = {}
    for r in readiness:
        grades[r.grade] = grades.get(r.grade, 0) + 1
    return {
        "dashboard": dash.model_dump(),
        "matrix_coverage_pct": matrix["coverage_pct"],
        "readiness": {
            "profiles_scored": len(readiness),
            "avg_score": avg_score,
            "grade_distribution": grades,
        },
        "open_insights": db.query(func.count(CapabilityInsight.id))
        .filter(CapabilityInsight.status == "OPEN")
        .scalar()
        or 0,
        "active_corridors": db.query(func.count(CapabilityCorridor.id))
        .filter(CapabilityCorridor.is_active.is_(True))
        .scalar()
        or 0,
        "locker_presences": db.query(func.count(CapabilityPlayerLockerPresence.id)).scalar() or 0,
        "feature_flags_enabled": db.query(func.count(CapabilityFeatureFlag.id))
        .filter(CapabilityFeatureFlag.is_enabled.is_(True))
        .scalar()
        or 0,
    }
