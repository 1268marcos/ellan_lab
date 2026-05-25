from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AccessRequestCreateIn(BaseModel):
    requester_id: str
    user_id: str
    domain_code: str
    entity_type: str
    entity_id: str
    entity_label: Optional[str] = None
    permission_key: str
    justification: str


class AccessRequestDecideIn(BaseModel):
    decision: str = Field(pattern="^(APPROVE|DENY)$")
    reviewer_id: Optional[str] = None
    review_notes: Optional[str] = None


class AccessRequestOut(BaseModel):
    id: str
    requester_id: str
    user_id: str
    domain_code: str
    entity_type: str
    entity_id: str
    entity_label: Optional[str] = None
    permission_key: str
    justification: str
    status: str
    grant_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AccessRequestListOut(BaseModel):
    items: list[AccessRequestOut]
    total: int
    pending_count: int


class JitGrantCreateIn(BaseModel):
    user_id: str
    domain_code: str
    entity_type: str
    entity_id: str
    permission_key: str
    reason: str
    duration_hours: int = Field(default=8, ge=1, le=72)
    approved_by: Optional[str] = None
    entity_label: Optional[str] = None


class JitGrantOut(BaseModel):
    id: str
    user_id: str
    domain_code: str
    entity_id: str
    permission_key: str
    status: str
    grant_id: Optional[str] = None
    expires_at: datetime

    model_config = {"from_attributes": True}


class JitGrantListOut(BaseModel):
    items: list[JitGrantOut]
    total: int


class DelegationOpenIn(BaseModel):
    delegate_user_id: str
    target_domain: str
    target_entity_type: str
    target_entity_id: str
    target_entity_label: Optional[str] = None
    reason: str
    duration_hours: int = Field(default=4, ge=1, le=24)
    approved_by: Optional[str] = None


class DelegationOut(BaseModel):
    id: str
    delegate_user_id: str
    target_domain: str
    target_entity_type: str
    target_entity_id: str
    target_entity_label: Optional[str] = None
    status: str
    expires_at: datetime

    model_config = {"from_attributes": True}


class DelegationListOut(BaseModel):
    items: list[DelegationOut]
    total: int


class DomainEntitlementOut(BaseModel):
    id: str
    domain_code: str
    remote_entity_type: str
    remote_entity_id: str
    remote_label: Optional[str] = None
    entitlement_key: str
    source_service: str
    synced_at: datetime

    model_config = {"from_attributes": True}


class DomainEntitlementListOut(BaseModel):
    items: list[DomainEntitlementOut]
    total: int
    domains_synced: int


class DomainAccessReportOut(BaseModel):
    user_id: str
    roles: list[str]
    domain_links: list[dict[str, Any]]
    active_grants: list[dict[str, Any]]
    pending_requests: int
    active_jit: int
    active_delegations: int
    player_access: list[dict[str, Any]]
    remote_entitlements: list[dict[str, Any]]
