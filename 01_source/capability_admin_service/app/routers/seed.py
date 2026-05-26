from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.seed_data import run_seed

router = APIRouter(tags=["seed"])


@router.post("/seed")
def seed(db: Session = Depends(get_db)) -> dict[str, int]:
    return run_seed(db)
