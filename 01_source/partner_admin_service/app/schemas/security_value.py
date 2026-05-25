from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, Field


class SecurityIntelligenceOut(BaseModel):
    overall_posture: str
    average_user_risk: float
    high_risk_entities: int
    open_alerts: int
    pending_reviews: int
    active_break_glass: int
    compliance_coverage_pct: float
    top_risks: list[dict[str, Any]]
    recommendations: list[str]


class RoleTemplateOut(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    roles: list[str] = Field(default_factory=list)
    permission_groups: list[str] = Field(default_factory=list)
    default_players: list[str] = Field(default_factory=list)
    target_segment: Optional[str] = None

    model_config = {"from_attributes": True}


class RoleTemplateListOut(BaseModel):
    items: list[RoleTemplateOut]
    total: int


class ApplyRoleTemplateIn(BaseModel):
    user_id: str
    template_code: str
    granted_by: Optional[str] = None


class ApplyRoleTemplateOut(BaseModel):
    user_id: str
    template_code: str
    roles_granted: int
    groups_assigned: int
    player_access_granted: int


class RiskScoreOut(BaseModel):
    entity_type: str
    entity_id: str
    score: float
    risk_tier: str
    factors: list[str] = Field(default_factory=list)
    computed_at: datetime

    model_config = {"from_attributes": True}


class RiskScoreListOut(BaseModel):
    items: list[RiskScoreOut]
    total: int


class AccessReviewCampaignCreateIn(BaseModel):
    name: str
    due_at: datetime
    scope: dict[str, Any] = Field(default_factory=dict)
    created_by: Optional[str] = None


class AccessReviewCampaignOut(BaseModel):
    id: str
    name: str
    status: str
    due_at: datetime
    pending_items: int = 0
    approved_items: int = 0
    revoked_items: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class AccessReviewCampaignListOut(BaseModel):
    items: list[AccessReviewCampaignOut]
    total: int


class AccessReviewItemOut(BaseModel):
    id: str
    campaign_id: str
    user_id: str
    subject_type: str
    subject_id: str
    subject_label: Optional[str] = None
    decision: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AccessReviewItemListOut(BaseModel):
    items: list[AccessReviewItemOut]
    total: int


class AccessReviewDecisionIn(BaseModel):
    decision: str = Field(pattern="^(APPROVE|REVOKE|ESCALATE)$")
    reviewer_id: Optional[str] = None
    notes: Optional[str] = None


class BreakGlassCreateIn(BaseModel):
    user_id: str
    reason: str
    granted_roles: list[str] = Field(default_factory=lambda: ["admin_operacao"])
    approved_by: Optional[str] = None
    duration_hours: int = 4


class BreakGlassOut(BaseModel):
    id: str
    user_id: str
    reason: str
    status: str
    granted_roles: list[str]
    started_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class BreakGlassListOut(BaseModel):
    items: list[BreakGlassOut]
    total: int


class BreakGlassRevokeIn(BaseModel):
    revoked_by: Optional[str] = None
    reason: Optional[str] = None


class AlertOut(BaseModel):
    id: str
    rule_id: str
    title: str
    detail: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    severity: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertListOut(BaseModel):
    items: list[AlertOut]
    total: int
    open_count: int


class ComplianceControlOut(BaseModel):
    code: str
    framework: str
    title: str
    description: Optional[str] = None
    domain: Optional[str] = None
    mapped_permissions: int = 0
    coverage_level: Optional[str] = None

    model_config = {"from_attributes": True}


class ComplianceListOut(BaseModel):
    items: list[ComplianceControlOut]
    total: int
    coverage_pct: float


class AccessMatrixOut(BaseModel):
    users: list[str]
    domains: list[str]
    cells: list[dict[str, Any]]
