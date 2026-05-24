from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import fiscal_intelligence_service

router = APIRouter(prefix="/fiscal-intelligence", tags=["fiscal-intelligence"])


class ContingencyIn(BaseModel):
    country: str = Field(min_length=2, max_length=5)
    authority: str = Field(min_length=2, max_length=80)
    contingency_mode: str = Field(min_length=2, max_length=32)
    reason: str | None = None
    region_code: str | None = None
    issuer_code: str | None = None


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    return fiscal_intelligence_service.intelligence_dashboard(db)


@router.post("/analyze")
def analyze(db: Session = Depends(get_db)) -> dict:
    return fiscal_intelligence_service.analyze_fiscal_ops(db)


@router.get("/insights")
def list_insights(
    status: str | None = Query("OPEN"),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> dict:
    rows = fiscal_intelligence_service.list_insights(db, status=status, limit=limit)
    items = [fiscal_intelligence_service.insight_to_dict(r) for r in rows]
    return {"items": items, "total": len(items)}


@router.get("/contingency-events")
def list_contingencies(
    active_only: bool = Query(True),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
) -> dict:
    rows = fiscal_intelligence_service.list_contingencies(db, active_only=active_only, limit=limit)
    items = [fiscal_intelligence_service.contingency_to_dict(r) for r in rows]
    return {"items": items, "total": len(items)}


@router.post("/contingency-events")
def register_contingency(body: ContingencyIn, db: Session = Depends(get_db)) -> dict:
    row = fiscal_intelligence_service.register_contingency(
        db,
        country=body.country,
        authority=body.authority,
        contingency_mode=body.contingency_mode,
        reason=body.reason,
        region_code=body.region_code,
        issuer_code=body.issuer_code,
    )
    return fiscal_intelligence_service.contingency_to_dict(row)


@router.post("/contingency-events/{event_id}/close")
def close_contingency(event_id: str, db: Session = Depends(get_db)) -> dict:
    row = fiscal_intelligence_service.close_contingency(db, event_id)
    if not row:
        raise HTTPException(status_code=404, detail="contingency event not found")
    return fiscal_intelligence_service.contingency_to_dict(row)


@router.post("/seed-demo")
def seed_demo(db: Session = Depends(get_db)) -> dict:
    return fiscal_intelligence_service.seed_demo_intelligence(db)
