from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class OrderCreateIn(BaseModel):
    id: Optional[str] = None
    channel: str = "KIOSK"
    region: str = "BR"
    totem_id: str = "TOTEM-01"
    amount_cents: int = Field(ge=0)
    currency: str = "BRL"
    status: str = "PENDING"
    payment_status: str = "PENDING"
    ecommerce_partner_id: Optional[str] = None
    tenant_id: Optional[str] = None
    partner_order_ref: Optional[str] = None
    sku_id: Optional[str] = None
    locker_id: Optional[str] = None


class OrderUpdateIn(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    locker_id: Optional[str] = None


class OrderOut(BaseModel):
    id: str
    channel: str
    region: str
    totem_id: str
    amount_cents: int
    currency: str
    status: str
    payment_status: str
    ecommerce_partner_id: Optional[str] = None
    tenant_id: Optional[str] = None
    partner_order_ref: Optional[str] = None
    sku_id: Optional[str] = None
    locker_id: Optional[str] = None
    pickup_deadline_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderListOut(BaseModel):
    items: list[OrderOut]
    total: int


class PickupCreateIn(BaseModel):
    id: Optional[str] = None
    order_id: str
    channel: str = "KIOSK"
    region: str = "BR"
    locker_id: Optional[str] = None
    slot: Optional[str] = None
    status: str = "PENDING"
    lifecycle_stage: str = "CREATED"


class PickupUpdateIn(BaseModel):
    status: Optional[str] = None
    lifecycle_stage: Optional[str] = None
    locker_id: Optional[str] = None
    slot: Optional[str] = None
    fraud_flag: Optional[bool] = None


class PickupOut(BaseModel):
    id: str
    order_id: str
    channel: str
    region: str
    locker_id: Optional[str] = None
    slot: Optional[str] = None
    status: str
    lifecycle_stage: str
    expires_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    redeemed_at: Optional[datetime] = None
    fraud_flag: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PickupListOut(BaseModel):
    items: list[PickupOut]
    total: int


class CreditOut(BaseModel):
    id: str
    order_id: str
    user_id: str
    type: str
    amount_cents: int
    currency: str
    status: str
    created_at_epoch: int
    expires_at: Optional[datetime] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreditListOut(BaseModel):
    items: list[CreditOut]
    total: int


class OutboxOut(BaseModel):
    id: str
    partner_id: str
    order_id: str
    event_type: str
    status: str
    attempt_count: int
    max_attempts: int
    next_retry_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OutboxListOut(BaseModel):
    items: list[OutboxOut]
    total: int


class OutboxReplayOut(BaseModel):
    ok: bool
    replayed: bool
    item: OutboxOut


class FulfillmentOut(BaseModel):
    id: str
    order_id: str
    fulfillment_type: str
    partner_id: Optional[str] = None
    status: str
    last_event_type: Optional[str] = None
    last_outbox_status: Optional[str] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class FulfillmentListOut(BaseModel):
    items: list[FulfillmentOut]
    total: int


class FulfillmentUpdateIn(BaseModel):
    status: Optional[str] = None
    last_event_type: Optional[str] = None
    last_outbox_status: Optional[str] = None


class CreditCreateIn(BaseModel):
    id: Optional[str] = None
    order_id: str
    user_id: str
    type: str = "GOODWILL"
    amount_cents: int = Field(gt=0)
    currency: str = "BRL"
    status: str = "AVAILABLE"


class OrderItemOut(BaseModel):
    id: str
    order_id: str
    sku_id: str
    sku_description: Optional[str] = None
    quantity: int
    unit_amount_cents: int
    total_amount_cents: int
    item_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderItemListOut(BaseModel):
    items: list[OrderItemOut]
    total: int


class PickupEventOut(BaseModel):
    id: str
    pickup_id: str
    version: int
    event_type: str
    source: str
    occurred_at: datetime

    model_config = {"from_attributes": True}


class PickupEventListOut(BaseModel):
    items: list[PickupEventOut]
    total: int


class PickupTokenOut(BaseModel):
    id: str
    order_id: str
    pickup_id: Optional[str] = None
    token_hash: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    manual_code: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PickupTokenListOut(BaseModel):
    items: list[PickupTokenOut]
    total: int


class PickupAttemptOut(BaseModel):
    id: str
    order_id: str
    gateway_id: str
    created_at_epoch: int
    ok: bool
    reason: Optional[str] = None

    model_config = {"from_attributes": True}


class PickupAttemptListOut(BaseModel):
    items: list[PickupAttemptOut]
    total: int


class DomainOutboxOut(BaseModel):
    id: str
    event_key: str
    aggregate_type: Optional[str] = None
    aggregate_id: Optional[str] = None
    event_name: Optional[str] = None
    status: str
    retry_count: int
    occurred_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DomainOutboxListOut(BaseModel):
    items: list[DomainOutboxOut]
    total: int


class DomainOutboxReplayOut(BaseModel):
    ok: bool
    replayed: bool
    item: DomainOutboxOut
