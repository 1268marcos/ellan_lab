from fastapi import APIRouter, Depends, Request

from app.workers.stream_consumer import read_dlq

router = APIRouter(prefix="/api/v1", tags=["dlq"])


@router.get("/dlq")
def list_dlq(request: Request, limit: int = 50) -> list[dict]:
    r = getattr(request.app.state, "redis", None)
    return read_dlq(r, count=limit)
