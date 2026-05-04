from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import feature_flags
from app.services import v1_payment_bridge

router = APIRouter(prefix="/v1", tags=["v1"])


class ConfirmPaymentIn(BaseModel):
    order_id: str = Field(min_length=1)


@router.get("/health/flags")
def health_flags() -> dict:
    return {"ok": True, "flags": feature_flags.as_public_dict(), "metrics": feature_flags.get_metrics()}


@router.post("/confirm-payment")
def confirm_payment_v1(payload: ConfirmPaymentIn) -> dict:
    v1_payment_bridge.post_confirm_side_effects(payload.order_id)
    return {"ok": True, "order_id": payload.order_id}
