from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.capability import CapabilityProfile
from app.models.ecosystem import (
    CapabilityEcosystemPlayer,
    CapabilityEcosystemSegment,
    CapabilityProfilePlayerBinding,
)
from app.services.audit_service import log_audit


def list_segments(db: Session) -> list[CapabilityEcosystemSegment]:
    return db.query(CapabilityEcosystemSegment).order_by(CapabilityEcosystemSegment.sort_order).all()


def list_players(db: Session, segment_code: str | None = None) -> list[CapabilityEcosystemPlayer]:
    q = db.query(CapabilityEcosystemPlayer).options(joinedload(CapabilityEcosystemPlayer.segment))
    if segment_code:
        seg = db.query(CapabilityEcosystemSegment).filter(CapabilityEcosystemSegment.code == segment_code).first()
        if seg:
            q = q.filter(CapabilityEcosystemPlayer.segment_id == seg.id)
    return q.order_by(CapabilityEcosystemPlayer.code).all()


def list_bindings(db: Session, profile_id: int | None = None) -> list[CapabilityProfilePlayerBinding]:
    q = db.query(CapabilityProfilePlayerBinding).options(joinedload(CapabilityProfilePlayerBinding.player))
    if profile_id:
        q = q.filter(CapabilityProfilePlayerBinding.profile_id == profile_id)
    return q.order_by(CapabilityProfilePlayerBinding.priority).all()


def bind_player(
    db: Session,
    *,
    profile_id: int,
    player_id: int,
    binding_role: str = "PRIMARY",
    priority: int = 100,
    actor: str | None = None,
) -> CapabilityProfilePlayerBinding:
    profile = db.get(CapabilityProfile, profile_id)
    player = db.get(CapabilityEcosystemPlayer, player_id)
    if not profile or not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="profile_or_player_not_found")
    existing = (
        db.query(CapabilityProfilePlayerBinding)
        .filter(
            CapabilityProfilePlayerBinding.profile_id == profile_id,
            CapabilityProfilePlayerBinding.player_id == player_id,
        )
        .first()
    )
    if existing:
        existing.binding_role = binding_role
        existing.priority = priority
        existing.is_active = True
        row = existing
    else:
        row = CapabilityProfilePlayerBinding(
            profile_id=profile_id,
            player_id=player_id,
            profile_code=profile.profile_code,
            player_code=player.code,
            binding_role=binding_role,
            priority=priority,
            is_active=True,
        )
        db.add(row)
    log_audit(
        db,
        entity_type="player_binding",
        entity_id=f"{profile_id}:{player_id}",
        action="BIND",
        profile_id=profile_id,
        actor=actor,
        payload={"player_code": player.code, "binding_role": binding_role},
    )
    db.commit()
    db.refresh(row)
    return row
