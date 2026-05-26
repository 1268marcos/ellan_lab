from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ecosystem import CapabilityProfileAuditLog
from app.schemas.common import ListOut
from app.services import ecosystem_global_service, ecosystem_service

router = APIRouter(prefix="/ecosystem", tags=["ecosystem"])


class BindingIn(BaseModel):
    profile_id: int
    player_id: int
    binding_role: str = "PRIMARY"
    priority: int = 100


@router.get("/segments", response_model=ListOut)
def segments(db: Session = Depends(get_db)) -> ListOut:
    items = ecosystem_service.list_segments(db)
    return ListOut(items=[{"id": s.id, "code": s.code, "name": s.name, "is_active": s.is_active} for s in items], total=len(items))


@router.get("/players", response_model=ListOut)
def players(segment_code: str | None = None, db: Session = Depends(get_db)) -> ListOut:
    items = ecosystem_service.list_players(db, segment_code)
    return ListOut(
        items=[
            {
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "segment_code": p.segment.code if p.segment else None,
                "country_codes": p.country_codes,
                "integration_protocol": p.integration_protocol,
                "is_active": p.is_active,
            }
            for p in items
        ],
        total=len(items),
    )


@router.get("/bindings", response_model=ListOut)
def bindings(profile_id: int | None = None, db: Session = Depends(get_db)) -> ListOut:
    items = ecosystem_service.list_bindings(db, profile_id)
    return ListOut(
        items=[
            {
                "id": b.id,
                "profile_code": b.profile_code,
                "player_code": b.player_code,
                "binding_role": b.binding_role,
                "priority": b.priority,
                "is_active": b.is_active,
            }
            for b in items
        ],
        total=len(items),
    )


@router.post("/bindings", status_code=status.HTTP_201_CREATED)
def create_binding(body: BindingIn, actor: str | None = Query(None), db: Session = Depends(get_db)):
    row = ecosystem_service.bind_player(
        db,
        profile_id=body.profile_id,
        player_id=body.player_id,
        binding_role=body.binding_role,
        priority=body.priority,
        actor=actor,
    )
    return {"id": row.id, "profile_code": row.profile_code, "player_code": row.player_code}


@router.get("/integration-modes", response_model=ListOut)
def integration_modes(db: Session = Depends(get_db)) -> ListOut:
    items = ecosystem_global_service.list_integration_modes(db)
    return ListOut(
        items=[{"id": m.id, "code": m.code, "name": m.name, "is_active": m.is_active} for m in items],
        total=len(items),
    )


@router.get("/player-integrations", response_model=ListOut)
def player_integrations(player_code: str | None = None, db: Session = Depends(get_db)) -> ListOut:
    items = ecosystem_global_service.list_player_integrations(db, player_code)
    return ListOut(
        items=[
            {
                "id": i.id,
                "player_code": i.player_code,
                "integration_mode_code": i.integration_mode_code,
                "direction": i.direction,
                "auth_type": i.auth_type,
                "production_ready": i.production_ready,
            }
            for i in items
        ],
        total=len(items),
    )


@router.get("/locker-presence", response_model=ListOut)
def locker_presence(
    player_code: str | None = None,
    locker_role: str | None = None,
    db: Session = Depends(get_db),
) -> ListOut:
    items = ecosystem_global_service.list_locker_presence(db, player_code, locker_role)
    return ListOut(
        items=[
            {
                "id": r.id,
                "player_code": r.player_code,
                "locker_role": r.locker_role,
                "program_code": r.program_code,
                "program_name": r.program_name,
                "region_scope": r.region_scope,
                "supports_inbound": r.supports_inbound,
                "supports_outbound": r.supports_outbound,
                "supports_returns": r.supports_returns,
            }
            for r in items
        ],
        total=len(items),
    )


@router.get("/player-relations", response_model=ListOut)
def player_relations(
    from_code: str | None = None,
    relation_type: str | None = None,
    db: Session = Depends(get_db),
) -> ListOut:
    items = ecosystem_global_service.list_player_relations(db, from_code, relation_type)
    return ListOut(
        items=[
            {
                "id": r.id,
                "from_player_code": r.from_player_code,
                "to_player_code": r.to_player_code,
                "relation_type": r.relation_type,
                "notes": r.notes,
            }
            for r in items
        ],
        total=len(items),
    )


@router.get("/audit-log", response_model=ListOut)
def audit_log(profile_id: int | None = None, limit: int = Query(100, le=500), db: Session = Depends(get_db)) -> ListOut:
    q = db.query(CapabilityProfileAuditLog).order_by(CapabilityProfileAuditLog.created_at.desc())
    if profile_id:
        q = q.filter(CapabilityProfileAuditLog.profile_id == profile_id)
    items = q.limit(limit).all()
    return ListOut(
        items=[
            {
                "id": a.id,
                "profile_id": a.profile_id,
                "entity_type": a.entity_type,
                "action": a.action,
                "actor": a.actor,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in items
        ],
        total=len(items),
    )
