from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ListOut
from app.services import intelligence_service

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


class FlagPatch(BaseModel):
    is_enabled: bool


@router.post("/recompute", status_code=status.HTTP_200_OK)
def recompute(db: Session = Depends(get_db)):
    return intelligence_service.recompute_intelligence(db)


@router.get("/readiness", response_model=ListOut)
def readiness(profile_id: int | None = None, db: Session = Depends(get_db)) -> ListOut:
    items = intelligence_service.list_readiness(db, profile_id)
    return ListOut(
        items=[
            {
                "profile_id": r.profile_id,
                "profile_code": r.profile_code,
                "score": r.score,
                "grade": r.grade,
                "dimensions": r.dimensions_json,
                "gaps": r.gaps_json,
                "computed_at": r.computed_at.isoformat() if r.computed_at else None,
            }
            for r in items
        ],
        total=len(items),
    )


@router.get("/insights", response_model=ListOut)
def insights(
    status_filter: str | None = Query("OPEN", alias="status"),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> ListOut:
    items = intelligence_service.list_insights(db, status_filter, limit)
    return ListOut(
        items=[
            {
                "id": i.id,
                "severity": i.severity,
                "category": i.category,
                "title": i.title,
                "detail": i.detail,
                "status": i.status,
                "recommendation": i.recommendation,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ],
        total=len(items),
    )


@router.get("/recommendations", response_model=ListOut)
def recommendations(db: Session = Depends(get_db)) -> ListOut:
    items = intelligence_service.build_recommendations(db)
    return ListOut(items=items, total=len(items))


@router.get("/world-report")
def world_report(db: Session = Depends(get_db)):
    return intelligence_service.build_world_report(db)


@router.get("/corridors", response_model=ListOut)
def corridors(db: Session = Depends(get_db)) -> ListOut:
    items = intelligence_service.list_corridors(db)
    return ListOut(
        items=[
            {
                "code": c.code,
                "from_region_code": c.from_region_code,
                "to_region_code": c.to_region_code,
                "channel_code": c.channel_code,
                "name": c.name,
                "default_currency": c.default_currency,
            }
            for c in items
        ],
        total=len(items),
    )


@router.get("/feature-flags", response_model=ListOut)
def feature_flags(db: Session = Depends(get_db)) -> ListOut:
    items = intelligence_service.list_feature_flags(db)
    return ListOut(
        items=[
            {
                "code": f.code,
                "name": f.name,
                "scope": f.scope,
                "is_enabled": f.is_enabled,
            }
            for f in items
        ],
        total=len(items),
    )


@router.patch("/feature-flags/{code}")
def patch_flag(code: str, body: FlagPatch, db: Session = Depends(get_db)):
    try:
        row = intelligence_service.set_feature_flag(db, code, body.is_enabled)
    except ValueError:
        raise HTTPException(status_code=404, detail="flag_not_found") from None
    return {"code": row.code, "is_enabled": row.is_enabled}
