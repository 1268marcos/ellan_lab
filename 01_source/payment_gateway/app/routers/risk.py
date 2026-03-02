from __future__ import annotations

import time
from fastapi import APIRouter

from app.core.policies import list_policies

router = APIRouter()

@router.get("/risk/policies")
def get_policies():
    """
    01_source/payment_gateway/app/routers/risk.py

    Obter as políticas de risco.
    """
    return {
        "service": "payment_gateway",
        "endpoint": "/risk/policies",
        "timestamp": time.time(),
        "policies": list_policies(),
    }