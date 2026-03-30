# 01_source/backend/runtime/app/routers/health.py
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {
        "ok": True,
        "service": "backend_runtime",
    }