from fastapi import APIRouter, HTTPException, Request

from app.core.health import health_payload

router = APIRouter(tags=["health"])


@router.get("/api/v1/health")
def health() -> dict:
    return health_payload()


@router.get("/health/ready")
def ready(request: Request) -> dict[str, str]:
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
    return {"status": "alive"}
