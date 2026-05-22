from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.partner_ecosystem import (
    CertificationMirrorOut,
    CorridorSlaOut,
    EcosystemReadinessOut,
    GlobalCorridorOut,
    GlobalOpsSummaryOut,
    PlayerCertificationOut,
    RelationHealthOut,
)
from app.services import partner_global_ops_service as svc

router = APIRouter(prefix="/ecosystem/global-ops", tags=["partner-global-ops"])


@router.get("/summary", response_model=GlobalOpsSummaryOut)
def global_ops_summary(db: Session = Depends(get_db)) -> GlobalOpsSummaryOut:
    return GlobalOpsSummaryOut(**svc.global_ops_summary(db))


@router.post("/seed")
def seed_global_ops(db: Session = Depends(get_db)) -> dict:
    return svc.seed_global_ops(db)


@router.post("/recompute-readiness")
def recompute_readiness(db: Session = Depends(get_db)) -> dict:
    out = svc.recompute_ecosystem_readiness(db)
    db.commit()
    return out


@router.post("/recompute-relation-health")
def recompute_relation_health(db: Session = Depends(get_db)) -> dict:
    out = svc.recompute_relation_health(db)
    db.commit()
    return out


@router.get("/certifications", response_model=list[PlayerCertificationOut])
def list_certifications(
    player_code: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[PlayerCertificationOut]:
    return [PlayerCertificationOut.model_validate(r) for r in svc.list_certifications(db, player_code=player_code)]


@router.get("/corridors", response_model=list[GlobalCorridorOut])
def list_corridors(
    origin: str | None = Query(None),
    dest: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[GlobalCorridorOut]:
    return [GlobalCorridorOut.model_validate(r) for r in svc.list_corridors(db, origin=origin, dest=dest)]


@router.get("/readiness", response_model=list[EcosystemReadinessOut])
def list_readiness(
    band: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[EcosystemReadinessOut]:
    rows = svc.list_ecosystem_readiness(db, band=band, limit=limit)
    out: list[EcosystemReadinessOut] = []
    for r in rows:
        try:
            blockers = json.loads(r.blockers_json or "[]")
        except json.JSONDecodeError:
            blockers = []
        out.append(
            EcosystemReadinessOut(
                ecosystem_player_id=r.ecosystem_player_id,
                player_code=r.player_code,
                score_total=float(r.score_total),
                score_certifications=float(r.score_certifications),
                score_capabilities=float(r.score_capabilities),
                score_corridors=float(r.score_corridors),
                score_webhooks=float(r.score_webhooks),
                readiness_band=r.readiness_band,
                blockers=blockers,
                computed_at=r.computed_at,
            )
        )
    return out


@router.get("/relation-health", response_model=list[RelationHealthOut])
def list_relation_health(
    status: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[RelationHealthOut]:
    return [RelationHealthOut.model_validate(r) for r in svc.list_relation_health(db, status=status)]


@router.get("/corridor-sla", response_model=list[CorridorSlaOut])
def list_corridor_sla(
    compliance_status: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[CorridorSlaOut]:
    return [CorridorSlaOut.model_validate(r) for r in svc.list_corridor_sla(db, compliance_status=compliance_status)]


@router.post("/corridor-sla/seed")
def seed_corridor_sla(db: Session = Depends(get_db)) -> dict[str, int]:
    n = svc.seed_corridor_sla(db)
    db.commit()
    return {"corridor_sla": n}


@router.post("/certifications/mirror", response_model=CertificationMirrorOut)
def mirror_certifications(db: Session = Depends(get_db)) -> CertificationMirrorOut:
    out = svc.mirror_certifications_bidirectional(db)
    db.commit()
    return CertificationMirrorOut(**out)
