from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RegulationIn(BaseModel):
    code: str = Field(..., min_length=2, max_length=16)
    name: str = Field(..., min_length=2, max_length=128)
    jurisdiction: str = Field(..., min_length=2, max_length=64)
    description: Optional[str] = None
    dpo_email: Optional[str] = None
    supervisory_authority: Optional[str] = None
    default_retention_days: int = Field(default=365, ge=1, le=3650)
    response_sla_days: int = Field(default=30, ge=1, le=365)
    active: bool = True


class RegulationUpdate(BaseModel):
    name: Optional[str] = None
    jurisdiction: Optional[str] = None
    description: Optional[str] = None
    dpo_email: Optional[str] = None
    supervisory_authority: Optional[str] = None
    default_retention_days: Optional[int] = Field(default=None, ge=1, le=3650)
    response_sla_days: Optional[int] = Field(default=None, ge=1, le=365)
    active: Optional[bool] = None


class RegulationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    jurisdiction: str
    description: Optional[str] = None
    dpo_email: Optional[str] = None
    supervisory_authority: Optional[str] = None
    default_retention_days: int
    response_sla_days: int
    active: bool
    created_at: datetime
    updated_at: datetime


class RegulationListOut(BaseModel):
    items: list[RegulationOut]
    total: int


class PolicyVersionIn(BaseModel):
    regulation_id: str
    version: str = Field(..., min_length=1, max_length=20)
    title: str = Field(..., min_length=2, max_length=255)
    content_url: Optional[str] = None
    summary: Optional[str] = None
    effective_at: datetime
    is_current: bool = False


class PolicyVersionUpdate(BaseModel):
    title: Optional[str] = None
    content_url: Optional[str] = None
    summary: Optional[str] = None
    effective_at: Optional[datetime] = None
    is_current: Optional[bool] = None


class PolicyVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regulation_id: str
    version: str
    title: str
    content_url: Optional[str] = None
    summary: Optional[str] = None
    effective_at: datetime
    is_current: bool
    created_at: datetime


class PolicyVersionListOut(BaseModel):
    items: list[PolicyVersionOut]
    total: int


class ConsentIn(BaseModel):
    regulation_code: str
    consent_type: str = Field(..., min_length=2, max_length=50)
    granted: bool
    user_id: Optional[str] = None
    guest_identifier: Optional[str] = None
    channel: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    policy_version: Optional[str] = None


class ConsentUpdate(BaseModel):
    granted: Optional[bool] = None
    revoked_at: Optional[datetime] = None
    policy_version: Optional[str] = None


class ConsentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    guest_identifier: Optional[str] = None
    regulation_code: str
    consent_type: str
    granted: bool
    channel: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    policy_version: Optional[str] = None
    granted_at: datetime
    revoked_at: Optional[datetime] = None
    created_at: datetime


class ConsentListOut(BaseModel):
    items: list[ConsentOut]
    total: int


class DeletionRequestIn(BaseModel):
    regulation_code: str
    user_id: Optional[str] = None
    requested_by: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


class DeletionRequestUpdate(BaseModel):
    status: Optional[str] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None


class DeletionRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regulation_code: str
    user_id: Optional[str] = None
    requested_by: Optional[str] = None
    status: str
    reason: Optional[str] = None
    rejection_reason: Optional[str] = None
    requested_at: datetime
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DeletionRequestListOut(BaseModel):
    items: list[DeletionRequestOut]
    total: int


class SubjectRequestIn(BaseModel):
    regulation_code: str
    request_type: str = Field(..., min_length=2, max_length=32)
    user_id: Optional[str] = None
    guest_identifier: Optional[str] = None
    requested_by: Optional[str] = None
    details: Optional[str] = None


class SubjectRequestUpdate(BaseModel):
    status: Optional[str] = None
    response_notes: Optional[str] = None
    completed_at: Optional[datetime] = None


class SubjectRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regulation_code: str
    user_id: Optional[str] = None
    guest_identifier: Optional[str] = None
    request_type: str
    status: str
    requested_by: Optional[str] = None
    details: Optional[str] = None
    response_notes: Optional[str] = None
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SubjectRequestListOut(BaseModel):
    items: list[SubjectRequestOut]
    total: int


class WebhookIn(BaseModel):
    regulation_code: str
    url: str = Field(..., min_length=8, max_length=500)
    events: list[str] = Field(default_factory=list)
    secret: Optional[str] = None
    signing_algo: str = "HMAC_SHA256"
    active: bool = True


class WebhookUpdate(BaseModel):
    url: Optional[str] = None
    events: Optional[list[str]] = None
    secret: Optional[str] = None
    active: Optional[bool] = None


class WebhookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regulation_code: str
    url: str
    events: list[str]
    signing_algo: str
    active: bool
    created_at: datetime
    updated_at: datetime


class WebhookListOut(BaseModel):
    items: list[WebhookOut]
    total: int


class ApiKeyMetaOut(BaseModel):
    id: str
    key_prefix: str
    label: Optional[str] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime


class ApiKeyListOut(BaseModel):
    regulation_code: str
    keys: list[ApiKeyMetaOut]


class ApiKeyRotateOut(BaseModel):
    regulation_code: str
    api_key: str
    key_prefix: str
    created_at: datetime


class DashboardOut(BaseModel):
    regulations: int
    active_policies: int
    pending_deletions: int
    pending_subject_requests: int
    consents_granted: int
    consents_revoked: int
    webhooks_active: int
    processing_activities: int = 0
    legal_bases: int = 0
    data_categories: int = 0
    processors: int = 0
    active_dpas: int = 0
    retention_rules: int = 0
    open_breaches: int = 0
    dpia_pending: int = 0
    active_transfers: int = 0
