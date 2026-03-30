# 01_source/backend/runtime/app/routers/internal_runtime.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Query

from app.core.internal_auth import require_internal_token
from app.core.locker_runtime_resolver import resolve_runtime_locker
from app.repositories.runtime_registry_repo import invalidate_runtime_locker_cache
from app.schemas.runtime_registry import RuntimeLockerContextOut
from app.services.runtime_bootstrap_service import bootstrap_runtime_on_startup
from app.services.runtime_registry_sync_service import sync_runtime_registry_from_central
from app.services.runtime_registry_schema_service import ensure_runtime_registry_schema


router = APIRouter(prefix="/internal/runtime", tags=["internal-runtime"])


@router.get("/lockers/resolve", response_model=RuntimeLockerContextOut)
def resolve_locker(
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
    _=Depends(require_internal_token),
):
    return RuntimeLockerContextOut(**resolve_runtime_locker(x_locker_id))


@router.post("/lockers/cache/invalidate")
def invalidate_cache(
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
    _=Depends(require_internal_token),
):
    invalidate_runtime_locker_cache(x_locker_id)
    return {
        "ok": True,
        "cache_invalidated": True,
        "locker_id": x_locker_id,
    }


@router.post("/schema/ensure")
def ensure_schema(
    _=Depends(require_internal_token),
):
    return ensure_runtime_registry_schema()


@router.post("/sync-from-central")
def sync_from_central(
    locker_id: str | None = Query(default=None),
    prune_missing: bool = Query(default=False),
    _=Depends(require_internal_token),
):
    result = sync_runtime_registry_from_central(
        locker_id=locker_id,
        prune_missing=prune_missing,
    )

    invalidate_runtime_locker_cache(locker_id)
    return result


@router.get("/ping")
def ping(_=Depends(require_internal_token)):
    return {"ok": True}


@router.post("/bootstrap")
def bootstrap_runtime(
    _=Depends(require_internal_token),
):
    return bootstrap_runtime_on_startup()