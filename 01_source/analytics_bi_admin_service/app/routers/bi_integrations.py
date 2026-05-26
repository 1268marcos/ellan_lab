from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.bi_integrations import (
    BiCapabilityLinkOut,
    BiCrossDomainOut,
    BiIntegrationMatrixOut,
    BiIntegrationProfileOut,
)
from app.services import bi_integrations_service

router = APIRouter(prefix="/player-integrations", tags=["player-integrations"])


@router.post("/seed")
def seed(db: Session = Depends(get_db)) -> dict:
    return bi_integrations_service.seed_integrations(db)


@router.get("/matrix", response_model=BiIntegrationMatrixOut)
def matrix(db: Session = Depends(get_db)) -> BiIntegrationMatrixOut:
    return BiIntegrationMatrixOut.model_validate(bi_integrations_service.integration_matrix(db))


@router.get("/profiles")
def list_profiles(
    segment: str | None = Query(None), db: Session = Depends(get_db)
) -> dict:
    rows = bi_integrations_service.list_profiles(db, segment=segment)
    return {
        "profiles": [BiIntegrationProfileOut.model_validate(r) for r in rows],
        "total": len(rows),
    }


@router.get("/capabilities")
def list_capabilities(
    player_code: str | None = Query(None), db: Session = Depends(get_db)
) -> dict:
    rows = bi_integrations_service.list_capabilities(db, player_code=player_code)
    return {
        "capabilities": [BiCapabilityLinkOut.model_validate(r) for r in rows],
        "total": len(rows),
    }


@router.get("/cross-domain")
def list_cross_domain(db: Session = Depends(get_db)) -> dict:
    rows = bi_integrations_service.list_cross_domain(db)
    return {
        "integrations": [BiCrossDomainOut.model_validate(r) for r in rows],
        "total": len(rows),
    }
