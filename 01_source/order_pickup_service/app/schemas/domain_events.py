# 01_source/order_pickup_service/app/schemas/domain_events.py
# 11/04/2026 - novo arquivo - para Criar um model Pydantic para order.paid

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class OrderPaidPayload(BaseModel):
    """Payload canônico order.paid (v2 enriquecido — campos extras opcionais)."""

    order_id: str = Field(..., min_length=1)
    region: str = Field(..., min_length=1)
    channel: str = Field(..., min_length=1)
    payment_method: str = Field(..., min_length=1)
    transaction_id: Optional[str] = None
    amount_cents: int = Field(..., ge=0)
    currency: str = Field(..., min_length=1)
    locker_id: str = Field(..., min_length=1)
    machine_id: str = Field(..., min_length=1)
    slot: str = Field(..., min_length=1)
    allocation_id: str = Field(..., min_length=1)
    pickup_id: Optional[str] = None
    tenant_id: Optional[str] = None
    operator_id: Optional[str] = None
    site_id: Optional[str] = None
    source_service: str = Field(..., min_length=1)
    consumer_cpf: Optional[str] = None
    consumer_name: Optional[str] = None
    tenant_cnpj: Optional[str] = None


class DomainEventEnvelope(BaseModel):
    event_key: str = Field(..., min_length=1)
    aggregate_type: str = Field(..., min_length=1)
    aggregate_id: str = Field(..., min_length=1)
    event_name: str = Field(..., min_length=1)
    event_version: int = Field(..., ge=1)
    payload: dict
    occurred_at: str = Field(..., min_length=1)

