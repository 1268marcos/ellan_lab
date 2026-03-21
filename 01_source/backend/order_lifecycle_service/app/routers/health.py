# 01_source/backend/order_lifecycle/app/routers/health.py
from sqlalchemy import text
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return HealthResponse(status="ok", database="ok")