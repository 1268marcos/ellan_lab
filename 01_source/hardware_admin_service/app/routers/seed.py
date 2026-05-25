from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.seed_data import run_domain_full_seed, run_seed

router = APIRouter(prefix="/seed", tags=["seed"])


@router.post("")
def seed(db: Session = Depends(get_db)) -> dict:
    return run_seed(db)


@router.post("/domain-full")
def seed_domain_full(
    mirror_external: bool = Query(False), db: Session = Depends(get_db)
) -> dict:
    return run_domain_full_seed(db, mirror_external=mirror_external)
