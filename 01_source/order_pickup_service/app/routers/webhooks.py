"""Webhooks inbound (runtime → order_pickup)."""

from __future__ import annotations

import secrets
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.services.runtime_slot_sync_service import apply_slot_state_change_webhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class RuntimeSlotStateChangeIn(BaseModel):
    locker_id: str = Field(..., min_length=1)
    slot_label: str = Field(..., min_length=1)
    previous_state: Optional[str] = None
    current_state: str = Field(..., min_length=1)
    occurred_at: str = Field(..., min_length=1)
    allocation_id: Optional[str] = None


def _require_runtime_slot_webhook_secret(
    x_webhook_secret: Optional[str] = Header(default=None, alias="X-Webhook-Secret"),
) -> None:
    expected = str(settings.runtime_slot_state_webhook_secret or "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"type": "WEBHOOK_SECRET_NOT_CONFIGURED", "message": "RUNTIME_SLOT_STATE_WEBHOOK_SECRET is not set."},
        )
    got = str(x_webhook_secret or "").strip()
    if len(got) != len(expected) or not secrets.compare_digest(got, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "WEBHOOK_UNAUTHORIZED", "message": "Invalid X-Webhook-Secret."},
        )


@router.post(
    "/runtime/slot-state-change",
    dependencies=[Depends(_require_runtime_slot_webhook_secret)],
    status_code=status.HTTP_200_OK,
)
def post_runtime_slot_state_change(payload: RuntimeSlotStateChangeIn, db: Session = Depends(get_db)):
    out = apply_slot_state_change_webhook(
        db,
        locker_id=payload.locker_id,
        slot_label=payload.slot_label,
        previous_state=payload.previous_state,
        current_state=payload.current_state,
        occurred_at=payload.occurred_at,
        allocation_id=payload.allocation_id,
    )
    if not out.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=out,
        )
    return out
