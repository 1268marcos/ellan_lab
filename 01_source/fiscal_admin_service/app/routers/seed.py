from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.fiscal_global_ops_service import seed_global_ops
from app.services.seed_data import run_seed

router = APIRouter(tags=["seed"])


@router.post("/seed")
def seed(db: Session = Depends(get_db)) -> dict[str, int | dict[str, int]]:
    base = run_seed(db)
    global_counts = seed_global_ops(db)
    return {**base, "global_ops": global_counts}
