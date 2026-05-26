from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.capability import (
    CapabilityProfile,
    CapabilityProfileAction,
    CapabilityProfileConstraint,
    CapabilityProfileMethod,
    CapabilityProfileTarget,
    PaymentMethodCatalog,
)
from app.services.audit_service import log_audit


def list_actions(db: Session, profile_id: int) -> list[CapabilityProfileAction]:
    return db.query(CapabilityProfileAction).filter(CapabilityProfileAction.profile_id == profile_id).all()


def add_action(db: Session, profile_id: int, body: dict, actor: str | None = None) -> CapabilityProfileAction:
    profile = db.get(CapabilityProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="profile_not_found")
    row = CapabilityProfileAction(profile_id=profile_id, **body)
    db.add(row)
    log_audit(db, entity_type="profile_action", entity_id=str(profile_id), action="CREATE", profile_id=profile_id, actor=actor, payload=body)
    db.commit()
    db.refresh(row)
    return row


def list_methods(db: Session, profile_id: int) -> list[CapabilityProfileMethod]:
    return db.query(CapabilityProfileMethod).filter(CapabilityProfileMethod.profile_id == profile_id).all()


def add_method(db: Session, profile_id: int, body: dict, actor: str | None = None) -> CapabilityProfileMethod:
    profile = db.get(CapabilityProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="profile_not_found")
    pm = db.get(PaymentMethodCatalog, body["payment_method_id"])
    if not pm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="payment_method_not_found")
    row = CapabilityProfileMethod(
        profile_id=profile_id,
        payment_method_id=body["payment_method_id"],
        label=body.get("label"),
        sort_order=body.get("sort_order", 100),
        is_default=body.get("is_default", False),
        is_active=body.get("is_active", True),
        wallet_provider_id=body.get("wallet_provider_id"),
        rules_json=body.get("rules_json") or {},
    )
    db.add(row)
    log_audit(db, entity_type="profile_method", entity_id=str(profile_id), action="CREATE", profile_id=profile_id, actor=actor)
    db.commit()
    db.refresh(row)
    return row


def list_constraints(db: Session, profile_id: int) -> list[CapabilityProfileConstraint]:
    return db.query(CapabilityProfileConstraint).filter(CapabilityProfileConstraint.profile_id == profile_id).all()


def upsert_constraint(db: Session, profile_id: int, code: str, value_json: dict, actor: str | None = None) -> CapabilityProfileConstraint:
    row = (
        db.query(CapabilityProfileConstraint)
        .filter(CapabilityProfileConstraint.profile_id == profile_id, CapabilityProfileConstraint.code == code)
        .first()
    )
    if row:
        row.value_json = value_json
    else:
        row = CapabilityProfileConstraint(profile_id=profile_id, code=code, value_json=value_json)
        db.add(row)
    log_audit(db, entity_type="profile_constraint", entity_id=code, action="UPSERT", profile_id=profile_id, actor=actor)
    db.commit()
    db.refresh(row)
    return row


def list_targets(db: Session, profile_id: int) -> list[CapabilityProfileTarget]:
    return db.query(CapabilityProfileTarget).filter(CapabilityProfileTarget.profile_id == profile_id).all()


def add_target(db: Session, profile_id: int, body: dict, actor: str | None = None) -> CapabilityProfileTarget:
    row = CapabilityProfileTarget(profile_id=profile_id, **body)
    db.add(row)
    log_audit(db, entity_type="profile_target", entity_id=body.get("target_key", ""), action="CREATE", profile_id=profile_id, actor=actor)
    db.commit()
    db.refresh(row)
    return row
