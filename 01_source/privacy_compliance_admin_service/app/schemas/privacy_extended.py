from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class LegalBasisIn(BaseModel):
    regulation_code: str
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    article_ref: Optional[str] = None
    description: Optional[str] = None
    requires_consent: bool = False


class LegalBasisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regulation_code: str
    code: str
    name: str
    article_ref: Optional[str] = None
    description: Optional[str] = None
    requires_consent: bool
    active: bool
    created_at: datetime


class LegalBasisListOut(BaseModel):
    items: list[LegalBasisOut]
    total: int


class DataCategoryIn(BaseModel):
    regulation_code: str
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=128)
    sensitivity: str = "NORMAL"
    description: Optional[str] = None
    special_category: bool = False


class DataCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regulation_code: str
    code: str
    name: str
    sensitivity: str
    description: Optional[str] = None
    special_category: bool
    active: bool
    created_at: datetime


class DataCategoryListOut(BaseModel):
    items: list[DataCategoryOut]
    total: int


class ProcessingActivityIn(BaseModel):
    regulation_code: str
    code: str = Field(..., max_length=32)
    name: str = Field(..., max_length=255)
    purpose: str
    data_controller: Optional[str] = None
    legal_basis_id: Optional[str] = None
    data_categories: list[str] = Field(default_factory=list)
    recipients: list[str] = Field(default_factory=list)
    retention_days: Optional[int] = None
    cross_border: bool = False
    status: str = "ACTIVE"


class ProcessingActivityUpdate(BaseModel):
    name: Optional[str] = None
    purpose: Optional[str] = None
    legal_basis_id: Optional[str] = None
    data_categories: Optional[list[str]] = None
    recipients: Optional[list[str]] = None
    retention_days: Optional[int] = None
    cross_border: Optional[bool] = None
    status: Optional[str] = None


class ProcessingActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regulation_code: str
    code: str
    name: str
    purpose: str
    data_controller: Optional[str] = None
    legal_basis_id: Optional[str] = None
    data_categories: list[str]
    recipients: list[str]
    retention_days: Optional[int] = None
    cross_border: bool
    status: str
    created_at: datetime
    updated_at: datetime


class ProcessingActivityListOut(BaseModel):
    items: list[ProcessingActivityOut]
    total: int


class ProcessorIn(BaseModel):
    name: str = Field(..., max_length=255)
    processor_type: str = "SUB_PROCESSOR"
    country: Optional[str] = None
    contact_email: Optional[str] = None
    services: list[str] = Field(default_factory=list)
    regulation_codes: list[str] = Field(default_factory=list)


class ProcessorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    processor_type: str
    country: Optional[str] = None
    contact_email: Optional[str] = None
    services: list[str]
    regulation_codes: list[str]
    active: bool
    created_at: datetime
    updated_at: datetime


class ProcessorListOut(BaseModel):
    items: list[ProcessorOut]
    total: int


class ProcessorAgreementIn(BaseModel):
    processor_id: str
    regulation_code: str
    agreement_type: str = "DPA"
    status: str = "ACTIVE"
    signed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    document_url: Optional[str] = None


class ProcessorAgreementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    processor_id: str
    regulation_code: str
    agreement_type: str
    status: str
    signed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    document_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProcessorAgreementListOut(BaseModel):
    items: list[ProcessorAgreementOut]
    total: int


class RetentionRuleIn(BaseModel):
    regulation_code: str
    data_category_id: Optional[str] = None
    processing_activity_id: Optional[str] = None
    retention_days: int = Field(..., ge=1)
    purge_method: str = "ANONYMIZE"
    legal_basis_code: Optional[str] = None
    notes: Optional[str] = None


class RetentionRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regulation_code: str
    data_category_id: Optional[str] = None
    processing_activity_id: Optional[str] = None
    retention_days: int
    purge_method: str
    legal_basis_code: Optional[str] = None
    notes: Optional[str] = None
    active: bool
    created_at: datetime


class RetentionRuleListOut(BaseModel):
    items: list[RetentionRuleOut]
    total: int


class BreachIncidentIn(BaseModel):
    regulation_code: str
    title: str = Field(..., max_length=255)
    severity: str = "MEDIUM"
    discovered_at: datetime
    affected_count: Optional[int] = None
    description: Optional[str] = None
    notification_required: bool = False


class BreachIncidentUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    remediation: Optional[str] = None
    reported_at: Optional[datetime] = None
    supervisory_notified_at: Optional[datetime] = None
    subjects_notified_at: Optional[datetime] = None


class BreachIncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regulation_code: str
    title: str
    severity: str
    status: str
    discovered_at: datetime
    reported_at: Optional[datetime] = None
    affected_count: Optional[int] = None
    description: Optional[str] = None
    remediation: Optional[str] = None
    notification_required: bool
    supervisory_notified_at: Optional[datetime] = None
    subjects_notified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class BreachIncidentListOut(BaseModel):
    items: list[BreachIncidentOut]
    total: int


class ImpactAssessmentIn(BaseModel):
    regulation_code: str
    processing_activity_id: Optional[str] = None
    title: str = Field(..., max_length=255)
    risk_level: str = "MEDIUM"
    reviewer: Optional[str] = None
    mitigation_summary: Optional[str] = None
    document_url: Optional[str] = None


class ImpactAssessmentUpdate(BaseModel):
    status: Optional[str] = None
    risk_level: Optional[str] = None
    assessed_at: Optional[datetime] = None
    reviewer: Optional[str] = None
    mitigation_summary: Optional[str] = None
    document_url: Optional[str] = None


class ImpactAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regulation_code: str
    processing_activity_id: Optional[str] = None
    title: str
    risk_level: str
    status: str
    assessed_at: Optional[datetime] = None
    reviewer: Optional[str] = None
    mitigation_summary: Optional[str] = None
    document_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ImpactAssessmentListOut(BaseModel):
    items: list[ImpactAssessmentOut]
    total: int


class TransferRecordIn(BaseModel):
    regulation_code: str
    destination_country: str = Field(..., min_length=2, max_length=2)
    mechanism: str = "SCC"
    processor_id: Optional[str] = None
    processing_activity_id: Optional[str] = None
    document_ref: Optional[str] = None


class TransferRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regulation_code: str
    destination_country: str
    mechanism: str
    processor_id: Optional[str] = None
    processing_activity_id: Optional[str] = None
    status: str
    document_ref: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TransferRecordListOut(BaseModel):
    items: list[TransferRecordOut]
    total: int


class RegulationHubOut(BaseModel):
    regulation_code: str
    regulation_name: str
    jurisdiction: str
    processing_activities: int
    legal_bases: int
    data_categories: int
    processors: int
    active_dpas: int
    retention_rules: int
    open_breaches: int
    dpia_pending: int
    active_transfers: int
    pending_dsar: int
    pending_deletions: int
    active_consents: int


class LockerNetworkPlayerOut(BaseModel):
    id: str
    code: str
    name: str
    network_type: str
    region_group: str
    countries: list[str]
    regulation_codes: list[str]
    privacy_role: str
    data_shared: list[str]
    website_url: str | None = None


class LockerNetworkPlayerListOut(BaseModel):
    items: list[LockerNetworkPlayerOut]
    total: int
    regulation_code: str | None = None
    summary: str | None = None
