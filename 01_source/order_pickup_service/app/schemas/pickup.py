# Compatível com: 
# token de retirada
# validação kiosk
# fluxo set-state
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class PickupRequest(BaseModel):
    token: str


class PickupResponse(BaseModel):
    order_id: int
    locker_port: int
    status: str


class PickupConfirmResponse(BaseModel):
    order_id: int
    status: str
    picked_up_at: datetime


class RedeemIn(BaseModel):
    """Schema para resgate de pedido"""
    order_id: str
    pickup_code: str
    email: Optional[EmailStr] = None  # ou use str se não precisar de validação
    # Adicione outros campos necessários conforme sua aplicação