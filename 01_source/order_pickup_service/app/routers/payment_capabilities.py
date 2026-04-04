# 01_source/order_pickup_service/app/routers/payment_capabilities.py

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.payment_capability_service import get_payment_capabilities

router = APIRouter(
    prefix="/payment-capabilities",
    tags=["payment-capabilities"],
)


@router.get("/")
def read_payment_capabilities(
    region: str = Query(..., min_length=2, max_length=20),
    channel: Literal["online", "kiosk"] = Query(...),
    context: str = Query(..., min_length=2, max_length=80),
    db: Session = Depends(get_db),
):
    payload = get_payment_capabilities(
        db=db,
        region=region.strip().upper(),
        channel=channel.strip().lower(),
        context=context.strip().lower(),
    )

    if not payload["found"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "CAPABILITY_PROFILE_NOT_FOUND",
                "region": region,
                "channel": channel,
                "context": context,
            },
        )

    return payload