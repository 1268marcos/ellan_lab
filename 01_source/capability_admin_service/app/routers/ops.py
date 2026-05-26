from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ListOut
from app.services import ops_service

router = APIRouter(prefix="/ops", tags=["ops"])


class ResolveIn(BaseModel):
    region_code: str
    channel_code: str
    context_code: str
    active_only: bool = True


class CloneIn(BaseModel):
    source_profile_id: int
    profile_code: str = Field(min_length=1, max_length=160)
    name: str = Field(min_length=1, max_length=180)
    region_id: int | None = None
    channel_id: int | None = None
    context_id: int | None = None
    copy_bindings: bool = True


class BulkActiveIn(BaseModel):
    profile_ids: list[int]
    is_active: bool


class TemplateFromProfileIn(BaseModel):
    code: str
    name: str
    description: str | None = None


class ApplyTemplateIn(BaseModel):
    template_code: str
    profile_code: str
    name: str
    region_id: int
    channel_id: int
    context_id: int


@router.post("/resolve")
def resolve(body: ResolveIn, db: Session = Depends(get_db)):
    return ops_service.resolve_profile(
        db,
        region_code=body.region_code,
        channel_code=body.channel_code,
        context_code=body.context_code,
        active_only=body.active_only,
    )


@router.post("/profiles/clone", status_code=status.HTTP_201_CREATED)
def clone_profile(body: CloneIn, actor: str | None = Query(None), db: Session = Depends(get_db)):
    row = ops_service.clone_profile(
        db,
        body.source_profile_id,
        profile_code=body.profile_code,
        name=body.name,
        region_id=body.region_id,
        channel_id=body.channel_id,
        context_id=body.context_id,
        copy_bindings=body.copy_bindings,
        actor=actor,
    )
    job = ops_service.record_job(db, "CLONE_PROFILE", body.model_dump(), {"profile_id": row.id, "profile_code": row.profile_code})
    db.commit()
    return {"profile_id": row.id, "profile_code": row.profile_code, "job_id": job.id}


@router.get("/profiles/compare")
def compare(profile_id_a: int, profile_id_b: int, db: Session = Depends(get_db)):
    return ops_service.compare_profiles(db, profile_id_a, profile_id_b)


@router.post("/profiles/{profile_id}/simulate")
def simulate(profile_id: int, flow: str = Query("pay"), db: Session = Depends(get_db)):
    return ops_service.simulate_flow(db, profile_id, flow)


@router.post("/profiles/bulk-active")
def bulk_active(body: BulkActiveIn, actor: str | None = Query(None), db: Session = Depends(get_db)):
    result = ops_service.bulk_set_active(db, body.profile_ids, body.is_active, actor=actor)
    job = ops_service.record_job(db, "BULK_ACTIVE", body.model_dump(), result, actor=actor)
    db.commit()
    return {**result, "job_id": job.id}


@router.get("/profiles/{profile_id}/export")
def export_profile(profile_id: int, db: Session = Depends(get_db)):
    return ops_service.export_package(db, profile_id)


@router.get("/templates", response_model=ListOut)
def templates(db: Session = Depends(get_db)) -> ListOut:
    items = ops_service.list_templates(db)
    return ListOut(
        items=[
            {
                "id": t.id,
                "code": t.code,
                "name": t.name,
                "region_code": t.region_code,
                "channel_code": t.channel_code,
                "context_code": t.context_code,
                "currency": t.currency,
            }
            for t in items
        ],
        total=len(items),
    )


@router.post("/templates/from-profile/{profile_id}", status_code=status.HTTP_201_CREATED)
def template_from_profile(profile_id: int, body: TemplateFromProfileIn, db: Session = Depends(get_db)):
    row = ops_service.create_template_from_profile(db, profile_id, body.code, body.name, body.description)
    return {"id": row.id, "code": row.code}


@router.post("/templates/apply", status_code=status.HTTP_201_CREATED)
def apply_template(body: ApplyTemplateIn, db: Session = Depends(get_db)):
    row = ops_service.apply_template(
        db,
        body.template_code,
        profile_code=body.profile_code,
        name=body.name,
        region_id=body.region_id,
        channel_id=body.channel_id,
        context_id=body.context_id,
    )
    return {"profile_id": row.id, "profile_code": row.profile_code}


@router.get("/jobs", response_model=ListOut)
def jobs(limit: int = Query(50, le=200), db: Session = Depends(get_db)) -> ListOut:
    items = ops_service.list_jobs(db, limit)
    return ListOut(
        items=[
            {
                "id": j.id,
                "job_type": j.job_type,
                "status": j.status,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "result": j.result_json,
            }
            for j in items
        ],
        total=len(items),
    )
