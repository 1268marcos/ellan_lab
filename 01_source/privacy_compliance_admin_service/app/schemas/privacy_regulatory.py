from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SubjectRightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regulation_code: str
    right_code: str
    name: str
    article_ref: Optional[str] = None
    description: Optional[str] = None
    response_sla_days: Optional[str] = None
    dsar_type: Optional[str] = None
    automated_available: bool
    active: bool


class SubjectRightListOut(BaseModel):
    items: list[SubjectRightOut]
    total: int
    regulation_code: Optional[str] = None


class RegulatoryObligationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regulation_code: str
    obligation_code: str
    name: str
    category: str
    article_ref: Optional[str] = None
    description: Optional[str] = None
    compliance_status: str
    evidence_url: Optional[str] = None
    due_review_at: Optional[datetime] = None
    active: bool
    updated_at: datetime


class RegulatoryObligationListOut(BaseModel):
    items: list[RegulatoryObligationOut]
    total: int
    regulation_code: Optional[str] = None


class RegulatoryObligationUpdate(BaseModel):
    compliance_status: Optional[str] = Field(default=None, pattern="^(COMPLIANT|PARTIAL|PENDING|NON_COMPLIANT)$")
    evidence_url: Optional[str] = Field(default=None, max_length=500)


class LiaRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regulation_code: str
    processing_activity_id: Optional[str] = None
    title: str
    purpose: str
    balancing_test_summary: Optional[str] = None
    status: str
    reviewer: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    document_url: Optional[str] = None
    created_at: datetime


class LiaRecordListOut(BaseModel):
    items: list[LiaRecordOut]
    total: int


class LiaRecordCreate(BaseModel):
    regulation_code: str = Field(min_length=2, max_length=16)
    processing_activity_id: Optional[str] = None
    title: str = Field(min_length=3, max_length=255)
    purpose: str = Field(min_length=10)
    balancing_test_summary: Optional[str] = None
    status: str = Field(default="DRAFT", pattern="^(DRAFT|IN_REVIEW|APPROVED|REJECTED)$")
    reviewer: Optional[str] = None
    document_url: Optional[str] = None


class OptOutRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regulation_code: str
    user_id: Optional[str] = None
    guest_identifier: Optional[str] = None
    opt_out_type: str
    signal_source: str
    gpc_signal: bool
    active: bool
    recorded_at: datetime
    revoked_at: Optional[datetime] = None


class OptOutRecordListOut(BaseModel):
    items: list[OptOutRecordOut]
    total: int


class OptOutRecordCreate(BaseModel):
    regulation_code: str = Field(default="CCPA", min_length=2, max_length=16)
    user_id: Optional[str] = None
    guest_identifier: Optional[str] = None
    opt_out_type: str = Field(pattern="^(SALE_SHARE|LIMIT_SPI|TARGETED_AD|PROFILING)$")
    signal_source: str = Field(default="WEB", pattern="^(WEB|GPC|API|KIOSK|CALL_CENTER)$")
    gpc_signal: bool = False


class AuthorityNoticeTemplateOut(BaseModel):
    regulation_code: str
    authority_name: str
    deadline_hours: Optional[int] = None
    deadline_label: str
    channel: str
    template_summary: str
    required_fields: list[str]


class RegulatoryDomainSummaryOut(BaseModel):
    regulation_code: str
    subject_rights_count: int
    obligations_count: int
    obligations_compliant_pct: float
    lia_count: int
    opt_out_count: int
    breach_notification_hours: Optional[int] = None


class RegulatoryToolkitOut(BaseModel):
    regulation_code: str
    regulation_name: str
    jurisdiction: str
    summary: RegulatoryDomainSummaryOut
    subject_rights: list[SubjectRightOut]
    obligations: list[RegulatoryObligationOut]
    lia_records: list[LiaRecordOut]
    opt_out_records: list[OptOutRecordOut]
    authority_templates: list[AuthorityNoticeTemplateOut]
    supported_regulations: list[str]


class RightsCompareOut(BaseModel):
    codes: list[str]
    rights_by_code: dict[str, list[SubjectRightOut]]
    common_dsar_types: list[str]
    unique_by_code: dict[str, list[str]]


class DsarDraftOut(BaseModel):
    regulation_code: str
    regulation_name: str
    request_type: str
    right_id: str
    right_code: str
    right_name: str
    article_ref: Optional[str] = None
    response_sla_days: str
    automated_available: bool
    details: str
    subject_line: str


class PlayerLegalDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    player_code: str
    player_name: str
    document_slug: str
    title: str
    regulation_code: str
    version: str
    language: str
    summary: Optional[str] = None
    public_path: str
    privacy_contact_email: Optional[str] = None
    active: bool
    effective_at: Optional[datetime] = None


class PlayerLegalDocumentListOut(BaseModel):
    items: list[PlayerLegalDocumentOut]
    total: int
    player_code: Optional[str] = None
