from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def ready(request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="db_unavailable") from exc
    r = getattr(request.app.state, "redis", None)
    if r is None:
        raise HTTPException(status_code=503, detail="redis_unavailable")
    try:
        r.ping()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="redis_ping_failed") from exc
    return {"status": "ready"}


@router.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "live"}
