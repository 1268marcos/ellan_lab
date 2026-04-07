# 01_source/order_pickup_service/app/services/capability_constraint_service.py
# 06/04/2026 - novo arquivo

from __future__ import annotations

from typing import Any
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.payment_capability_service import get_payment_capabilities


def get_capability_constraint(
    *,
    db: Session,
    region: str,
    channel: str,
    context: str,
    code: str,
    required: bool = True,
    default: Any = None,
) -> Any:
    """
    Resolve constraint diretamente do capability_profile (DB = source of truth)
    """

    capabilities = get_payment_capabilities(
        db=db,
        region=region,
        channel=channel,
        context=context,
    )

    if not capabilities.get("found"):
        raise HTTPException(
            status_code=400,
            detail={
                "type": "CAPABILITY_PROFILE_NOT_FOUND",
                "message": "Capability profile não encontrado.",
                "region": region,
                "channel": channel,
                "context": context,
            },
        )

    constraints = capabilities.get("constraints") or {}

    if code in constraints:
        return constraints[code]

    if required:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "CAPABILITY_CONSTRAINT_MISSING",
                "message": f"Constraint obrigatória não encontrada: {code}",
                "region": region,
                "channel": channel,
                "context": context,
                "available": list(constraints.keys()),
            },
        )

    return default