from fastapi import APIRouter

from app.core.health import health_payload

router = APIRouter(tags=["health"])


@router.get("/api/v1/health")
def health() -> dict:
    return health_payload()
