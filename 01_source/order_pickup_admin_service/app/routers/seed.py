from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.seed_data import run_seed

router = APIRouter(prefix="/seed", tags=["seed"])


@router.post("")
def seed(db: Session = Depends(get_db)) -> dict:
    return run_seed(db)
