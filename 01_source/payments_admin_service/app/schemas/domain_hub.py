from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaymentDomainRegistryOut(_Orm):
    code: str
    name: str
    description: str | None
    ops_base_path: str | None
    api_service_name: str | None
    is_active: bool
    sort_order: int


class PaymentDomainRegistryListOut(BaseModel):
    items: list[PaymentDomainRegistryOut]
    total: int


class PaymentExternalReferenceIn(BaseModel):
    order_id: str | None = None
    payment_entity_type: str
    payment_entity_id: str
    external_domain: str
    external_entity_type: str
    external_entity_id: str
    link_role: str = "PRIMARY"
    sync_status: str = "LINKED"
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class PaymentExternalReferenceOut(_Orm):
    id: str
    order_id: str | None
    payment_entity_type: str
    payment_entity_id: str
    external_domain: str
    external_entity_type: str
    external_entity_id: str
    link_role: str
    sync_status: str
    last_synced_at: datetime | None
    metadata_json: dict[str, Any]


class PaymentExternalReferenceListOut(BaseModel):
    items: list[PaymentExternalReferenceOut]
    total: int


class PaymentDomainObligationIn(BaseModel):
    order_id: str
    domain_code: str
    obligation_type: str
    status: str = "PENDING"
    priority: int = 50
    blocking_payment: bool = False
    due_at: datetime | None = None
    external_ref_id: str | None = None
    notes: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class PaymentDomainObligationUpdate(BaseModel):
    status: str | None = None
    blocking_payment: bool | None = None
    resolved_at: datetime | None = None
    notes: str | None = None


class PaymentDomainObligationOut(_Orm):
    id: str
    order_id: str
    domain_code: str
    obligation_type: str
    status: str
    priority: int
    blocking_payment: bool
    due_at: datetime | None
    resolved_at: datetime | None
    external_ref_id: str | None
    notes: str | None


class PaymentDomainObligationListOut(BaseModel):
    items: list[PaymentDomainObligationOut]
    total: int


class PaymentCrossDomainEventOut(_Orm):
    id: str
    order_id: str | None
    event_type: str
    source_domain: str
    target_domains_json: list[str] | Any
    status: str
    published_at: datetime | None
    created_at: datetime


class PaymentCrossDomainEventListOut(BaseModel):
    items: list[PaymentCrossDomainEventOut]
    total: int


class DomainGapItem(BaseModel):
    order_id: str
    gap_type: str
    domain_code: str
    message: str
    severity: str


class CrossDomainGapsOut(BaseModel):
    items: list[DomainGapItem]
    total: int


class Order360DomainSection(BaseModel):
    domain_code: str
    domain_name: str
    ops_path: str | None
    references: list[PaymentExternalReferenceOut]
    obligations: list[PaymentDomainObligationOut]


class PaymentOrder360Out(BaseModel):
    order_id: str
    payment_summary: dict[str, Any]
    domains: list[Order360DomainSection]
    pending_obligations: int
    blocking_obligations: int
    external_refs_total: int
    cross_domain_events_pending: int
