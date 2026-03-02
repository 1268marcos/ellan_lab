# 01_source/order_pickup_service/app/schemas/internal.py
# Para que serve esse schema?
# Ele padroniza os contratos “internos” do 
# order_pickup_service (chamados por outros serviços / jobs / automações), 
# sem misturar com o que o cliente final (online/kiosk) envia.

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field

# =========================
# Tipos básicos internos
# =========================

Region = Literal["SP", "PT"]
OrderChannel = Literal["ONLINE", "KIOSK"]

OrderStatus = Literal[
    "PAYMENT_PENDING",
    "PAID_PENDING_PICKUP",
    "DISPENSED",
    "PICKED_UP",
    "EXPIRED",
]

SlotState = Literal[
    "AVAILABLE",
    "RESERVED",
    "LOCKED",
    "OUT_OF_STOCK",
]


# =========================
# 1) Evento interno (auditoria / logs)
# =========================

class InternalEvent(BaseModel):
    """
    Evento interno genérico pra rastrear mudanças relevantes.
    Útil pra log, auditoria, replay, debug, etc.
    """
    event_id: str = Field(..., description="UUID do evento")
    event_type: str = Field(..., description="Tipo do evento: ex. ORDER_STATUS_CHANGED")
    created_at: datetime = Field(..., description="Timestamp do evento (UTC recomendado)")

    # contexto mínimo
    region: Region
    totem_id: str
    channel: OrderChannel
    order_id: str

    # payload livre para detalhes
    data: Dict[str, Any] = Field(default_factory=dict)


# =========================
# 2) Confirmação interna de pagamento
# =========================

class InternalPaymentApprovedIn(BaseModel):
    """
    Payload usado internamente quando algum componente confirma pagamento.
    Ex.: payment_gateway -> order_pickup_service
    """
    order_id: str
    region: Region
    totem_id: str
    channel: OrderChannel

    # rastreabilidade
    provider: str = Field(..., description="Ex.: pix, card, mbway")
    transaction_id: str = Field(..., description="id do provedor")
    amount_cents: int
    currency: str = Field(default="EUR", description="Moeda (padrão EUR, ajuste se quiser)") # pode ser ajustado isso automático no service

    # antifraude leve / telemetria
    device_fingerprint: Optional[str] = None
    ip: Optional[str] = None


class InternalPaymentApprovedOut(BaseModel):
    """
    Resposta interna confirmando o efeito.
    """
    ok: bool = True
    order_id: str
    status: OrderStatus
    slot: Optional[int] = None
    message: str


# =========================
# 3) Operação interna de estado de slot
# =========================

class InternalSetSlotStateIn(BaseModel):
    """
    Chamado interno para marcar a gaveta como OUT_OF_STOCK (cinza)
    ou outros estados, caso seu backend suporte.
    """
    region: Region
    totem_id: str
    slot: int
    state: SlotState


class InternalSetSlotStateOut(BaseModel):
    ok: bool = True
    region: Region
    totem_id: str
    slot: int
    state: SlotState
    backend_response: Optional[Dict[str, Any]] = None


# =========================
# 4) Ping interno / healthcheck (opcional)
# =========================

class InternalHealthOut(BaseModel):
    ok: bool = True
    service: str = "order_pickup_service"
    time: datetime
    details: Dict[str, Any] = Field(default_factory=dict)


# =========================
# 5) Compatibilidade com Router (Payment Confirm) 
# ESSA É UMA SOLUÇÃO RAPIDA
# Optei por usar o schema rico (InternalPaymentAprrovedIn)
# em app/routers/internal.py
# =========================

# class PaymentConfirmIn(BaseModel):
#     """
#     Schema simplificado para o endpoint POST /internal/orders/{order_id}/payment-confirm
#     O order_id vem na URL, então o body só precisa dos dados do pagamento.
#     """
#     gateway_transaction_id: str  # ✅ Nome exato esperado pelo router




class QRIn(BaseModel):
    step_index: int
    expires_at: int
    signature: str

class PickupVerifyIn(BaseModel):
    order_id: str
    region: str
    gateway_id: str
    locker_id: str
    porta: int
    qr: QRIn

class PickupVerifyOut(BaseModel):
    ok: bool = True
    decision: str  # "OPEN" | "DENY"
    reason: Optional[str] = None
    order_id: Optional[str] = None
    slot: Optional[int] = None

class DoorInfo(BaseModel):
    opened_at: Optional[int] = None
    closed_at: Optional[int] = None
    open_ok: bool = True
    close_ok: bool = True

class PickupConfirmIn(BaseModel):
    region: str
    gateway_id: str
    locker_id: str
    porta: int
    door: Optional[DoorInfo] = None

class GatewayEventIn(BaseModel):
    event_id: str
    event_type: str
    created_at: int
    locker_id: str
    porta: Optional[int] = None
    order_id: Optional[str] = None
    request_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)

class EventsBatchIn(BaseModel):
    gateway_id: str
    region: str
    events: List[GatewayEventIn]