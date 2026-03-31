# 01_source/order_pickup_service/app/schemas/public_pickup.py

from __future__ import annotations

from pydantic import BaseModel


class PublicPickupOut(BaseModel):
    order_id: str
    status: str
    expires_at: str | None = None
    token_id: str | None = None
    qr_value: str | None = None
    manual_code_masked: str | None = None