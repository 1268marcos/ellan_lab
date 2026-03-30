# 01_source/backend/runtime/app/services/runtime_bootstrap_service.py
from __future__ import annotations

from fastapi import HTTPException

from app.core.config import settings
from app.repositories.runtime_registry_repo import invalidate_runtime_locker_cache
from app.services.runtime_registry_schema_service import ensure_runtime_registry_schema
from app.services.runtime_registry_sync_service import sync_runtime_registry_from_central


def _build_error(
    *,
    err_type: str,
    message: str,
    retryable: bool,
    **extra,
) -> dict:
    detail = {
        "type": err_type,
        "message": message,
        "retryable": retryable,
    }
    if extra:
        detail.update(extra)
    return detail


def bootstrap_runtime_on_startup() -> dict:
    """
    Bootstrap operacional do backend/runtime.

    Etapas:
    1. garantir schema do runtime registry
    2. sincronizar dados a partir da fonte central
    3. invalidar cache do resolver
    """
    steps: list[dict] = []

    if settings.runtime_apply_schema_on_startup:
        schema_result = ensure_runtime_registry_schema()
        steps.append(
            {
                "step": "ensure_runtime_registry_schema",
                "result": schema_result,
            }
        )

    if settings.runtime_sync_on_startup:
        sync_result = sync_runtime_registry_from_central(
            locker_id=None,
            prune_missing=settings.runtime_sync_prune_missing_on_startup,
        )
        steps.append(
            {
                "step": "sync_runtime_registry_from_central",
                "result": sync_result,
            }
        )

        invalidate_runtime_locker_cache(None)
        steps.append(
            {
                "step": "invalidate_runtime_registry_cache",
                "result": {
                    "ok": True,
                    "scope": "all",
                },
            }
        )

    return {
        "ok": True,
        "message": "Runtime bootstrap completed successfully.",
        "apply_schema_on_startup": settings.runtime_apply_schema_on_startup,
        "sync_on_startup": settings.runtime_sync_on_startup,
        "prune_missing_on_startup": settings.runtime_sync_prune_missing_on_startup,
        "steps": steps,
    }


def safe_bootstrap_runtime_on_startup() -> dict:
    """
    Wrapper para uso no startup do FastAPI.
    Mantém erro rico e permite fail-fast configurável.
    """
    try:
        return bootstrap_runtime_on_startup()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="RUNTIME_BOOTSTRAP_FAILED",
                message="Unexpected failure during runtime bootstrap.",
                retryable=True,
                error=str(exc),
            ),
        ) from exc