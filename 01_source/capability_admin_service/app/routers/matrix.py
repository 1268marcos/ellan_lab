from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.matrix_service import build_matrix

router = APIRouter(tags=["matrix"])


@router.get("/matrix")
def matrix(db: Session = Depends(get_db)):
    return build_matrix(db)
