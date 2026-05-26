from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.ecosystem_global import (
    CapabilityIntegrationMode,
    CapabilityPlayerIntegration,
    CapabilityPlayerLockerPresence,
    CapabilityPlayerRelation,
)


def list_integration_modes(db: Session) -> list[CapabilityIntegrationMode]:
    return db.query(CapabilityIntegrationMode).order_by(CapabilityIntegrationMode.code).all()


def list_player_integrations(db: Session, player_code: str | None = None) -> list[CapabilityPlayerIntegration]:
    q = db.query(CapabilityPlayerIntegration).filter(CapabilityPlayerIntegration.is_active.is_(True))
    if player_code:
        q = q.filter(CapabilityPlayerIntegration.player_code == player_code)
    return q.order_by(CapabilityPlayerIntegration.player_code).all()


def list_locker_presence(
    db: Session,
    player_code: str | None = None,
    locker_role: str | None = None,
) -> list[CapabilityPlayerLockerPresence]:
    q = db.query(CapabilityPlayerLockerPresence).filter(CapabilityPlayerLockerPresence.is_active.is_(True))
    if player_code:
        q = q.filter(CapabilityPlayerLockerPresence.player_code == player_code)
    if locker_role:
        q = q.filter(CapabilityPlayerLockerPresence.locker_role == locker_role)
    return q.order_by(CapabilityPlayerLockerPresence.player_code).all()


def list_player_relations(
    db: Session, from_code: str | None = None, relation_type: str | None = None
) -> list[CapabilityPlayerRelation]:
    q = db.query(CapabilityPlayerRelation).filter(CapabilityPlayerRelation.is_active.is_(True))
    if from_code:
        q = q.filter(CapabilityPlayerRelation.from_player_code == from_code)
    if relation_type:
        q = q.filter(CapabilityPlayerRelation.relation_type == relation_type)
    return q.order_by(CapabilityPlayerRelation.from_player_code).all()
