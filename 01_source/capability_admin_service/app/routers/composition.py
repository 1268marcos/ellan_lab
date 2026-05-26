from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.capability import CapabilityProfileSnapshot
from app.schemas.common import ListOut
from app.services import composition_service

router = APIRouter(prefix="/profiles", tags=["composition"])


class ActionIn(BaseModel):
    action_code: str
    label: str
    sort_order: int = 100
    is_active: bool = True
    config_json: dict = Field(default_factory=dict)


class MethodIn(BaseModel):
    payment_method_id: int
    label: str | None = None
    sort_order: int = 100
    is_default: bool = False
    is_active: bool = True
    wallet_provider_id: int | None = None
    rules_json: dict = Field(default_factory=dict)


class ConstraintIn(BaseModel):
    code: str
    value_json: dict


class TargetIn(BaseModel):
    target_type: str
    target_key: str
    is_active: bool = True
    metadata_json: dict = Field(default_factory=dict)


@router.get("/{profile_id}/actions", response_model=ListOut)
def get_actions(profile_id: int, db: Session = Depends(get_db)) -> ListOut:
    items = composition_service.list_actions(db, profile_id)
    return ListOut(items=[{"id": i.id, "action_code": i.action_code, "label": i.label, "is_active": i.is_active} for i in items], total=len(items))


@router.post("/{profile_id}/actions", status_code=201)
def post_action(profile_id: int, body: ActionIn, actor: str | None = Query(None), db: Session = Depends(get_db)):
    row = composition_service.add_action(db, profile_id, body.model_dump(), actor=actor)
    return {"id": row.id, "action_code": row.action_code}


@router.get("/{profile_id}/methods", response_model=ListOut)
def get_methods(profile_id: int, db: Session = Depends(get_db)) -> ListOut:
    items = composition_service.list_methods(db, profile_id)
    return ListOut(
        items=[
            {
                "id": i.id,
                "payment_method_id": i.payment_method_id,
                "is_default": i.is_default,
                "sort_order": i.sort_order,
                "is_active": i.is_active,
            }
            for i in items
        ],
        total=len(items),
    )


@router.post("/{profile_id}/methods", status_code=201)
def post_method(profile_id: int, body: MethodIn, actor: str | None = Query(None), db: Session = Depends(get_db)):
    row = composition_service.add_method(db, profile_id, body.model_dump(), actor=actor)
    return {"id": row.id, "payment_method_id": row.payment_method_id}


@router.get("/{profile_id}/constraints", response_model=ListOut)
def get_constraints(profile_id: int, db: Session = Depends(get_db)) -> ListOut:
    items = composition_service.list_constraints(db, profile_id)
    return ListOut(items=[{"id": i.id, "code": i.code, "value_json": i.value_json} for i in items], total=len(items))


@router.put("/{profile_id}/constraints")
def put_constraint(profile_id: int, body: ConstraintIn, actor: str | None = Query(None), db: Session = Depends(get_db)):
    row = composition_service.upsert_constraint(db, profile_id, body.code, body.value_json, actor=actor)
    return {"id": row.id, "code": row.code}


@router.get("/{profile_id}/targets", response_model=ListOut)
def get_targets(profile_id: int, db: Session = Depends(get_db)) -> ListOut:
    items = composition_service.list_targets(db, profile_id)
    return ListOut(
        items=[{"id": i.id, "target_type": i.target_type, "target_key": i.target_key, "is_active": i.is_active} for i in items],
        total=len(items),
    )


@router.post("/{profile_id}/targets", status_code=201)
def post_target(profile_id: int, body: TargetIn, actor: str | None = Query(None), db: Session = Depends(get_db)):
    row = composition_service.add_target(db, profile_id, body.model_dump(), actor=actor)
    return {"id": row.id, "target_key": row.target_key}


@router.get("/{profile_id}/snapshots/list", response_model=ListOut)
def list_snapshots(profile_id: int, db: Session = Depends(get_db)) -> ListOut:
    items = (
        db.query(CapabilityProfileSnapshot)
        .filter(CapabilityProfileSnapshot.profile_id == profile_id)
        .order_by(CapabilityProfileSnapshot.snapshot_version.desc())
        .all()
    )
    return ListOut(
        items=[
            {
                "id": s.id,
                "snapshot_version": s.snapshot_version,
                "created_by": s.created_by,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in items
        ],
        total=len(items),
    )
