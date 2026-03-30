# 01_source/backend/runtime/app/routers/internal_runtime.py
from fastapi import APIRouter, Depends
from app.core.internal_auth import require_internal_token

router = APIRouter(prefix="/internal/runtime", tags=["internal-runtime"])


@router.get("/ping")
def ping(_=Depends(require_internal_token)):
    return {"ok": True}